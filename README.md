# IosCam

Zero-cost iPhone 12 Pro → USB → Windows camera pipeline with a small Windows control panel and an OBS workflow.

```text
iPhone 12 Pro
AVCaptureSession 1080p60
        ↓
VideoToolbox H.264
        ↓
TCP :2345 over Apple usbmux / Lightning
        ↓
Windows + pymobiledevice3
        ↓
PyAV decode → Windows filters → IosCam Preview
        ↓
OBS Window Capture → OBS Virtual Camera → browser / chat site
```

## Daily use

On the iPhone:

1. Keep Developer Mode enabled.
2. Open **IosCam**.
3. Tap **Start Camera** and leave the app in the foreground.

On Windows, double-click:

```text
start_ioscam.bat
```

For IosCam + best-effort automatic OBS launch:

```text
start_ioscam_obs.bat
```

There is no need to activate `.venv` manually. On first run the BAT file calls `scripts/setup_windows.ps1` and creates/repairs the environment.

## Windows controls

The control panel can change these iPhone camera settings live over the same USB TCP connection:

- Rear Wide 1×
- Rear Ultra Wide 0.5×
- Rear Telephoto
- Front camera
- Zoom
- Exposure bias
- Autofocus on/off
- Manual focus position

These image operations are applied on Windows after decode:

- Blur
- Brightness
- Contrast
- Saturation
- Sharpness
- Mirror
- Rotation 0/90/180/270
- Stats overlay
- Fullscreen preview

The preview window has a stable title: **`IosCam Preview`**.

## OBS setup — one time

1. Start `start_ioscam.bat` and make sure `IosCam Preview` is showing video.
2. Open OBS.
3. Add **Source → Window Capture**.
4. Select the **IosCam Preview** window.
5. Fit/crop it in your scene.
6. In OBS press **Start Virtual Camera**.
7. In the browser/chat site choose **OBS Virtual Camera** as the camera.

You do not need a custom Windows camera driver for this workflow.

## USB prerequisites

- Standalone iTunes / Apple Mobile Device Support installed.
- `Apple Mobile Device Service` running.
- iPhone unlocked and trusted by the PC.
- Data-capable Lightning cable.

Quick test:

```powershell
C:\ioscam\.venv\Scripts\python.exe -m pymobiledevice3 usbmux list
```

The device should show `ConnectionType: USB`.

## Build updated iOS IPA for 0 ₽

Push the project to the public GitHub repo. **Actions → Build unsigned iOS IPA** compiles it on a macOS runner. Download the `IosCam-unsigned` artifact, sign/install locally with Sideloadly, then trust the development profile on the iPhone.

No Apple passwords, PATs or signing secrets belong in the repository.

## Tests

```powershell
C:\ioscam\.venv\Scripts\python.exe -m pip install -r receiver\requirements-dev.txt
C:\ioscam\.venv\Scripts\python.exe -m pytest -q
```

Protocol notes: `docs/protocol.md`.
