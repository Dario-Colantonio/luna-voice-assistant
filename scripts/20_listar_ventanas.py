import ctypes
from ctypes import wintypes

import psutil

user32 = ctypes.windll.user32
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

# Solo mostramos ventanas relacionadas con estas palabras (en proceso o título).
BUSCAR = [
    "spotify", "whatsapp", "code", "visual studio", "devenv",
    "configuraci", "settings", "applicationframehost",
]


def titulo(hwnd):
    largo = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(largo + 1)
    user32.GetWindowTextW(hwnd, buffer, largo + 1)
    return buffer.value


def clase(hwnd):
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, 256)
    return buffer.value


def datos_proceso(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    try:
        proceso = psutil.Process(pid.value)
        nombre = proceso.name()
    except Exception:
        return pid.value, "?", "?"
    try:
        ruta = proceso.exe()
    except Exception:
        ruta = "?"
    return pid.value, nombre, ruta


encontradas = []


def callback(hwnd, lparam):
    if user32.IsWindowVisible(hwnd):
        texto = titulo(hwnd)
        if texto:
            pid, nombre, ruta = datos_proceso(hwnd)
            if any(b in (nombre + " " + texto).lower() for b in BUSCAR):
                encontradas.append((nombre, pid, clase(hwnd), ruta, texto))
    return True


user32.EnumWindows(EnumWindowsProc(callback), 0)

for nombre, pid, cl, ruta, texto in sorted(encontradas):
    print(f"{nombre} | pid {pid} | clase {cl}\n    ruta:  {ruta}\n    título: {texto}\n")
print(f"{len(encontradas)} ventanas encontradas.")