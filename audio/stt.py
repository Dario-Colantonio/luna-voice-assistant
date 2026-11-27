import numpy as np
from faster_whisper import WhisperModel


class Transcriptor:
    """Convierte audio en texto usando Whisper (faster-whisper) en CPU."""

    def __init__(self, modelo="small", carpeta=None, idioma="es", prompt=None):
        self._modelo = WhisperModel(
            modelo,
            device="cpu",
            compute_type="int8",
            download_root=str(carpeta) if carpeta else None,
        )
        self._idioma = idioma
        self._prompt = prompt.strip() if prompt else None

    def calentar(self):
        """La primera transcripción es la más lenta; se hace al iniciar Luna."""
        silencio = np.zeros(16000, dtype=np.float32)
        segmentos, _ = self._modelo.transcribe(silencio, language=self._idioma, vad_filter=False)
        list(segmentos)  # hay que recorrer el resultado para que se ejecute

    def transcribir(self, audio):
        """Recibe audio int16 a 16 kHz (numpy) y devuelve el texto."""
        audio = audio.astype(np.float32) / 32768.0  # Whisper espera valores de -1 a 1
        segmentos, _ = self._modelo.transcribe(
            audio,
            language=self._idioma,
            beam_size=1,
            vad_filter=True,
            initial_prompt=self._prompt,
        )
        return " ".join(s.text.strip() for s in segmentos).strip()