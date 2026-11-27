from ctypes import POINTER, cast

import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from core.config import cargar_config
from core.registry import comando


def _control():
    """Control de volumen de la salida de audio predeterminada de Windows."""
    try:
        comtypes.CoInitialize()  # cada hilo necesita inicializar COM una vez
    except OSError:
        pass

    dispositivo = AudioUtilities.GetSpeakers()
    if hasattr(dispositivo, "EndpointVolume"):  # versiones nuevas de pycaw
        return dispositivo.EndpointVolume
    interfaz = dispositivo.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interfaz, POINTER(IAudioEndpointVolume))  # versiones viejas


def _leer():
    return round(_control().GetMasterVolumeLevelScalar() * 100)


def _fijar(porcentaje):
    porcentaje = max(0, min(100, int(porcentaje)))
    _control().SetMasterVolumeLevelScalar(porcentaje / 100, None)
    return porcentaje


def _paso():
    return cargar_config().get("volumen", {}).get("paso", 10)


@comando("subir volumen")
def subir_volumen(numero=None, absoluto=False):
    if absoluto and numero is not None:
        return f"Volumen al {_fijar(numero)} por ciento."
    paso = numero if numero is not None else _paso()
    return f"Volumen al {_fijar(_leer() + paso)} por ciento."


@comando("bajar volumen")
def bajar_volumen(numero=None, absoluto=False):
    if absoluto and numero is not None:
        return f"Volumen al {_fijar(numero)} por ciento."
    paso = numero if numero is not None else _paso()
    return f"Volumen al {_fijar(_leer() - paso)} por ciento."


@comando("poner volumen", "volumen")
def poner_volumen(numero=None):
    if numero is None:
        return "No entendí a qué nivel."
    return f"Volumen al {_fijar(numero)} por ciento."


@comando("silenciar", "silenciar sonido")
def silenciar():
    _control().SetMute(1, None)
    return "Listo."


@comando("activar sonido")
def activar_sonido():
    _control().SetMute(0, None)
    return "Listo."