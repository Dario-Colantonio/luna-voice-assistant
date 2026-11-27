import sys
import time
from pathlib import Path

# Permite importar los módulos del proyecto (audio, core) desde scripts/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audio.tts import Voz
from core.config import RAIZ, cargar_config

config = cargar_config()

print("Cargando la voz...")
t0 = time.perf_counter()
voz = Voz(
    RAIZ / config["voz"]["modelo"],
    velocidad=config["voz"]["velocidad"],
    silencio_inicial=config["voz"]["silencio_inicial"],
)
print(f"Voz cargada en {time.perf_counter() - t0:.1f} s")

t0 = time.perf_counter()
voz.calentar()
print(f"Calentamiento en {time.perf_counter() - t0:.1f} s")

for frase in [
    "Hola, soy Luna.",
    "Abro Google Chrome.",
    "No entendí. Repetilo, por favor.",
]:
    t0 = time.perf_counter()
    print(f"Diciendo: {frase}")
    voz.hablar(frase)
    print(f"  (total {time.perf_counter() - t0:.1f} s, con reproducción)")