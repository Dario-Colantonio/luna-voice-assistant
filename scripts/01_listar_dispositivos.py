import sounddevice as sd

print("=== Dispositivos de audio detectados ===")
print(sd.query_devices())
print()
print("Entrada (micrófono) por defecto:", sd.default.device[0])
print("Salida (parlantes) por defecto:", sd.default.device[1])