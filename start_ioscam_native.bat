@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "BROKER=%ProgramFiles%\OBS2MF\Vcam.Broker.exe"
if not exist "%BROKER%" (
    echo [IosCam] Media Foundation bridge is not installed.
    echo [IosCam] Run install_native_camera.bat once as administrator.
    echo.
    pause
    exit /b 2
)

rem The Python process writes processed frames directly into the OBS Virtual
rem Camera driver. OBS Studio itself must NOT have its Virtual Camera running.
tasklist /FI "IMAGENAME eq Vcam.Broker.exe" 2>nul | find /I "Vcam.Broker.exe" >nul
if errorlevel 1 (
    echo [IosCam] Starting Windows Media Foundation bridge...
    start "IosCam MF Bridge" "%BROKER%"
    timeout /t 2 /nobreak >nul
)

echo [IosCam] Native compatibility mode:
echo [IosCam]   iPhone USB -^> IosCam filters -^> OBS camera driver -^> Media Foundation
call "%~dp0start_ioscam.bat" --native-mf --preview-backend auto %*
exit /b %ERRORLEVEL%
