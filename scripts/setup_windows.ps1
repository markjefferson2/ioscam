[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host '[IosCam] Looking for Python 3.12+ x64...'
$Python = $null

if (Get-Command py -ErrorAction SilentlyContinue) {
    $Candidates = @('-3.13', '-3.12')
    foreach ($Version in $Candidates) {
        & py $Version -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) and sys.maxsize > 2**32 else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $Python = @('py', $Version)
            break
        }
    }
}

if (-not $Python -and (Get-Command python -ErrorAction SilentlyContinue)) {
    & python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) and sys.maxsize > 2**32 else 1)"
    if ($LASTEXITCODE -eq 0) { $Python = @('python') }
}

if (-not $Python) {
    throw 'Python 3.12+ x64 was not found. Install Python x64 from python.org, then run start_ioscam.bat again.'
}

$VenvPython = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPython)) {
    Write-Host '[IosCam] Creating .venv...'
    if ($Python.Count -eq 2) {
        & $Python[0] $Python[1] -m venv .venv
    } else {
        & $Python[0] -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create .venv.' }
}

Write-Host '[IosCam] Installing receiver dependencies...'
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }
& $VenvPython -m pip install -r (Join-Path $Root 'receiver\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }

$AppleService = Get-Service -ErrorAction SilentlyContinue | Where-Object {
    $_.DisplayName -like '*Apple Mobile Device*' -or $_.Name -like '*Apple*Mobile*Device*'
} | Select-Object -First 1

if (-not $AppleService) {
    Write-Warning 'Apple Mobile Device Service was not found. Install standalone iTunes / Apple Mobile Device Support.'
} elseif ($AppleService.Status -ne 'Running') {
    Write-Warning "Apple Mobile Device Service is $($AppleService.Status). Start it from an elevated PowerShell."
} else {
    Write-Host "[IosCam] Apple service: $($AppleService.DisplayName) ($($AppleService.Status))"
}

Write-Host '[IosCam] Setup complete.'
