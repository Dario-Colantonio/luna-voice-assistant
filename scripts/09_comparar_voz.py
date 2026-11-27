import io
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import sounddevice as sd
from piper import PiperVoice, SynthesisConfig

from core.config import RAIZ

# Se puede pasar el nombre de la voz y la velocidad al ejecutar.
nombre = sys.argv[1] if len(sys.argv) > 1 else "es_AR-daniela-high"
velocidad = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0  # más de 1 = más lento

print(f"Voz: {nombre} | velocidad: {velocidad}")
voz = PiperVoice.load(str(RAIZ / "models" / f"{nombre}.onnx"))
ajustes = SynthesisConfig(length_scale=velocidad)

FRASES = [
    "Estoy abriendo Google Chrome.",
    "Abro Google Chrome.",
    "No entendí lo que dijiste, ¿podés repetirlo?",
    "No entendí. Repetilo, por favor.",
    "Listo, subí el volumen.",
]

for frase in FRASES:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as f:
        voz.synthesize_wav(frase, f, syn_config=ajustes)
    buffer.seek(0)
    with wave.open(buffer, "rb") as f:
        sample_rate = f.getframerate()
        datos = f.readframes(f.getnframes())
    audio = np.frombuffer(datos, dtype="int16")
    silencio = np.zeros(int(sample_rate * 0.5), dtype="int16")

    print(f"-> {frase}")
    sd.play(np.concatenate([silencio, audio]), sample_rate)
    sd.wait()