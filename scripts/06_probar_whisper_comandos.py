import time

import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
DURACION = 4

# Texto de ayuda: le indica a Whisper qué vocabulario esperar.
PROMPT = (
    "Comandos para el asistente: abrí Google Chrome, buscá YouTube, "
    "abrí Spotify, pausá la música, subí el volumen, bajá el volumen, "
    "bajá el brillo, prendé el Bluetooth, abrí Visual Studio Code, "
    "abrí Visual Studio Community, cerrá Visual Studio, "
    "cerrá Google Chrome, cerrá Youtube, "
    "cerrá Spotify, reproducí musica, subí el brillo"
)

print("Cargando el modelo 'small'...")
modelo = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8",
    download_root="models/whisper",
)


def transcribir(audio, prompt=None):
    t0 = time.perf_counter()
    segmentos, _ = modelo.transcribe(
        audio,
        language="es",
        beam_size=1,
        vad_filter=True,
        initial_prompt=prompt,
    )
    texto = " ".join(s.text.strip() for s in segmentos)
    return texto, time.perf_counter() - t0


print("Listo. Decí SOLO el comando, sin «Che Luna».")
while True:
    entrada = input("\nEnter para grabar (o 'q' y Enter para salir): ")
    if entrada.strip().lower() == "q":
        break

    print(f"Grabando {DURACION} segundos...")
    audio = sd.rec(
        int(DURACION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    audio = audio[:, 0]

    sin_ayuda, t1 = transcribir(audio)
    con_ayuda, t2 = transcribir(audio, PROMPT)
    print(f"Sin ayuda: {sin_ayuda!r} ({t1:.1f} s)")
    print(f"Con ayuda: {con_ayuda!r} ({t2:.1f} s)")