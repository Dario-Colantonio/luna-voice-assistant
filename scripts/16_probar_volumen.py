import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from commands.volumen import _control, _fijar, _leer

original = _leer()
print(f"Volumen actual: {original}")
print(f"Rango en dB (mínimo, máximo, paso): {_control().GetVolumeRange()}")

for pedido in [10, 18, 20, 28, 30]:
    _fijar(pedido)
    exacto = _control().GetMasterVolumeLevelScalar() * 100
    print(f"\nPedido {pedido} -> Python lee {_leer()} (exacto {exacto:.1f})")
    input("Mirá el número en la barra de volumen de Windows y apretá Enter...")

_fijar(original)
print(f"\nRestaurado a {original}")