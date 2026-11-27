import ctypes

import comtypes
from pycaw.pycaw import AudioUtilities

from core.registry import comando

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002


def _tecla(codigo):
    """Simula apretar y soltar una tecla multimedia."""
    ctypes.windll.user32.keybd_event(codigo, 0, 0, 0)
    ctypes.windll.user32.keybd_event(codigo, 0, KEYEVENTF_KEYUP, 0)


def _suena_algo():
    """True si alguna aplicación (que no sea Luna) está reproduciendo audio."""
    try:
        comtypes.CoInitialize()  # cada hilo necesita inicializar COM una vez
    except OSError:
        pass

    for sesion in AudioUtilities.GetAllSessions():
        try:
            if not sesion.Process:
                continue  # sonidos del sistema
            if sesion.Process.name().lower().startswith("python"):
                continue  # el propio Luna (pitido y voz)
            if sesion.State == 1:  # 1 = activa
                return True
        except Exception:
            continue
    return False


@comando("pausar musica", "pausar cancion")
def pausar():
    if not _suena_algo():
        return "No hay nada sonando."
    _tecla(VK_MEDIA_PLAY_PAUSE)
    return "Listo."


@comando(
    "reproducir musica", "reproducir cancion",
    "poner musica", "poner cancion",
)
def reproducir():
    if _suena_algo():
        return "Ya está sonando."
    _tecla(VK_MEDIA_PLAY_PAUSE)
    return "Listo."


@comando("siguiente cancion", "proxima cancion")
def siguiente():
    _tecla(VK_MEDIA_NEXT_TRACK)
    return "Listo."


@comando("cancion anterior", "anterior cancion")
def anterior():
    _tecla(VK_MEDIA_PREV_TRACK)
    return "Listo."