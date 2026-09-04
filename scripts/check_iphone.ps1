[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    throw 'Missing .venv. Run .\scripts\setup_windows.ps1 first.'
}

Write-Host '[IosCam] Checking Apple Mobile Device Service...'
$AppleService = Get-Service -ErrorAction SilentlyContinue | Where-Object {
    $_.DisplayName -like '*Apple Mobile Device*' -or $_.Name -like '*Apple*Mobile*Device*'
} | Select-Object -First 1
if (-not $AppleService) {
    throw 'Apple Mobile Device Service was not found. Install Apple Devices/iTunes support.'
}
if ($AppleService.Status -ne 'Running') {
    throw "Apple Mobile Device Service is $($AppleService.Status), not Running."
}
Write-Host "  $($AppleService.DisplayName): Running"

Write-Host '[IosCam] Looking for a USB iPhone via usbmux...'
$Probe = @'
import asyncio
from pymobiledevice3.usbmux import list_devices

async def main():
    devices = await list_devices()
    usb = [d for d in devices if d.is_usb]
    if not usb:
        print("No USB iPhone found.")
        print("Unlock the iPhone, reconnect the cable, and tap Trust This Computer.")
        raise SystemExit(2)
    for d in usb:
        print(f"USB iPhone: serial={d.serial}")

asyncio.run(main())
'@

& $Python -c $Probe
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host '[IosCam] USB transport is ready.'
