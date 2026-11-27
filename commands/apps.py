import json
import subprocess
import threading
import webbrowser

from rapidfuzz import fuzz

from core.config import cargar_config
from core.registry import comando
from core.texto import normalizar

UMBRAL_APP = 75  # parecido mínimo (0 a 100) entre lo que dijiste y el nombre

_apps = {}  # nombre normalizado -> (nombre original, AppID)
_listo = threading.Event()


def _cargar_apps():
    """Lee la lista de aplicaciones del menú Inicio (tarda unos 3 s)."""
    consulta = (
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        "Get-StartApps | ConvertTo-Json"
    )
    try:
        resultado = subprocess.run(
            ["powershell", "-NoProfile", "-Command", consulta],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        datos = json.loads(resultado.stdout) if resultado.stdout.strip() else []
        if isinstance(datos, dict):
            datos = [datos]
        for app in datos:
            _apps[normalizar(app["Name"])] = (app["Name"], app["AppID"])
    except Exception as error:
        print(f"No se pudo leer la lista de aplicaciones: {error}")
    finally:
        _listo.set()


# Se carga en segundo plano apenas se importa este archivo,
# así Luna no se demora al arrancar.
threading.Thread(target=_cargar_apps, daemon=True).start()


def _buscar_app(pedido):
    """Devuelve (nombre, AppID) de la aplicación más parecida, o None."""
    _listo.wait(timeout=15)

    candidatos = dict(_apps)
    alias = cargar_config().get("apps", {}).get("alias", {})
    for dicho, real in alias.items():
        if normalizar(real) in _apps:
            candidatos[normalizar(dicho)] = _apps[normalizar(real)]

    if pedido in candidatos:
        return candidatos[pedido]

    mejor, mejor_puntaje = None, 0
    for nombre, valor in candidatos.items():
        puntaje = fuzz.ratio(pedido, nombre)
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = valor, puntaje
    return mejor if mejor_puntaje >= UMBRAL_APP else None


@comando("abrir {app}")
def abrir(parametro, numero=None):
    # «Visual Studio 2017»: el intérprete saca el 2017 como número; lo devolvemos.
    pedido = parametro if numero is None else f"{parametro} {numero}"
    encontrada = _buscar_app(normalizar(pedido))
    if encontrada is None:
        # No es una aplicación instalada: probamos si es un sitio conocido.
        sitio = cargar_config().get("sitios", {}).get(normalizar(pedido))
        if sitio:
            webbrowser.open(sitio)
            return f"Abro {parametro}."
        return f"No encontré {parametro}."
    nombre, app_id = encontrada
    subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{app_id}"])
    return f"Abro {nombre}."