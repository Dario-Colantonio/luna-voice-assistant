import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audio.microphone import Microfono
from audio.wakeword import DetectorWakeWord
from core.config import RAIZ, cargar_config

config = cargar_config()

print("Cargando el detector...")
detector = DetectorWakeWord(
    RAIZ / config["wakeword"]["modelo"],
    frase=config["wakeword"]["frase"],
    sample_rate=config["audio"]["sample_rate"],
)
mic = Microfono(config["audio"]["sample_rate"], config["audio"]["bloque"])


def esperar_detecciones(cantidad):
    detectadas = 0
    while detectadas < cantidad:
        bloque = mic.leer()
        if bloque is None:
            continue
        if detector.procesar(bloque):
            detectadas += 1
            hora = time.strftime("%H:%M:%S")
            print(f"[{hora}] ¡Detectado! ({detectadas}/{cantidad}) -> {detector.ultimo_texto!r}")


try:
    mic.iniciar()
    print(f"Micrófono activo: {mic.activo}")
    print("\nFase 1: decí «che luna» 3 veces (con pausas).")
    esperar_detecciones(3)

    mic.detener()
    print(f"\nMicrófono activo: {mic.activo}")
    print("Micrófono DESACTIVADO durante 8 segundos.")
    print("Decí «che luna» varias veces: no tiene que pasar nada.")
    time.sleep(8)

    mic.iniciar()
    detector.reiniciar()
    print(f"\nMicrófono activo: {mic.activo}")
    print("Fase 2: decí «che luna» 2 veces.")
    esperar_detecciones(2)
finally:
    mic.detener()

print("\nPrueba completa.")