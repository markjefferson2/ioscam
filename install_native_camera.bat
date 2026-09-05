@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_native_camera.ps1" %*
if errorlevel 1 (
    echo.
    echo [IosCam] Native camera bridge installation failed.
    pause
    exit /b 1
)
echo.
echo [IosCam] Native camera bridge is installed.
pause
