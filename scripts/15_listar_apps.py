import json
import subprocess
import time

# Pedimos a PowerShell la lista de aplicaciones del menú Inicio.
# La primera parte fuerza UTF-8 para que no se rompan los acentos.
CONSULTA = (
    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
    "Get-StartApps | ConvertTo-Json"
)

t0 = time.perf_counter()
resultado = subprocess.run(
    ["powershell", "-NoProfile", "-Command", CONSULTA],
    capture_output=True,
    text=True,
    encoding="utf-8",
)
print(f"Consulta hecha en {time.perf_counter() - t0:.1f} s")

if not resultado.stdout.strip():
    print("PowerShell no devolvió nada. Error:")
    print(resultado.stderr)
    raise SystemExit

apps = json.loads(resultado.stdout)
if isinstance(apps, dict):
    apps = [apps]
print(f"Aplicaciones encontradas: {len(apps)}\n")

BUSCAR = ["chrome", "spotify", "visual studio", "code", "brave"]
for app in apps:
    nombre = app["Name"]
    if any(b in nombre.lower() for b in BUSCAR):
        print(f"{nombre}\n    {app['AppID']}")