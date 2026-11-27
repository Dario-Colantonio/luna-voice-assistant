import io
import wave

import numpy as np
import sounddevice as sd
from piper import PiperVoice, SynthesisConfig


class Voz:
    """Convierte texto en voz usando Piper y lo reproduce."""

    def __init__(self, ruta_modelo, velocidad=1.0, silencio_inicial=0.5, silencio_final=0.4):
        self._voz = PiperVoice.load(str(ruta_modelo))
        self._ajustes = SynthesisConfig(length_scale=velocidad)
        self._silencio_inicial = silencio_inicial
        self._silencio_final = silencio_final

    def _sintetizar(self, texto):
        """Devuelve (audio, sample_rate) sin guardar nada en disco."""
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as f:
            self._voz.synthesize_wav(texto, f, syn_config=self._ajustes)
        buffer.seek(0)
        with wave.open(buffer, "rb") as f:
            sample_rate = f.getframerate()
            datos = f.readframes(f.getnframes())
        return np.frombuffer(datos, dtype="int16"), sample_rate

    def calentar(self):
        """Primera síntesis, que es la más lenta. Se hace al iniciar Luna."""
        self._sintetizar("hola")

    def hablar(self, texto):
        audio, sample_rate = self._sintetizar(texto)
        # Silencio antes: los auriculares Bluetooth tardan en "despertar".
        # Silencio después: evita que se corte el final por el retraso del Bluetooth.
        antes = np.zeros(int(sample_rate * self._silencio_inicial), dtype="int16")
        despues = np.zeros(int(sample_rate * self._silencio_final), dtype="int16")
        sd.play(np.concatenate([antes, audio, despues]), sample_rate)
        sd.wait()