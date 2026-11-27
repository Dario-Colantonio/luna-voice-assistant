# Luna 🌙 — asistente de voz local para Windows

<!-- Cuando tengas el logo, guardalo en la carpeta docs/ y descomentá la línea siguiente:
![Logo de Luna](docs/logo.png)
-->

> **In short:** Luna is a voice assistant for Windows 10 that runs in the background. Say *"Che Luna"* and give a command: it opens and closes apps, controls volume, music and Bluetooth, and talks back. Wake-word detection, speech recognition and speech synthesis run on-device (Vosk, Whisper, Piper). Built in Python on a modest laptop (Intel Core i3, 12 GB RAM, no GPU).

Luna es un asistente de voz de escritorio para Windows 10 que reconoce, interpreta y habla **en local**: sin APIs de pago y sin que el audio salga de la computadora (solo usa Internet para descargar los modelos y para las búsquedas web). Se queda en segundo plano, se activa al decir **«Che Luna»**, entiende la orden en español rioplatense, la ejecuta en Windows y responde con voz.

Es un proyecto personal, hecho para explorar Python y el reconocimiento de voz local desde un perfil de desarrollo C# / .NET.

> Versión 1.0 · Proyecto personal, probado en una notebook Dell Inspiron 3501 (Intel Core i3, 12 GB de RAM, sin GPU dedicada).


## Qué hace

| Decís… | Luna… |
|---|---|
| «Che Luna, abrí Spotify» | abre cualquier aplicación del menú Inicio por su nombre |
| «Che Luna, cerrá WhatsApp» | cierra el programa de forma amable (si hay algo sin guardar, el programa pregunta) |
| «Che Luna, buscá recetas en YouTube» | abre la búsqueda en el navegador predeterminado |
| «Che Luna, subí el volumen al 30» / «bajá el volumen un 20 %» | fija un nivel o sube/baja una cantidad |
| «Che Luna, silenciá el sonido» | silencia o reactiva el audio |
| «Che Luna, pausá la música» / «siguiente canción» | controla Spotify o el reproductor activo |
| «Che Luna, activá el Bluetooth» | enciende o apaga la radio Bluetooth |
| «Che Luna, apagá la computadora» | programa el apagado en 60 s y avisa; «cancelá el apagado» lo detiene |
| «Che Luna, abrí Spotify y reproducí música» | ejecuta dos órdenes seguidas |

También vive en la **bandeja del sistema**: un icono verde (escuchando), naranja (atendiendo una orden) o gris (inactiva o con el micrófono desactivado), con un interruptor de micrófono por privacidad y la opción de iniciar con Windows.

## Alcance

Luna 1.0 **ejecuta órdenes**: no mantiene conversaciones ni responde preguntas generales. Fue una decisión de alcance deliberada: pocas funciones, bien hechas y completamente locales.

## Cómo funciona

```
Micrófono → Detector «Che Luna» → Grabación (hasta la pausa) → Transcripción → Intérprete → Comando → Respuesta hablada
              (Vosk)                                              (Whisper)                                  (Piper)
```

1. **Detector:** Vosk, con una gramática restringida, escucha de forma permanente con muy poco consumo de CPU.
2. **Grabación:** al detectar la frase, suena un pitido y se graba la orden hasta que hay una pausa. El umbral de silencio se adapta al ruido ambiente.
3. **Transcripción:** Whisper (`faster-whisper`, modelo `small`, en CPU con cuantización int8) convierte el audio en texto, ayudado por un texto inicial con el vocabulario esperado.
4. **Intérprete:** normaliza el texto (acentos, voseo, números dichos con palabras), parte las órdenes compuestas y elige el comando más parecido con coincidencia aproximada (`rapidfuzz`).
5. **Comando:** una función Python ejecuta la acción en Windows.
6. **Respuesta:** Piper genera la voz y Luna vuelve a escuchar, descartando el audio captado mientras hablaba.

### Estructura del proyecto

```
Luna/
├── main.py              # punto de entrada: bandeja, hilos y carga de modelos
├── config.yaml          # toda la configuración
├── core/                # asistente (estados), intérprete, registro de comandos, configuración
├── audio/               # micrófono, detector, grabación, transcripción, voz
├── commands/            # un archivo por familia de comandos (se descubren solos)
├── interface/           # icono de la bandeja del sistema
├── models/              # modelos locales (no incluidos en el repositorio)
└── scripts/             # pruebas y herramientas de calibración
```

## Tecnologías

| Pieza | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| Detección de «Che Luna» | Vosk (modelo pequeño en español) |
| Reconocimiento de voz | faster-whisper (Whisper `small`) |
| Síntesis de voz | Piper TTS (voz `es_AR-daniela-high`) |
| Interfaz | PySide6 (icono de la bandeja del sistema) |
| Audio y volumen | sounddevice, pycaw |
| Sistema | PowerShell/WinRT (Bluetooth), API de ventanas de Windows (ctypes), psutil |
| Interpretación | rapidfuzz |

