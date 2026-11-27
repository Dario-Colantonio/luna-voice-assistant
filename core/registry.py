import importlib
import inspect
import pkgutil
from dataclasses import dataclass
from typing import Callable

from core.texto import analizar


@dataclass
class Comando:
    frase: str              # la frase original, tal como se escribió
    funcion: Callable
    palabras: list          # parte fija de la frase, ya normalizada
    tiene_parametro: bool   # True si termina en {algo}


_COMANDOS = []


def comando(*frases):
    """Etiqueta que registra una función como comando.

    Ejemplos:
        @comando("subir volumen")
        @comando("abrir {app}")      # lo que sigue se entrega como 'parametro'
    """

    def decorador(funcion):
        for frase in frases:
            partes = frase.split()
            tiene_parametro = bool(partes) and partes[-1].startswith("{") and partes[-1].endswith("}")
            fija = " ".join(partes[:-1] if tiene_parametro else partes)
            palabras, _ = analizar(fija)
            _COMANDOS.append(Comando(frase, funcion, palabras, tiene_parametro))
        return funcion

    return decorador


def comandos_registrados():
    return list(_COMANDOS)


def descubrir_comandos():
    """Importa todos los archivos de la carpeta commands/, y con eso se registran solos."""
    import commands

    for modulo in pkgutil.iter_modules(commands.__path__):
        importlib.import_module(f"commands.{modulo.name}")


def ejecutar_funcion(cmd, parametro, numero, absoluto=False):
    """Llama a la función pasándole solo los datos que declara necesitar."""
    declarados = inspect.signature(cmd.funcion).parameters
    datos = {"parametro": parametro, "numero": numero, "absoluto": absoluto}
    return cmd.funcion(**{k: v for k, v in datos.items() if k in declarados})