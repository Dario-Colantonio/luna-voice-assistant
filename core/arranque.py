import sys
import winreg
from pathlib import Path

from core.config import RAIZ

CLAVE = r"Software\Microsoft\Windows\CurrentVersion\Run"
NOMBRE = "Luna"


def _comando():
    # pythonw.exe es Python sin ventana de consola.
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    return f'"{pythonw}" "{RAIZ / "main.py"}"'


def activado():
    """True si Luna está configurada para iniciar con Windows."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE) as clave:
            valor, _ = winreg.QueryValueEx(clave, NOMBRE)
        return valor == _comando()
    except FileNotFoundError:
        return False


def activar():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE, 0, winreg.KEY_SET_VALUE) as clave:
        winreg.SetValueEx(clave, NOMBRE, 0, winreg.REG_SZ, _comando())


def desactivar():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE, 0, winreg.KEY_SET_VALUE) as clave:
            winreg.DeleteValue(clave, NOMBRE)
    except FileNotFoundError:
        pass  # ya estaba desactivado