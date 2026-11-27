import time
from dataclasses import dataclass

from rapidfuzz import fuzz

from core.config import cargar_config
from core.registry import Comando, comandos_registrados, ejecutar_funcion
from core.texto import analizar, dividir_ordenes, es_absoluto

UMBRAL = 80  # parecido mínimo (0 a 100) para aceptar un comando


@dataclass
class Coincidencia:
    comando: Comando
    puntaje: float
    parametro: str | None
    numero: int | None
    absoluto: bool = False


def interpretar(texto):
    """Devuelve la mejor Coincidencia, o None si no se entendió nada."""
    palabras, numero = analizar(texto)
    if not palabras:
        return None
    absoluto = es_absoluto(texto)

    mejor = None
    for cmd in comandos_registrados():
        n = len(cmd.palabras)
        candidato = " ".join(palabras[:n])
        resto = palabras[n:]

        if cmd.tiene_parametro and not resto:
            continue  # falta lo que viene después (ej.: «abrir» sin decir qué)

        puntaje = fuzz.ratio(candidato, " ".join(cmd.palabras))
        if not cmd.tiene_parametro:
            puntaje -= min(len(resto) * 2, 10)  # penaliza levemente palabras de más

        if puntaje < UMBRAL:
            continue

        parametro = " ".join(resto) if cmd.tiene_parametro else None
        # Ante un empate gana el comando más específico (con más palabras fijas).
        if mejor is None or (puntaje, n) > (mejor.puntaje, len(mejor.comando.palabras)):
            mejor = Coincidencia(cmd, puntaje, parametro, numero, absoluto)
    return mejor


# NUEVO
def interpretar_varias(texto):
    """Si la frase son varias órdenes, devuelve la lista de coincidencias; si no, None."""
    partes = dividir_ordenes(texto)
    if len(partes) < 2:
        return None
    coincidencias = [interpretar(p) for p in partes]
    if any(c is None for c in coincidencias):
        return None  # alguna parte no es un comando: se trata como una sola orden
    return coincidencias


def _ejecutar_una(c):
    try:
        respuesta = ejecutar_funcion(c.comando, c.parametro, c.numero, c.absoluto)
    except Exception as error:
        print(f"Error en el comando {c.comando.frase!r}: {error}")
        return "Hubo un problema."
    return respuesta or "Listo."


def ejecutar(texto):
    """Interpreta el texto, ejecuta el o los comandos y devuelve lo que Luna debe decir."""
    coincidencias = interpretar_varias(texto)  # NUEVO
    if coincidencias is None:
        c = interpretar(texto)
        if c is None:
            return "No entendí ese comando."
        coincidencias = [c]

    espera = cargar_config().get("ordenes", {}).get("espera_tras_abrir", 6)
    respuestas = []
    for i, c in enumerate(coincidencias):
        # NUEVO: después de abrir un programa hay que darle tiempo a arrancar.
        if i > 0 and coincidencias[i - 1].comando.frase.startswith("abrir"):
            time.sleep(espera)
        respuestas.append(_ejecutar_una(c))
    return " ".join(respuestas)