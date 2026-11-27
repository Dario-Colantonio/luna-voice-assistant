import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from audio.grabador import nivel
from audio.microphone import Microfono
from core.config import cargar_config

config = cargar_config()
mic = Microfono(config["audio"]["sample_rate"], config["audio"]["bloque"])


def medir(segundos):
    niveles = []
    transcurrido = 0.0
    while transcurrido < segundos:
        bloque = mic.leer()
        if bloque is None:
            continue
        niveles.append(nivel(bloque))
        transcurrido += len(bloque) / 2 / mic.sample_rate
    return niveles


try:
    mic.iniciar()

    input("Apretá Enter y quedate EN SILENCIO durante 3 segundos...")
    mic.vaciar()
    silencio = medir(3)

    input("Apretá Enter y hablá normalmente durante 3 segundos...")
    mic.vaciar()
    voz = medir(3)
finally:
    mic.detener()

max_silencio = max(silencio)
mediana_voz = float(np.median(voz))
sugerido = int(max_silencio * 2)

print(f"\nSilencio: máximo {max_silencio:.0f}")
print(f"Voz: mediana {mediana_voz:.0f}, máximo {max(voz):.0f}")
print(f"Umbral sugerido: {sugerido}")
if sugerido >= mediana_voz * 0.5:
    print("Aviso: el silencio y la voz están muy cerca. Probá en un lugar más silencioso.")