## Decisiones de diseño

- **Comandos como complementos.** Agregar una función es crear un archivo en `commands/` con una función y una etiqueta con sus frases. El programa lo descubre solo, sin tocar nada más.
- **Red de seguridad para lo peligroso.** El apagado no es inmediato: se programa con cuenta regresiva y se puede cancelar, así un error de reconocimiento no cuesta trabajo perdido.
- **Robustez al ruido.** Un umbral fijo de volumen fallaba con ruido de fondo; ahora Luna estima el ruido ambiente antes de cada orden.
- **Frases que no se parezcan.** Dos acciones distintas no deben sonar parecido para el intérprete («pausar» y «pasar» se confundían).
- **Medir antes de arreglar.** Varios problemas (un pitido que no se oía, grabaciones que no terminaban) se resolvieron con mediciones, no con suposiciones.
- **Detector y reconocedor separados.** Whisper es demasiado lento para escuchar de forma permanente, así que solo se usa después de la palabra de activación.

## Requisitos

- Windows 10 de 64 bits
- Python 3.11 (otras versiones pueden no tener paquetes compilados para todas las dependencias)
- Micrófono y salida de audio
- Internet **solo** para la instalación, la descarga inicial de modelos y las búsquedas web

## Instalación

```bat
git clone https://github.com/[TU-USUARIO]/[NOMBRE-DEL-REPOSITORIO].git
cd [NOMBRE-DEL-REPOSITORIO]

py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

(`requirements.txt` lista las bibliotecas principales. Para reproducir exactamente el entorno de desarrollo, usar `requirements-lock.txt`.)

### Descargar los modelos

Los modelos no están en el repositorio por su tamaño. Se guardan en la carpeta `models/`, que hay que crear:

```bat
mkdir models
```

1. **Vosk (detector):** descargar [vosk-model-small-es-0.42](https://alphacephei.com/vosk/models) y descomprimirlo para que quede en `models/vosk-model-small-es-0.42/`.
2. **Piper (voz):**
   ```bat
   cd models
   python -m piper.download_voices es_AR-daniela-high
   cd ..
   ```
3. **Whisper:** se descarga solo, la primera vez que se ejecuta Luna (guarda el modelo en `models/whisper/`).

### Calibrar el micrófono (recomendado)

```bat
python scripts\11_calibrar_umbral.py
```

Poner el valor sugerido en `grabacion.umbral_voz` de `config.yaml`.

## Uso

```bat
python main.py
```

Con la bandeja del sistema, el icono aparece gris mientras carga (entre 15 y 50 segundos en el equipo de prueba, según qué tan ocupada esté la computadora) y se pone verde cuando está lista. Para usarla sin terminal, hacer clic derecho en el icono y activar **Iniciar con Windows**, o abrir `iniciar_luna.bat`.

## Agregar un comando

Crear un archivo en `commands/`, por ejemplo `commands/hora.py`:

```python
from datetime import datetime

from core.registry import comando


@comando("que hora es", "decime la hora")
def decir_hora():
    ahora = datetime.now()
    return f"Son las {ahora.hour} y {ahora.minute}."
```

Lo que devuelve la función es lo que Luna dice en voz alta. Las frases se escriben sin tildes y en infinitivo (el intérprete convierte «subí», «sube» o «subir» en la misma forma). Al final de una frase se puede usar `{algo}` para recibir lo que sigue, por ejemplo `@comando("abrir {app}")`.

## Configuración

Todo está en `config.yaml`:

- `grabacion`: umbral de voz, pausa que indica el final de la orden, duración máxima.
- `stt.prompt`: vocabulario que se le pasa a Whisper para mejorar el reconocimiento.
- `apps.alias`: nombres alternativos para abrir programas («visual studio community»).
- `cerrar.apps`: qué programas puede cerrar Luna y cómo reconocerlos.
- `sitios`: sitios web que se abren por nombre.
- `energia.espera_apagado`: segundos de aviso antes de apagar.

## Limitaciones conocidas

- Solo Windows, y probado en un único equipo.
- Pensado para español rioplatense; la precisión depende del micrófono y del ruido ambiente.
- Pausar y reproducir usan la tecla multimedia de Windows, que alterna; Luna consulta qué aplicaciones están reproduciendo audio para decidir si la envía.
- Los comandos de cierre solo funcionan para los programas configurados en `cerrar.apps`.
- «Apagá la computadora» es real: guardá tu trabajo y conocé la orden «cancelá el apagado» antes de usarlo.

## Licencia

**[COMPLETAR: elegir una licencia. Revisar además las licencias de las dependencias y de los modelos.]**

## Créditos

Construido sobre Whisper (OpenAI) a través de faster-whisper, Vosk, Piper TTS, PySide6, pycaw, sounddevice y rapidfuzz. Desarrollado con la ayuda de Claude (Anthropic) como compañero de programación.

**Autor:** Dario Colantonio · www.linkedin.com/in/dario-colantonio
