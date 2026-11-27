import ctypes
import time
from ctypes import wintypes

import psutil
from rapidfuzz import fuzz

from core.config import cargar_config
from core.registry import comando
from core.texto import normalizar

user32 = ctypes.windll.user32
WM_CLOSE = 0x0010  # la orden que recibe una ventana cuando apretás la X
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

UMBRAL = 80  # parecido mínimo entre lo que dijiste y los nombres de la configuración


def _titulo(hwnd):
    largo = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(largo + 1)
    user32.GetWindowTextW(hwnd, buffer, largo + 1)
    return buffer.value


def _datos_proceso(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    try:
        proceso = psutil.Process(pid.value)
        nombre = proceso.name()
    except Exception:
        return pid.value, "", ""
    try:
        ruta = proceso.exe()
    except Exception:
        ruta = ""
    return pid.value, nombre, ruta


def _ventanas():
    """Lista de (hwnd, pid, proceso, ruta, titulo) de las ventanas visibles con título."""
    resultado = []

    def callback(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            titulo = _titulo(hwnd)
            if titulo:
                pid, nombre, ruta = _datos_proceso(hwnd)
                resultado.append((hwnd, pid, nombre, ruta, titulo))
        return True

    funcion = EnumWindowsProc(callback)  # se guarda para que no la borre el recolector
    user32.EnumWindows(funcion, 0)
    return resultado


def _coincide(ventana, regla):
    _, _, nombre, ruta, titulo = ventana
    if nombre.lower() != regla["proceso"].lower():
        return False
    fragmento = regla.get("ruta_contiene")
    if fragmento and fragmento.lower() not in ruta.lower():
        return False
    parte_titulo = regla.get("titulo_contiene")
    if parte_titulo and normalizar(parte_titulo) not in normalizar(titulo):
        return False
    return True


def _buscar_regla(pedido):
    """La regla de la configuración cuyo nombre hablado más se parece a lo que dijiste."""
    reglas = cargar_config().get("cerrar", {}).get("apps", [])
    candidatos = {}
    for regla in reglas:
        for dicho in regla.get("decir", []):
            candidatos[normalizar(dicho)] = regla

    if pedido in candidatos:
        return candidatos[pedido]

    mejor, mejor_puntaje = None, 0
    for dicho, regla in candidatos.items():
        puntaje = fuzz.ratio(pedido, dicho)
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = regla, puntaje
    return mejor if mejor_puntaje >= UMBRAL else None


def _procesos(nombre):
    return [
        p for p in psutil.process_iter(["name"])
        if (p.info["name"] or "").lower() == nombre.lower()
    ]


def _terminar(nombre):
    """Termina los procesos con ese nombre y sus procesos hijos."""
    objetivos = []
    for proceso in _procesos(nombre):
        try:
            objetivos.extend(proceso.children(recursive=True))
        except Exception:
            pass
        objetivos.append(proceso)
    for proceso in objetivos:
        try:
            proceso.terminate()
        except Exception:
            pass
    psutil.wait_procs(objetivos, timeout=2)


@comando("cerrar {app}")
def cerrar(parametro, numero=None):
    # «Visual Studio 2017»: el intérprete saca el 2017 como número; lo devolvemos.
    pedido = normalizar(parametro if numero is None else f"{parametro} {numero}")
    regla = _buscar_regla(pedido)
    if regla is None:
        return f"No sé cerrar {parametro}."

    nombre = regla.get("nombre", parametro)
    forzar = regla.get("forzar", False)
    espera = cargar_config().get("cerrar", {}).get("espera", 3)

    ventanas = [v for v in _ventanas() if _coincide(v, regla)]
    if not ventanas and not (forzar and _procesos(regla["proceso"])):
        return f"{nombre} no está abierto."

    # Orden de cierre normal: el programa puede preguntar si guardar.
    for ventana in ventanas:
        user32.PostMessageW(ventana[0], WM_CLOSE, 0, 0)

    limite = time.monotonic() + espera
    while time.monotonic() < limite:
        if not [v for v in _ventanas() if _coincide(v, regla)]:
            break
        time.sleep(0.25)

    quedan = [v for v in _ventanas() if _coincide(v, regla)]
    if quedan:
        return f"Le pedí a {nombre} que se cierre, pero sigue abierto. Fijate si pregunta algo."

    if forzar:
        # Puede haber quedado en segundo plano: se le da un momento y se termina.
        limite = time.monotonic() + 2
        while time.monotonic() < limite and _procesos(regla["proceso"]):
            time.sleep(0.25)
        if _procesos(regla["proceso"]):
            _terminar(regla["proceso"])

    return f"Cierro {nombre}."