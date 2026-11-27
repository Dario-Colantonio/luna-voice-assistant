import time

import numpy as np
import sounddevice as sd

SR = 16000


def tono(segundos, volumen):
    t = np.linspace(0, segundos, int(SR * segundos), endpoint=False)
    return (np.sin(2 * np.pi * 880 * t) * volumen * 32767).astype(np.int16)


silencio = np.zeros(int(SR * 0.5), dtype=np.int16)

print("Esperando 5 s sin sonido, para que el audio 'duerma'...")
time.sleep(5)

print("1) Pitido corto SOLO (como está en Luna ahora)")
sd.play(tono(0.15, 0.3), SR)
sd.wait()
time.sleep(5)

print("2) Pitido corto con 0,5 s de silencio antes")
sd.play(np.concatenate([silencio, tono(0.15, 0.3)]), SR)
sd.wait()
time.sleep(5)

print("3) Pitido largo y más fuerte (0,4 s), solo")
sd.play(tono(0.4, 0.6), SR)
sd.wait()
print("Fin.")