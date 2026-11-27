import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from commands.bluetooth import _powershell

accion = sys.argv[1] if len(sys.argv) > 1 else "leer"
if accion not in ("leer", "On", "Off"):
    print("Uso: python scripts\\22_probar_bluetooth.py [leer|On|Off]")
    raise SystemExit

inicio = time.perf_counter()
datos = _powershell(accion)
print(f"{accion}: {datos}  ({time.perf_counter() - inicio:.1f} s)")