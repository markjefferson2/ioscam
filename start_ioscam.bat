@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV_PY=%CD%\.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [IosCam] First run: creating Python environment...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%CD%\scripts\setup_windows.ps1"
    if errorlevel 1 goto :fail
)

"%VENV_PY%" -c "import av, cv2, pymobiledevice3" >nul 2>&1
if errorlevel 1 (
    echo [IosCam] Dependencies are incomplete. Repairing environment...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%CD%\scripts\setup_windows.ps1"
    if errorlevel 1 goto :fail
)

echo [IosCam] Starting control panel...
"%VENV_PY%" -m receiver.launcher --launch-obs %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo [IosCam] Exited with code %RC%.
    pause
)
exit /b %RC%

:fail
echo.
echo [IosCam] Setup failed. Read the error above.
pause
exit /b 1
