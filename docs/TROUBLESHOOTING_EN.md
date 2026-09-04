# IosCam — troubleshooting

[← English README](../README_EN.md) · [Installation](INSTALL_EN.md)

## Quick diagnostic chain

Run these in order:

```powershell
Get-Service "Apple Mobile Device Service"
Test-NetConnection 127.0.0.1 -Port 27015
C:\ioscam\.venv\Scripts\python.exe -m pymobiledevice3 usbmux list
```

Then start IosCam → Start Camera on the iPhone and run:

```text
C:\ioscam\start_ioscam.bat
```

## `Failed to connect to usbmuxd socket`

`pymobiledevice3` cannot reach Apple usbmux / Apple Mobile Device Service.

Check:

```powershell
Get-Service "Apple Mobile Device Service"
```

If it does not exist, install Apple device support/iTunes. For Windows compatibility with Sideloadly, the web iTunes + web iCloud links from https://sideloadly.io/ are the simplest combined setup.

If the service is stopped, from elevated PowerShell:

```powershell
Start-Service "Apple Mobile Device Service"
```

Check the endpoint:

```powershell
Test-NetConnection 127.0.0.1 -Port 27015
```

Expected: `TcpTestSucceeded : True`.

## `usbmux list` does not show the iPhone

```powershell
C:\ioscam\.venv\Scripts\python.exe -m pymobiledevice3 usbmux list
```

If empty:

- unlock the iPhone;
- reconnect the cable;
- accept Trust This Computer;
- try a direct USB port instead of a hub;
- verify the cable supports data;
- check that the Apple/iTunes stack itself sees the device.

## `H.264 decode failed ... Invalid data found when processing input`

If this only appears immediately after connection and the video starts shortly afterwards, the receiver attached between H.264 keyframes and recovered at the next clean keyframe.

If it **keeps repeating**:

1. iPhone: Stop Camera → Start Camera.
2. Restart `start_ioscam.bat`.
3. Make sure a second receiver process is not already connected.
4. Do not run a separate `usbmux forward` alongside the built-in receiver.
5. If reproducible, file an Issue with a sanitized error excerpt only — no device identifiers.

## Preview is rotated

IosCam Control → OUTPUT / OBS → Rotation:

```text
0 / 90 / 180 / 270
```

The current default configuration uses `90`.

## A camera/lens fails to switch

IosCam currently requires **1920×1080 @ 60 fps** for the selected camera.

Possible reasons:

- the iPhone model has no Ultra Wide/Telephoto lens;
- that lens exposes no matching 1080p60 format;
- the camera is temporarily unavailable.

Return to **Rear Wide 1×** for the baseline tested path.

## Blur uses too much CPU

Blur is processed on Windows. Reduce/disable Blur. Sharpness and other filters also add work.

For a clean transport/decode test use:

```text
Blur 0
Brightness 0
Contrast 1
Saturation 1
Sharpness 0
```

## FPS is below 60

Check separately:

- IosCam Control telemetry;
- CPU/GPU load;
- Windows filters;
- OBS Settings → Video → FPS = 60;
- scene/output constraints in OBS.

`RX→screen` is receiver-side latency, not complete glass-to-glass camera latency.

## OBS cannot see `IosCam Preview`

1. Start IosCam first and wait for preview.
2. OBS → Source → Window Capture.
3. Select **IosCam Preview**.
4. For an existing source, reopen Properties and select the window again.
5. On Windows 11, try the modern Windows Graphics Capture method if OBS offers it.

## OBS has no Start Virtual Camera button

Install/update OBS Studio: https://obsproject.com/download

Official troubleshooting: https://obsproject.com/kb/virtual-camera-troubleshooting

## The website cannot see `OBS Virtual Camera`

1. In OBS click **Start Virtual Camera**.
2. Refresh/reopen the website.
3. Check browser camera permission.
4. Select **OBS Virtual Camera**.
5. If the browser cached device enumeration, fully restart the browser.

## `.venv` / pytest / dependencies are broken

Do not use global `pip` for IosCam.

Recreate the environment:

```powershell
cd C:\ioscam
Remove-Item -Recurse -Force .venv
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Developer tests:

```powershell
C:\ioscam\.venv\Scripts\python.exe -m pip install -r receiver\requirements-dev.txt
C:\ioscam\.venv\Scripts\python.exe -m pytest -q
```

## `Python 3.12+ x64 was not found`

Install x64 Python 3.12/3.13 from https://www.python.org/downloads/windows/ and start the BAT again.

## Sideloadly cannot see the iPhone / Anisette errors

Check the current Sideloadly requirements: https://sideloadly.io/faq

Its Windows setup recommends web iTunes + web iCloud. Keep the iPhone unlocked and do the initial pairing over USB.

## iOS reports `Untrusted Developer`

On iPhone:

```text
Settings → General → VPN & Device Management
```

Select the developer profile, use Trust / Allow & Restart, then finish confirmation after restart.

## The app stops launching after a few days

Sideloadly documents 7-day validity for apps signed with a free Apple ID. Re-sign/refresh the app or enable Sideloadly auto-refresh.

## GitHub Actions IPA artifact disappeared

The current IosCam workflow uses `retention-days: 7`. If the artifact expired, run the workflow again in your fork using `workflow_dispatch`.

## Log privacy

Before posting an Issue/chat, **never expose**:

- GitHub token / PAT
- Apple ID password
- IMEI
- serial number
- phone number
- ICCID / IMSI
- full `lockdown info`

`pymobiledevice3 lockdown info` includes many private device fields. `usbmux list` is usually enough; even there, you may redact `Identifier/UniqueDeviceID` before posting.
