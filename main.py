import signal
import sys
import tempfile
import threading
import traceback
import time
from pathlib import Path

from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtWidgets import QApplication

from core.config import RAIZ, cargar_config
from interface.tray import Bandeja


def _redirigir_salida():
    """Con pythonw.exe (sin consola) no hay salida estándar: se guarda en luna.log."""
    if sys.stdout is None or sys.stderr is None:
        ruta = RAIZ / "luna.log"
        modo = "w" if ruta.exists() and ruta.stat().st_size > 1_000_000 else "a"
        log = open(ruta, modo, encoding="utf-8", buffering=1)
        sys.stdout = log
        sys.stderr = log


def _construir_asistente(config, silenciada, bandeja):
    """Carga los modelos (tarda unos segundos) y arma el asistente."""
    inicio = time.perf_counter()

    def marca(etapa):
        print(f"[carga {time.strftime('%H:%M:%S')}] {etapa} (+{time.perf_counter() - inicio:.0f} s)")

    marca("empezando")
    from audio.microphone import Microfono
    from audio.stt import Transcriptor
    from audio.tts import Voz
    from audio.wakeword import DetectorWakeWord
    from core.assistant import Asistente
    from core.registry import comandos_registrados, descubrir_comandos
    marca("bibliotecas importadas")

    sr = config["audio"]["sample_rate"]

    voz = Voz(
        RAIZ / config["voz"]["modelo"],
        velocidad=config["voz"]["velocidad"],
        silencio_inicial=config["voz"]["silencio_inicial"],
        silencio_final=config["voz"].get("silencio_final", 0.4),
    )
    marca("voz cargada")
    voz.calentar()
    marca("voz calentada")

    stt = config["stt"]
    transcriptor = Transcriptor(
        stt["modelo"],
        carpeta=RAIZ / stt["carpeta"],
        idioma=stt["idioma"],
        prompt=stt["prompt"],
    )
    marca("whisper cargado")
    transcriptor.calentar()
    marca("whisper calentado")

    detector = DetectorWakeWord(
        RAIZ / config["wakeword"]["modelo"],
        frase=config["wakeword"]["frase"],
        sample_rate=sr,
    )
    marca("detector cargado")
    mic = Microfono(sr, config["audio"]["bloque"])

    descubrir_comandos()
    print(f"{len(comandos_registrados())} frases de comandos cargadas.")
    marca("listo")

    return Asistente(
        mic, detector, transcriptor, voz, config,
        al_cambiar_estado=lambda estado: bandeja.estado_cambiado.emit(estado.value),
        silenciada=silenciada,
    )


def main():
    _redirigir_salida()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # sin ventanas, la app vive en la bandeja

    # Una sola copia de Luna a la vez.
    candado = QLockFile(str(Path(tempfile.gettempdir()) / "luna.lock"))
    if not candado.tryLock(100):
        print("Luna ya está en ejecución.")
        return

    config = cargar_config()
    silenciada = threading.Event()
    asistente = {}

    def cambiar_microfono(activo):
        if activo:
            silenciada.clear()
        else:
            silenciada.set()

    def salir():
        if "obj" in asistente:
            asistente["obj"].detener()
        app.quit()

    bandeja = Bandeja(cambiar_microfono, salir)

    def trabajo():
        try:
            obj = _construir_asistente(config, silenciada, bandeja)
            asistente["obj"] = obj
            bandeja.mensaje.emit("Lista. Decí «Che Luna».")
            obj.ejecutar()
        except Exception:
            traceback.print_exc()
            bandeja.mensaje.emit("No se pudo iniciar. Mirá luna.log")

    hilo = threading.Thread(target=trabajo, daemon=True)
    hilo.start()

    # Truco para que Python atienda Ctrl+C aunque Qt esté ocupado.
    temporizador = QTimer()
    temporizador.timeout.connect(lambda: None)
    temporizador.start(500)
    signal.signal(signal.SIGINT, lambda *args: salir())

    print("Luna iniciando (el icono está en la bandeja del sistema)...")
    app.exec()

    if "obj" in asistente:
        asistente["obj"].detener()
    hilo.join(timeout=5)
    candado.unlock()


if __name__ == "__main__":
    main()