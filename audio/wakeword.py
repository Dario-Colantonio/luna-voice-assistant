import json

from vosk import KaldiRecognizer, Model, SetLogLevel


class DetectorWakeWord:
    """Detecta la frase de activación usando Vosk con una gramática restringida."""

    def __init__(self, ruta_modelo, frase="che luna", sample_rate=16000):
        SetLogLevel(-1)  # silencia los mensajes internos de Vosk
        self._frase = frase
        self._modelo = Model(str(ruta_modelo))
        self._sample_rate = sample_rate
        self.ultimo_texto = ""  # lo último que Vosk entendió (sirve para depurar)

        # Gramática con "competidores": cada palabra suelta de la frase tiene
        # su propio camino. Sin esto, «che» solo se forzaría a encajar en
        # «che luna» y daría falsas activaciones.
        palabras = frase.split()
        gramatica = json.dumps([frase, *palabras, "[unk]"])
        self._reconocedor = KaldiRecognizer(self._modelo, sample_rate, gramatica)

    def procesar(self, bloque):
        """Recibe un bloque de audio (bytes, int16). Devuelve True si oyó la frase."""
        if not self._reconocedor.AcceptWaveform(bloque):
            return False  # la frase todavía no terminó
        texto = json.loads(self._reconocedor.Result()).get("text", "")
        if texto:
            self.ultimo_texto = texto
        return self._frase in texto

    def reiniciar(self):
        """Descarta el audio a medio procesar (por ejemplo, tras una pausa)."""
        self._reconocedor.Reset()