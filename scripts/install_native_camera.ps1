[CmdletBinding()]
param(
    [string]$Installer
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot

$Build = [Environment]::OSVersion.Version.Build
if ($Build -lt 22000) {
    throw "Native Media Foundation mode requires Windows 11 build 22000 or newer. Current build: $Build"
}

$Broker = Join-Path $env:ProgramFiles 'OBS2MF\Vcam.Broker.exe'
if (Test-Path $Broker) {
    Write-Host "[IosCam] Media Foundation bridge already installed: $Broker" -ForegroundColor Green
    exit 0
}

if (-not $Installer) {
    $SearchRoots = @(
        (Join-Path $Root 'native\dist'),
        (Join-Path $HOME 'Downloads')
    ) | Where-Object { Test-Path $_ }

    $Candidate = foreach ($Dir in $SearchRoots) {
        Get-ChildItem -Path $Dir -Filter 'OBS2MF-Setup-*.exe' -File -ErrorAction SilentlyContinue
    }
    $Installer = $Candidate | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
}

if (-not $Installer) {
    Write-Host '[IosCam] Local OBS2MF installer not found; downloading the latest upstream release...' -ForegroundColor Cyan
    $Api = 'https://api.github.com/repos/mbales-tech/OBS2MF/releases/latest'
    $Headers = @{ 'User-Agent' = 'IosCam-native-installer' }
    try {
        $Release = Invoke-RestMethod -Uri $Api -Headers $Headers
        $Asset = $Release.assets | Where-Object { $_.name -like 'OBS2MF-Setup-*.exe' } | Select-Object -First 1
        if (-not $Asset) { throw 'Latest release does not contain OBS2MF-Setup-*.exe.' }
        $DownloadDir = Join-Path $env:TEMP 'IosCam-native'
        New-Item -ItemType Directory -Path $DownloadDir -Force | Out-Null
        $Installer = Join-Path $DownloadDir $Asset.name
        Invoke-WebRequest -Uri $Asset.browser_download_url -Headers $Headers -OutFile $Installer
        Write-Host "[IosCam] Downloaded: $Installer"
    }
    catch {
        Write-Host '[IosCam] Automatic download failed.' -ForegroundColor Yellow
        Write-Host '[IosCam] Download OBS2MF-Setup-*.exe manually from:'
        Write-Host '[IosCam] https://github.com/mbales-tech/OBS2MF/releases'
        throw
    }
}

if (-not (Test-Path $Installer)) {
    throw "Native bridge installer missing: $Installer"
}

Write-Host "[IosCam] Installing Media Foundation bridge: $Installer"
$Process = Start-Process -FilePath $Installer -Verb RunAs -Wait -PassThru
if ($Process.ExitCode -ne 0) {
    throw "Installer exited with code $($Process.ExitCode)."
}

if (-not (Test-Path $Broker)) {
    throw "Installer completed but broker was not found at $Broker"
}

Write-Host '[IosCam] Native Media Foundation bridge installed.' -ForegroundColor Green
Write-Host '[IosCam] The Windows camera will appear as OBS2MF (Windows Virtual Camera).'
