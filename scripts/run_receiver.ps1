[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $ReceiverArgs
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    throw 'Missing .venv. Run .\scripts\setup_windows.ps1 first.'
}

& $Python -m receiver.main @ReceiverArgs
exit $LASTEXITCODE
