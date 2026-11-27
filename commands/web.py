import webbrowser
from urllib.parse import quote_plus

from core.config import cargar_config
from core.registry import comando
from core.texto import normalizar


@comando("buscar {busqueda}")
def buscar(parametro):
    consulta = normalizar(parametro)
    sitios = cargar_config().get("sitios", {})

    # «buscá YouTube»: si es un sitio conocido, se abre directamente.
    if consulta in sitios:
        webbrowser.open(sitios[consulta])
        return f"Abro {parametro}."

    # «buscá gatos en YouTube»: búsqueda dentro de YouTube.
    final = " en youtube"
    if consulta.endswith(final):
        tema = consulta[: -len(final)]
        webbrowser.open("https://www.youtube.com/results?search_query=" + quote_plus(tema))
        return "Listo."

    # Cualquier otra cosa: búsqueda en Google.
    webbrowser.open("https://www.google.com/search?q=" + quote_plus(consulta))
    return "Busco en Internet."