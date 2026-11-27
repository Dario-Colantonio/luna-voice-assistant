import time

from pycaw.pycaw import AudioUtilities

print("Estados: 0 = inactiva, 1 = ACTIVA (suena), 2 = expirada")
for _ in range(12):
    print(f"\n[{time.strftime('%H:%M:%S')}]")
    for sesion in AudioUtilities.GetAllSessions():
        try:
            nombre = sesion.Process.name() if sesion.Process else "(sonidos del sistema)"
        except Exception:
            nombre = "(proceso desconocido)"
        print(f"  {nombre}: {sesion.State}")
    time.sleep(2.5)