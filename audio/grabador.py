from collections import deque

import numpy as np


def nivel(bloque):
    """Volumen (RMS) de un bloque de audio en bytes int16."""
    muestras = np.frombuffer(bloque, dtype=np.int16).astype(np.float32)
    return float(np.sqrt(np.mean(muestras**2)))


def grabar_comando(
    mic,
    umbral,
    espera_inicio=4.0,
    silencio_fin=1.0,
    maximo=8.0,
    ruido=None,
    factor_ruido=1.5,
    depurar=False,
):
    """Graba desde que el usuario empieza a hablar hasta que hace una pausa.

    El límite entre "voz" y "silencio" es el mayor entre `umbral` y el ruido
    ambiente (`ruido`) multiplicado por `factor_ruido`, así se adapta a
    ambientes ruidosos.

    Devuelve el audio (numpy int16), o None si nadie habló a tiempo.
    """
    limite = umbral
    if ruido is not None:
        limite = max(umbral, ruido * factor_ruido)

    previos = deque(maxlen=2)  # últimos bloques de silencio, para no cortar la 1ª sílaba
    bloques = []
    hablando = False
    t_espera = 0.0
    t_hablando = 0.0
    t_silencio = 0.0

    if depurar:
        ruido_txt = "?" if ruido is None else f"{ruido:.0f}"
        print(f"  ruido ambiente estimado: {ruido_txt} -> límite {limite:.0f}")

    while True:
        bloque = mic.leer()
        if bloque is None:
            if not mic.activo:
                return None
            continue

        duracion = len(bloque) / 2 / mic.sample_rate  # 2 bytes por muestra
        volumen = nivel(bloque)
        fuerte = volumen > limite

        if depurar:
            marca = "VOZ" if fuerte else "   "
            print(f"  {marca} nivel {volumen:5.0f} {'#' * int(volumen / 50)}")

        if not hablando:
            if fuerte:
                hablando = True
                bloques.extend(previos)
                bloques.append(bloque)
            else:
                previos.append(bloque)
                t_espera += duracion
                if t_espera >= espera_inicio:
                    return None
        else:
            bloques.append(bloque)
            t_hablando += duracion
            if fuerte:
                t_silencio = 0.0
            else:
                t_silencio += duracion
                if t_silencio >= silencio_fin:
                    break
            if t_hablando >= maximo:
                break

    return np.frombuffer(b"".join(bloques), dtype=np.int16)