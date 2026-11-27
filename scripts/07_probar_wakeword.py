import json
import queue
import time

import sounddevice as sd
from vosk import KaldiRecognizer, Model, SetLogLevel

SAMPLE_RATE = 16000
BLOQUE = 4000  # muestras por bloque: 0,25 s de audio
FRASE = "che luna"

SetLogLevel(-1)  # silencia los mensajes internos de Vosk

print("Cargando el modelo de Vosk...")
modelo = Model("models/vosk-model-small-es-0.42")

# Gramática con "competidores": «che» y «luna» sueltas tienen su propio
# camino, así Vosk no necesita forzarlas a encajar en «che luna».
gramatica = json.dumps([FRASE, "che", "luna", "[unk]"])
reconocedor = KaldiRecognizer(modelo, SAMPLE_RATE, gramatica)

cola = queue.Queue()


def callback(datos, frames, tiempo_info, estado):
    """Sounddevice llama a esta función con cada bloque de audio."""
    if estado:
        print(estado)
    cola.put(bytes(datos))


print(f"\nEscuchando. Decí «{FRASE}». Ctrl+C para salir.\n")
detecciones = 0
t_inicio = time.perf_counter()
t_procesando = 0.0

try:
    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOQUE,
        dtype="int16",
        channels=1,
        callback=callback,
    ):
        while True:
            bloque = cola.get()

            t0 = time.perf_counter()
            es_final = reconocedor.AcceptWaveform(bloque)
            if es_final:
                texto = json.loads(reconocedor.Result()).get("text", "")
            t_procesando += time.perf_counter() - t0

            # Solo miramos resultados finales (la frase ya terminó).
            if not es_final or not texto:
                continue

            hora = time.strftime("%H:%M:%S")
            if FRASE in texto:
                detecciones += 1
                print(f"[{hora}] ¡DETECTADO! ({detecciones}) -> {texto!r}")
            else:
                print(f"[{hora}] (oído, no activa) -> {texto!r}")
except KeyboardInterrupt:
    total = time.perf_counter() - t_inicio
    uso = t_procesando / total * 100
    print(f"\nFin. Total de detecciones: {detecciones}")
    print(f"Tiempo escuchando: {total:.0f} s")
    print(f"Uso aproximado de un núcleo de CPU: {uso:.1f}%")