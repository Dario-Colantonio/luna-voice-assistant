import re
import unicodedata

# Palabras que no aportan al significado de una orden.
PALABRAS_VACIAS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "al", "por", "favor", "che", "luna",
    "pantalla",
}

# Formas en que se pueden pedir las cosas -> forma única (infinitivo).
# Si Luna no entiende un verbo, se agrega una línea acá.
VERBOS = {
    "abri": "abrir", "abre": "abrir", "abrime": "abrir", "abi": "abrir",
    "cerra": "cerrar", "cierra": "cerrar",
    "busca": "buscar", "buca": "buscar",
    "subi": "subir", "sube": "subir",
    "baja": "bajar",
    "pausa": "pausar",
    "reproduci": "reproducir", "reproduce": "reproducir",
    "prende": "activar", "prendi": "activar", "enciende": "activar", "activa": "activar",
    "apaga": "apagar", "desactiva": "desactivar",
    "cancela": "cancelar",
    "pone": "poner", "poneme": "poner",
    "silencia": "silenciar",
}

# Números dichos con palabras (Whisper a veces escribe «diez» en vez de «10»).
# «un» y «una» no están: casi siempre son artículos («subí un poco»).
UNIDADES = {
    "cero": 0, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11,
    "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16,
    "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20,
    "veintiuno": 21, "veintidos": 22, "veintitres": 23, "veinticuatro": 24,
    "veinticinco": 25, "veintiseis": 26, "veintisiete": 27, "veintiocho": 28,
    "veintinueve": 29,
}
DECENAS = {
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
    "setenta": 70, "ochenta": 80, "noventa": 90,
}


def _limpiar(texto):
    """Minúsculas, sin acentos y sin signos (se conserva el % para los números)."""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9%]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _numeros_a_cifras(limpio):
    """'treinta y cinco por ciento' -> '35 %'. Maneja de 0 a 100."""
    limpio = re.sub(r"\bpor\s+ciento\b", "%", limpio)
    palabras = limpio.split()
    salida = []
    i = 0
    while i < len(palabras):
        p = palabras[i]
        if p in DECENAS:
            valor = DECENAS[p]
            if (
                i + 2 < len(palabras)
                and palabras[i + 1] == "y"
                and 1 <= UNIDADES.get(palabras[i + 2], 0) <= 9
            ):
                valor += UNIDADES[palabras[i + 2]]
                i += 2
            salida.append(str(valor))
        elif p in UNIDADES:
            salida.append(str(UNIDADES[p]))
        elif p == "cien":
            salida.append("100")
        else:
            salida.append(p)
        i += 1
    return " ".join(salida)


def analizar(texto):
    """Devuelve (palabras, numero). Ej: 'Subí el volumen un 10%' -> (['subir','volumen'], 10)."""
    limpio = _numeros_a_cifras(_limpiar(texto))

    numero = None
    m = re.search(r"\b(\d+)\s*(?:%|por\s+ciento)?", limpio)
    if m:
        numero = int(m.group(1))
        limpio = limpio[: m.start()] + " " + limpio[m.end():]

    palabras = [p for p in limpio.split() if p not in PALABRAS_VACIAS and p != "%"]
    if palabras:
        palabras[0] = VERBOS.get(palabras[0], palabras[0])
    return palabras, numero


def normalizar(texto):
    """Minúsculas, sin acentos ni signos. Sirve para comparar nombres."""
    return _limpiar(texto)

def es_absoluto(texto):
    """True si el número es un nivel final ('al 30') y no una cantidad ('un 30')."""
    limpio = _numeros_a_cifras(_limpiar(texto))
    return re.search(r"\b(?:al|a|en)\s+\d+", limpio) is not None


def dividir_ordenes(texto):
    """'abrí Spotify y reproducí música' -> ['abri spotify', 'reproduci musica']."""
    limpio = _numeros_a_cifras(_limpiar(texto))
    partes = re.split(r"\s+(?:y|e|luego|despues)\s+", limpio)
    return [p.strip() for p in partes if p.strip()]