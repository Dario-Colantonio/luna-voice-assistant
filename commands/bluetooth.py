import base64
import subprocess

from core.registry import comando

SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Código de PowerShell que usa la API de radios de Windows. __ACCION__ se
# reemplaza por: leer (solo consulta), On (encender) u Off (apagar).
_PLANTILLA = r"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$accion = '__ACCION__'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]

function Await($tarea, $tipoResultado) {
    $asTask = $asTaskGeneric.MakeGenericMethod($tipoResultado)
    $netTask = $asTask.Invoke($null, @($tarea))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioState,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null

$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$bt = $radios | Where-Object { $_.Kind -eq 'Bluetooth' } | Select-Object -First 1
if (-not $bt) { 'RESULTADO:sin_bluetooth'; exit 0 }

if ($accion -ne 'leer') {
    $estado = [Windows.Devices.Radios.RadioState]$accion
    $res = Await ($bt.SetStateAsync($estado)) ([Windows.Devices.Radios.RadioAccessStatus])
    "RESULTADO:$res"
}
"ESTADO:$($bt.State)"
"""


def _powershell(accion):
    """Ejecuta la acción ('leer', 'On' u 'Off'). Devuelve un diccionario con lo que informó."""
    if accion not in ("leer", "On", "Off"):
        raise ValueError(f"Acción desconocida: {accion}")
    codigo = _PLANTILLA.replace("__ACCION__", accion)
    codificado = base64.b64encode(codigo.encode("utf-16-le")).decode()
    resultado = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", codificado],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        creationflags=SIN_VENTANA,
    )
    datos = {}
    for linea in resultado.stdout.splitlines():
        if linea.startswith(("RESULTADO:", "ESTADO:")):
            clave, valor = linea.split(":", 1)
            datos[clave] = valor.strip()
    return datos


def _cambiar(accion, hecho):
    datos = _powershell(accion)
    if datos.get("RESULTADO") == "sin_bluetooth":
        return "No encontré Bluetooth en esta computadora."
    if datos.get("RESULTADO") == "Allowed":
        return hecho
    return "No pude cambiar el Bluetooth."


@comando("activar bluetooth")
def activar():
    return _cambiar("On", "Bluetooth activado.")


@comando("desactivar bluetooth", "apagar bluetooth")
def desactivar():
    return _cambiar("Off", "Bluetooth desactivado.")