# IosCam — English documentation

[← Home](README.md) · [Русский](README_RU.md) · [Full installation](docs/INSTALL_EN.md) · [Troubleshooting](docs/TROUBLESHOOTING_EN.md)

**IosCam** turns an iPhone into a wired 1080p60 Windows camera without Camo Pro, DroidCam, or a Wi-Fi video hop.

```text
iPhone
  ↓  AVCaptureSession 1920×1080 @ 60
VideoToolbox H.264
  ↓
Lightning / USB + Apple usbmux
  ↓
IosCam on Windows
  ↓
IosCam Preview
  ↓
OBS Window Capture
  ↓
OBS Virtual Camera
  ↓
browser / Discord / chat site / video app
```

## Features

### Control the iPhone camera from Windows

- Rear Wide 1×
- Rear Ultra Wide 0.5×
- Rear Telephoto
- Front
- Zoom 1–5×, clamped to the selected device's supported range
- Exposure bias
- Autofocus on/off
- Manual focus position

If a lens does not exist on a given iPhone or has no 1920×1080@60 format, the iOS app will report an error. That is a device/capture-format limitation.

### Windows image processing

- Blur
- Brightness
- Contrast
- Saturation
- Sharpness
- Mirror
- Rotation 0/90/180/270
- Stats overlay
- Fullscreen preview

Blur currently affects the entire frame. AI person/background segmentation is not implemented yet.

## Daily use

After one-time setup:

1. Connect and unlock the iPhone with a data-capable cable.
2. On iPhone open **IosCam** → **Start Camera**.
3. On Windows run:

```text
C:\ioscam\start_ioscam.bat
```

The BAT uses the local `.venv`, repairs missing dependencies if needed, and launches the IosCam control panel. If OBS is installed in a standard location, the launcher also attempts to open OBS.

4. In OBS, create a **Window Capture** for **`IosCam Preview`** once.
5. Click **Start Virtual Camera**.
6. In your website/app choose **OBS Virtual Camera**.

## Requirements

- x64 Windows; tested on Windows 11
- Python 3.12+ x64
- iPhone running iOS 17+; tested on iPhone 12 Pro / iOS 26.6.1
- Data-capable USB/Lightning cable
- Apple Mobile Device Service
- Sideloadly to sign/install the unsigned IPA
- OBS Studio for the virtual-camera layer

Full guide: **[docs/INSTALL_EN.md](docs/INSTALL_EN.md)**.

## USB transport

IosCam does not upload the live camera stream to a cloud server. The iOS app listens on device TCP port `2345`, and the Windows receiver reaches that port through Apple usbmux over the physical USB connection. On Windows, `pymobiledevice3` talks to Apple Mobile Device Service; Apple's Windows usbmux endpoint is exposed through loopback `127.0.0.1:27015`.

Verify the device:

```powershell
C:\ioscam\.venv\Scripts\python.exe -m pymobiledevice3 usbmux list
```

The iPhone should appear with `ConnectionType: USB`.

## Build the IPA for $0

`.github/workflows/build-ios.yml` builds an **unsigned** `IosCam-unsigned.ipa` on a GitHub-hosted macOS/Xcode runner. The repository never needs your Apple password, signing certificate, or GitHub PAT for that build.

If a recent green Actions run has an **IosCam-unsigned** artifact, download it. If it has expired, fork the repository, enable Actions, and manually run **Build unsigned iOS IPA**.

Sign/install the resulting IPA locally with Sideloadly and your own Apple ID. A free Apple ID normally signs sideloaded apps for 7 days; Sideloadly also provides an auto-refresh option.

## OBS

First confirm that **`IosCam Preview`** is displaying video.

In OBS:

1. Sources → `+` → **Window Capture**.
2. Window → **IosCam Preview**.
3. If needed set Settings → Video to 1920×1080 / 60 FPS.
4. Controls → **Start Virtual Camera**.
5. In the target browser/app choose **OBS Virtual Camera**.

Official OBS guide: https://obsproject.com/kb/virtual-camera-guide

## Privacy and secrets

**Never commit or paste publicly:**

- GitHub Personal Access Token / token
- Apple ID password
- signing certificates / private keys
- raw `pymobiledevice3 lockdown info`

`lockdown info` can include **IMEI, serial number, phone number, ICCID/IMSI, MAC addresses, and other device identifiers**. Redact them before sharing logs.

If a token is exposed in chat, an issue, a commit, or a screenshot, revoke it and create a new one.

## Tests

```powershell
C:\ioscam\.venv\Scripts\python.exe -m pip install -r receiver\requirements-dev.txt
C:\ioscam\.venv\Scripts\python.exe -m pytest -q
```

## Current limitations / roadmap

Current scope:

- 1080p60 H.264
- no audio transport
- no 4K60 yet
- no native Windows virtual-camera driver
- OBS is the virtual-camera layer
- full-frame blur instead of AI background blur

Natural next steps include cleaner H.264 keyframe resync, 4K60/HEVC, background segmentation, audio, and an optional direct Windows virtual-camera backend.

## Support

Start with **[docs/TROUBLESHOOTING_EN.md](docs/TROUBLESHOOTING_EN.md)**.

When filing a GitHub Issue, do not publish IMEI/serial/phone/token values. Include your Windows version, iPhone/iOS version, the exact error/command, and whether `pymobiledevice3 usbmux list` sees the iPhone over USB.

## License

IosCam project source is [MIT](LICENSE). Third-party dependencies retain their own licenses: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
