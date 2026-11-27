import wave

import numpy as np
import sounddevice as sd

ARCHIVO = "prueba_mic.wav"
SALIDA = 3  # "Altavoces (Cirrus Logic...)" según tu lista de dispositivos

with wave.open(ARCHIVO, "rb") as f:
    sample_rate = f.getframerate()
    datos = f.readframes(f.getnframes())

audio = np.frombuffer(datos, dtype="int16")

print(f"Reproduciendo {ARCHIVO} por el dispositivo {SALIDA}...")
sd.play(audio, sample_rate, device=SALIDA)
sd.wait()
print("Listo.")