from pathlib import Path

import yaml

# Carpeta raíz del proyecto (la que contiene config.yaml).
# Se calcula desde la ubicación de este archivo, así las rutas
# funcionan sin importar desde dónde se ejecute Luna.
RAIZ = Path(__file__).resolve().parent.parent


def cargar_config() -> dict:
    with open(RAIZ / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)