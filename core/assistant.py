import threading
import time
from collections import deque
from enum import Enum

import numpy as np
import sounddevice as sd

from audio.grabador import grabar_comando, nivel
from core.router import ejecutar


class Estado(Enum):
    ESCUCHANDO = "escuchando"   # esperando «Che Luna»  (verde)
    PROCESANDO = "procesando"   # atendiendo una orden  (naranja)
    INACTIVA = "inactiva"       # apagada o sin micrófono (gris)


class Asistente:
    """Coordina micrófono, detector, transcripción y voz."""

    def __init__(
        self, mic, detector, transcriptor, voz, config,
        al_cambiar_estado=None, silenciada=None,
    ):
        self._mic = mic
        self._detector = detector
        self._transcriptor = transcriptor
        self._voz = voz
        self._grabacion = config["grabacion"]
        self._al_cambiar_estado = al_cambiar_estado
        self._parar = threading.Event()
        # Si está activada, Luna cierra el micrófono (modo privacidad).
        self._silenciada = silenciada if silenciada is not None else threading.Event()
        self.estado = Estado.INACTIVA
        self._niveles = deque(maxlen=20)  # volumen de los últimos 5 s de escucha
        self._ruido = None

        # Pitido (880 Hz) que indica "ya podés hablar", con silencio antes
        # (para despertar auriculares Bluetooth) y un poco después.
        ajustes = config.get("pitido", {})
        duracion = ajustes.get("duracion", 0.4)
        volumen = ajustes.get("volumen", 0.6)
        previo = ajustes.get("silencio_previo", 0.35)
        sr = 16000
        t = np.linspace(0, duracion, int(sr * duracion), endpoint=False)
        tono = (np.sin(2 * np.pi * 880 * t) * volumen * 32767).astype(np.int16)
        self._tono = np.concatenate([
            np.zeros(int(sr * previo), dtype=np.int16),
            tono,
            np.zeros(int(sr * 0.2), dtype=np.int16),
        ])
        self._tono_sr = sr

    def _cambiar_estado(self, nuevo):
        if nuevo == self.estado:
            return
        self.estado = nuevo
        print(f"[estado] {nuevo.value}")
        if self._al_cambiar_estado:
            self._al_cambiar_estado(nuevo)

    def _pitido(self):
        sd.play(self._tono, self._tono_sr)
        sd.wait()

    def ejecutar(self):
        """Bucle principal. Se detiene con detener()."""
        self._parar.clear()
        try:
            while not self._parar.is_set():
                if self._silenciada.is_set():
                    # Modo privacidad: el micrófono se cierra de verdad.
                    if self._mic.activo:
                        self._mic.detener()
                    self._cambiar_estado(Estado.INACTIVA)
                    time.sleep(0.2)
                    continue

                if not self._mic.activo:
                    try:
                        self._mic.iniciar()
                    except Exception as error:
                        print(f"No se pudo abrir el micrófono: {error}")
                        self._cambiar_estado(Estado.INACTIVA)
                        time.sleep(5)
                        continue
                    self._detector.reiniciar()
                    self._niveles.clear()
                    self._cambiar_estado(Estado.ESCUCHANDO)

                bloque = self._mic.leer(timeout=0.5)
                if bloque is None:
                    continue
                self._niveles.append(nivel(bloque))
                if self._detector.procesar(bloque):
                    self._atender()
        finally:
            self._mic.detener()
            self._cambiar_estado(Estado.INACTIVA)

    def detener(self):
        self._parar.set()

    def _atender(self):
        self._cambiar_estado(Estado.PROCESANDO)
        print("¡Che Luna detectado!")

        # Ruido ambiente: el nivel "típico bajo" de los últimos 5 s de escucha.
        if len(self._niveles) >= 8:
            self._ruido = float(np.percentile(list(self._niveles), 30))
        else:
            self._ruido = None
        self._niveles.clear()

        self._pitido()
        self._mic.vaciar()  # descarta el pitido y lo captado hasta ahora

        t0 = time.perf_counter()
        audio = self._grabar()
        t_grabacion = time.perf_counter() - t0

        if audio is None:
            print("No se oyó ningún comando.")
            respuesta = "No te escuché."
        else:
            t0 = time.perf_counter()
            texto = self._transcriptor.transcribir(audio)
            t_transcripcion = time.perf_counter() - t0
            print(f"Texto: {texto!r}")
            print(f"  grabación {t_grabacion:.1f} s | transcripción {t_transcripcion:.1f} s")
            respuesta = ejecutar(texto) if texto else "No entendí."

        print(f"Respuesta: {respuesta!r}")  # <- nueva
        t0 = time.perf_counter()
        self._voz.hablar(respuesta)
        print(f"  voz {time.perf_counter() - t0:.1f} s")

        # Luna no debe oírse a sí misma: descartamos lo captado mientras hablaba.
        self._mic.vaciar()
        self._detector.reiniciar()
        self._cambiar_estado(Estado.ESCUCHANDO)

    def _grabar(self):
        g = self._grabacion
        return grabar_comando(
            self._mic,
            umbral=g["umbral_voz"],
            espera_inicio=g["espera_inicio"],
            silencio_fin=g["silencio_fin"],
            maximo=g["maximo"],
            ruido=self._ruido,
            factor_ruido=g.get("factor_ruido", 1.5),
            depurar=g.get("depurar", False),
        )