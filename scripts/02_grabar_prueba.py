import wave

import numpy as np
import sounddevice as sd

# 16000 Hz, mono, enteros de 16 bits: es el formato que esperan
# los modelos de reconocimiento de voz (Vosk, Whisper).
SAMPLE_RATE = 16000
DURACION = 5
ARCHIVO = "prueba_mic.wav"

print(f"Grabando {DURACION} segundos... hablá ahora.")
audio = sd.rec(
    int(DURACION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="int16",
)
sd.wait()  # espera a que termine la grabación
print("Grabación terminada.")

# Nivel máximo de la señal. El máximo posible en 16 bits es 32767.
pico = int(np.abs(audio).max())
porcentaje = pico / 32767 * 100
print(f"Nivel máximo: {pico} de 32767 ({porcentaje:.0f}%)")

if pico < 500:
    print("Señal muy baja: revisá el micrófono, el volumen de entrada o los permisos.")
elif pico > 32000:
    print("Señal saturada: bajá el volumen de entrada del micrófono.")
else:
    print("Nivel correcto.")

# Guardamos un archivo WAV para poder escucharlo.
with wave.open(ARCHIVO, "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)  # 2 bytes = 16 bits
    f.setframerate(SAMPLE_RATE)
    f.writeframes(audio.tobytes())
print(f"Guardado en {ARCHIVO}")

# Reproducimos lo grabado para que lo escuches.
print("Reproduciendo...")
sd.play(audio, SAMPLE_RATE)
sd.wait()
print("Listo.")