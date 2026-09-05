@echo off
rem OBS editing mode: IosCam Preview -> OBS Window Capture -> OBS Virtual Camera.
call "%~dp0start_ioscam.bat" --launch-obs --preview-backend pygame %*
