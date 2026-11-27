import subprocess

from core.config import cargar_config
from core.registry import comando

SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _espera():
    return cargar_config().get("energia", {}).get("espera_apagado", 60)


@comando("apagar computadora", "apagar compu", "apagar equipo", "apagar pc", "apagar notebook")
def apagar():
    segundos = _espera()
    resultado = subprocess.run(
        ["shutdown", "/s", "/t", str(segundos)],
        capture_output=True,
        creationflags=SIN_VENTANA,
    )
    if resultado.returncode != 0:
        return "No pude programar el apagado."
    return f"Apago la computadora en {segundos} segundos. Para cancelarlo, decí: cancelar apagado."


@comando("cancelar apagado", "cancelar apagar")
def cancelar_apagado():
    resultado = subprocess.run(
        ["shutdown", "/a"],
        capture_output=True,
        creationflags=SIN_VENTANA,
    )
    if resultado.returncode == 0:
        return "Apagado cancelado."
    return "No hay ningún apagado en curso."