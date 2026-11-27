import sys
import time

import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
DURACION = 5

# El nombre del modelo se puede pasar al ejecutar: "base" o "small".
NOMBRE_MODELO = sys.argv[1] if len(sys.argv) > 1 else "base"

print(f"Cargando el modelo '{NOMBRE_MODELO}'...")
t0 = time.perf_counter()
modelo = WhisperModel(
    NOMBRE_MODELO,
    device="cpu",
    compute_type="int8",  # cuantización: más liviano y rápido en CPU
    download_root="models/whisper",  # donde se guarda el modelo
)
print(f"Modelo cargado en {time.perf_counter() - t0:.1f} s")

input(f"\nPresioná Enter y hablá durante {DURACION} segundos...")
print("Grabando...")
audio = sd.rec(
    int(DURACION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32",  # Whisper trabaja con valores entre -1 y 1
)
sd.wait()
audio = audio[:, 0]  # de matriz (n, 1) a lista simple (n,)
print("Transcribiendo...")

t0 = time.perf_counter()
segmentos, info = modelo.transcribe(
    audio,
    language="es",
    beam_size=1,  # búsqueda más simple: más rápida
    vad_filter=True,  # ignora los silencios
)
# 'segmentos' se calcula a medida que lo recorremos,
# por eso el cronómetro incluye esta línea.
texto = " ".join(s.text.strip() for s in segmentos)
t_transcripcion = time.perf_counter() - t0

print(f"\nTexto reconocido: {texto!r}")
print(f"Transcripción hecha en {t_transcripcion:.1f} s")