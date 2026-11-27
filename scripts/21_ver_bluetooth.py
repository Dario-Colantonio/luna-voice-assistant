import base64
import subprocess

# Código de PowerShell que consulta las radios de Windows (solo lectura).
CODIGO = r"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
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

$acceso = Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus])
"Acceso: $acceso"

$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
foreach ($r in $radios) { "$($r.Kind) | $($r.Name) | $($r.State)" }
"Total de radios: $($radios.Count)"
"""

# Se pasa codificado para evitar problemas con las comillas.
codificado = base64.b64encode(CODIGO.encode("utf-16-le")).decode()
resultado = subprocess.run(
    ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", codificado],
    capture_output=True,
    text=True,
    encoding="utf-8",
    timeout=30,
)

print(resultado.stdout)
if resultado.returncode != 0 or resultado.stderr.strip():
    print("Errores:")
    print(resultado.stderr)