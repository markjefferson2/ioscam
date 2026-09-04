# iPhone USB Webcam MVP

Zero-cost native iPhone webcam transport for Windows.

The MVP targets an **iPhone 12 Pro** and sends **1920×1080 @ 60 fps H.264** over the **physical Lightning/USB cable**. There is no Camo/DroidCam subscription, no Wi‑Fi video path, and no cloud dependency while the camera is running.

```text
iPhone 12 Pro
AVCaptureSession (NV12 1080p60)
        ↓
VideoToolbox H.264 hardware encoder
        ↓
ICAM packets / TCP :2345
        ↓
Apple usbmux over Lightning/USB
        ↓
Windows + pymobiledevice3
        ↓
PyAV / FFmpeg H.264 decoder
        ↓
OpenCV preview
```

This is an MVP, not yet a Windows virtual camera. OBS/Virtual Camera, 4K60, HEVC, camera controls, and audio are deliberately deferred until 1080p60 USB transport is stable.

## 1. What you need

On Windows:

- Windows 10/11 x64.
- Python **3.12 x64**.
- Apple device support that installs/runs **Apple Mobile Device Service** (Apple Devices/iTunes support).
- A Lightning/USB cable that carries data, not charge-only.
- Git for pushing the iOS source to a public GitHub repository.

On the iPhone:

- IPhoneCam installed from the unsigned IPA after local signing with your Apple ID.
- Developer Mode enabled if iOS asks for it when launching a sideloaded development app.
- The app should stay in the foreground for the MVP stability test.

Do **not** put Apple ID credentials, signing certificates, passwords, or provisioning files in the repository or GitHub Actions.

## 2. Build the unsigned IPA for 0 ₽

There is no Mac requirement on your desk. Xcode runs in GitHub Actions only when you need a new iOS build.

1. Create a **public** GitHub repository.
2. Push this repository to it.
3. Open **Actions → Build unsigned iOS IPA**.
4. Run the workflow (or push a commit).
5. Download the `IPhoneCam-unsigned` artifact.
6. Extract `IPhoneCam-unsigned.ipa`.

The workflow uses `macos-26` and Xcode 26.6, builds `iphoneos`/arm64 with code signing disabled, then packages `Payload/IPhoneCam.app` into an unsigned IPA. No Apple secrets are used in CI.

## 3. Sign/install the IPA from Windows

Use a zero-cost sideloading tool such as Sideloadly/AltStore on your own Windows PC. Give the Apple ID only to the local signing tool, **not** to this repository.

General flow:

1. Connect and unlock the iPhone.
2. Tap **Trust This Computer** if prompted.
3. Give the local sideloading tool `IPhoneCam-unsigned.ipa`.
4. Sign/install it with your Apple ID.
5. On the phone, enable Developer Mode / trust the development profile if iOS asks.
6. Launch **iPhone USB Cam** and grant camera access.

A free Apple-ID development signature is temporary, so the app may need to be refreshed/re-signed periodically. That limitation affects installation only; video runtime itself is local USB.

## 4. Prepare Windows receiver

From PowerShell in the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_windows.ps1
```

Then connect/unlock the iPhone and check that usbmux sees a **USB** device:

```powershell
.\scripts\check_iphone.ps1
```

Expected ending:

```text
USB iPhone: serial=...
[IPhoneCam] USB transport is ready.
```

If this fails, do not debug video yet. First get the Apple service + trust + data cable working.

## 5. Run the camera

On the iPhone:

1. Launch **iPhone USB Cam**.
2. Tap **Start Camera**.
3. It should show `Waiting for PC over USB…`.

On Windows:

```powershell
.\scripts\run_receiver.ps1
```

The receiver directly asks Apple usbmux to connect to **device TCP port 2345**. There is no separate `iproxy` process and no localhost port-forward command to keep alive.

For decode-only troubleshooting without an OpenCV window:

```powershell
.\scripts\run_receiver.ps1 --no-preview
```

Press `Q` or `Esc` in the preview to end the current preview session. `Ctrl+C` stops the reconnect loop.

## 6. Expected behavior

The iOS side requests:

```text
rear wide camera
1920×1080
60 fps
NV12
H.264 hardware encoder
12,000,000 bit/s
RealTime = true
B-frames / frame reordering = off
GOP = 60
```

The Windows side intentionally uses bounded queues. If display/decode cannot keep up, it prefers dropping back to the next IDR over letting latency grow indefinitely.

Acceptance target for the MVP:

- approximately 60 fps preview;
- physical USB transport only;
- stable for at least 10 minutes;
- no steadily increasing delay;
- unplug/replug recovers through the receiver reconnect loop.

## 7. Troubleshooting

### `No USB iPhone found`

Check all of these before touching Python code:

```powershell
Get-Service | Where-Object { $_.DisplayName -like '*Apple Mobile Device*' }
```

The iPhone must be unlocked, paired/trusted, and connected with a data-capable cable. Replug the phone after installing Apple device support.

### `device TCP port 2345 is not reachable`

The cable/usbmux path is alive, but the iPhone app is not currently listening. Open IPhoneCam and tap **Start Camera**.

### PyAV/OpenCV missing

Rerun:

```powershell
.\scripts\setup_windows.ps1
```

The venv is `.venv`; the receiver should be run with the provided launcher so it does not accidentally use another Python installation.

### Stream starts but corrupts after heavy CPU load

The receiver is designed to clear an overloaded encoded queue and wait for the next IDR. You may see a short visual recovery at the next keyframe instead of seconds of accumulated delay. That is intentional.

### Screen locks / app goes to background

The MVP is a foreground camera application. Keep it open while testing. Background capture behavior is not part of the first milestone.

## 8. Tests

Python protocol/queue/transport tests:

```powershell
.\.venv\Scripts\python.exe -m pip install -r receiver\requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -v
```

The repository also contains portable Swift tests for the two pure wire-format helpers (`PacketProtocol` and AVCC→Annex-B conversion). GitHub's actual iOS build is the authoritative compile test for AVFoundation/VideoToolbox/Network.framework code.

Protocol details: [`docs/protocol.md`](docs/protocol.md).
