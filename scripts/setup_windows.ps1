[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host '[IPhoneCam] Checking Python 3.12...'
$PythonLauncher = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 -c "import sys; assert sys.version_info[:2] == (3, 12); print(sys.version)"
    if ($LASTEXITCODE -eq 0) {
        $PythonLauncher = @('py', '-3.12')
    }
}

if (-not $PythonLauncher) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw 'Python 3.12 was not found. Install Python 3.12 x64 and rerun this script.'
    }
    & python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
    if ($LASTEXITCODE -ne 0) {
        throw 'The python command is not Python 3.12. Install Python 3.12 x64 or use the py launcher.'
    }
    $PythonLauncher = @('python')
}

$VenvPython = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPython)) {
    Write-Host '[IPhoneCam] Creating .venv...'
    if ($PythonLauncher.Count -eq 2) {
        & $PythonLauncher[0] $PythonLauncher[1] -m venv .venv
    } else {
        & $PythonLauncher[0] -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create .venv.' }
}

Write-Host '[IPhoneCam] Installing receiver dependencies...'
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }
& $VenvPython -m pip install -r (Join-Path $Root 'receiver\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }

$AppleService = Get-Service -ErrorAction SilentlyContinue | Where-Object {
    $_.DisplayName -like '*Apple Mobile Device*' -or $_.Name -like '*Apple*Mobile*Device*'
} | Select-Object -First 1

if (-not $AppleService) {
    Write-Warning 'Apple Mobile Device Service was not found. Install Apple Devices/iTunes support before USB transport will work.'
} elseif ($AppleService.Status -ne 'Running') {
    Write-Warning "Apple Mobile Device Service is $($AppleService.Status). Try: Start-Service '$($AppleService.Name)' from an elevated PowerShell."
} else {
    Write-Host "[IPhoneCam] Apple service: $($AppleService.DisplayName) ($($AppleService.Status))"
}

Write-Host ''
Write-Host '[IPhoneCam] Setup complete.'
Write-Host 'Next: .\scripts\check_iphone.ps1'
