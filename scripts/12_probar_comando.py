import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audio.grabador import grabar_comando
from audio.microphone import Microfono
from audio.stt import Transcriptor
from core.config import RAIZ, cargar_config

config = cargar_config()
rec = config["grabacion"]
stt_cfg = config["stt"]

print("Cargando Whisper...")
transcriptor = Transcriptor(
    stt_cfg["modelo"],
    carpeta=RAIZ / stt_cfg["carpeta"],
    idioma=stt_cfg["idioma"],
    prompt=stt_cfg["prompt"],
)
t0 = time.perf_counter()
transcriptor.calentar()
print(f"Calentamiento: {time.perf_counter() - t0:.1f} s")

mic = Microfono(config["audio"]["sample_rate"], config["audio"]["bloque"])
try:
    mic.iniciar()
    while True:
        entrada = input("\nEnter para dar una orden (o 'q' y Enter para salir): ")
        if entrada.strip().lower() == "q":
            break

        mic.vaciar()
        print("Escuchando... decí tu comando.")
        t0 = time.perf_counter()
        audio = grabar_comando(
            mic,
            umbral=rec["umbral_voz"],
            espera_inicio=rec["espera_inicio"],
            silencio_fin=rec["silencio_fin"],
            maximo=rec["maximo"],
        )
        if audio is None:
            print("No te escuché hablar.")
            continue

        duracion = len(audio) / mic.sample_rate
        print(f"Grabado: {duracion:.1f} s de audio")

        t1 = time.perf_counter()
        texto = transcriptor.transcribir(audio)
        print(f"Texto: {texto!r}  (transcrito en {time.perf_counter() - t1:.1f} s)")
finally:
    mic.detener()