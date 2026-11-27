import time
import wave

import numpy as np
import sounddevice as sd
from piper import PiperVoice

MODELO = "models/es_AR-daniela-high.onnx"
TEXTO = "Hola, soy Luna. Estoy lista para ayudarte."
ARCHIVO = "prueba_voz.wav"

print("Cargando la voz...")
t0 = time.perf_counter()
voz = PiperVoice.load(MODELO)
print(f"Voz cargada en {time.perf_counter() - t0:.1f} s")

print("Generando audio...")
t0 = time.perf_counter()
with wave.open(ARCHIVO, "wb") as f:
    voz.synthesize_wav(TEXTO, f)
t_sintesis = time.perf_counter() - t0

with wave.open(ARCHIVO, "rb") as f:
    sample_rate = f.getframerate()
    datos = f.readframes(f.getnframes())
audio = np.frombuffer(datos, dtype="int16")
duracion = len(audio) / sample_rate

print(f"Audio de {duracion:.1f} s generado en {t_sintesis:.1f} s")

# Sin 'device': usa la salida predeterminada de Windows (tu monitor).

# Algunos auriculares Bluetooth tardan en "despertar" y se comen el
# comienzo del audio. Anteponemos 0,5 s de silencio para compensarlo.
silencio = np.zeros(int(sample_rate * 0.5), dtype="int16")
audio_final = np.concatenate([silencio, audio])

print("Reproduciendo...")
sd.play(audio_final, sample_rate)
sd.wait()
print("Listo.")