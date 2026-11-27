import queue

import sounddevice as sd


class Microfono:
    """Abre el micrófono y entrega el audio en bloques."""

    def __init__(self, sample_rate=16000, tamano_bloque=4000):
        self.sample_rate = sample_rate
        self._tamano_bloque = tamano_bloque
        self._cola = queue.Queue()
        self._stream = None

    @property
    def activo(self):
        return self._stream is not None

    def _callback(self, datos, frames, tiempo, estado):
        # Sounddevice llama a esta función desde otro hilo con cada bloque.
        # Solo lo guardamos en la cola; el procesamiento se hace afuera.
        if estado:
            print(estado)
        self._cola.put(bytes(datos))

    def iniciar(self):
        """Abre el micrófono. Si ya estaba abierto, no hace nada."""
        if self._stream is not None:
            return
        self.vaciar()
        self._stream = sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=self._tamano_bloque,
            dtype="int16",
            channels=1,
            callback=self._callback,
        )
        self._stream.start()

    def detener(self):
        """Cierra el micrófono de verdad (el icono de Windows se apaga)."""
        if self._stream is None:
            return
        self._stream.stop()
        self._stream.close()
        self._stream = None

    def leer(self, timeout=1.0):
        """Devuelve el siguiente bloque de audio, o None si no llegó ninguno."""
        try:
            return self._cola.get(timeout=timeout)
        except queue.Empty:
            return None

    def vaciar(self):
        """Descarta el audio acumulado (por ejemplo, lo captado mientras Luna hablaba)."""
        while True:
            try:
                self._cola.get_nowait()
            except queue.Empty:
                break