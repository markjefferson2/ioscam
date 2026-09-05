# Install IosCam from scratch — Windows + iPhone + OBS

[← English README](../README_EN.md) · [Troubleshooting](TROUBLESHOOTING_EN.md)

This is the complete path from a clean Windows machine to **OBS Virtual Camera**.

## 0. Requirements

- Windows 10/11 x64; primary tested OS is Windows 11
- Python 3.12 or 3.13 x64: https://www.python.org/downloads/windows/
- Git for Windows if using `git clone`: https://git-scm.com/download/win
- iPhone running iOS 17+; tested on iPhone 12 Pro / iOS 26.6.1
- Data-capable USB/Lightning cable
- Apple Mobile Device Service
- Sideloadly: https://sideloadly.io/
- OBS Studio: https://obsproject.com/download
- A free Apple ID is sufficient

### Important Windows iTunes/iCloud note

IosCam needs Apple Mobile Device Service. On Windows, `pymobiledevice3` uses Apple's usbmux/Apple Mobile Device Service. Sideloadly's official Windows setup recommends the **web versions of iTunes & iCloud**, not Microsoft Store versions. The simplest compatible setup is to use the Web iTunes / Web iCloud links provided at https://sideloadly.io/.

If Apple Mobile Device Service is already installed and working, do not replace the Apple stack without a reason.

## 1. Get the source

### Option A — Git

```powershell
cd C:\
git clone https://github.com/markjefferson2/ioscam.git
cd C:\ioscam
```

If you already have the repository:

```powershell
cd C:\ioscam
git pull
```

### Option B — Download ZIP

GitHub → Code → Download ZIP → extract to:

```text
C:\ioscam
```

## 2. Prepare the Windows receiver

The easiest path is simply:

```text
C:\ioscam\start_ioscam.bat
```

On first run the BAT calls `scripts/setup_windows.ps1`, creates:

```text
C:\ioscam\.venv
```

and installs `pymobiledevice3`, `av`, and `opencv-python`.

Manual setup:

```powershell
cd C:\ioscam
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Do not install IosCam dependencies into your global Python environment. The local `.venv` avoids conflicts with bots, aiogram, and other projects.

## 3. Verify Apple Mobile Device Service

```powershell
Get-Service "Apple Mobile Device Service"
```

Expected state: `Running`.

If present but stopped, from an elevated PowerShell:

```powershell
Start-Service "Apple Mobile Device Service"
```

Optional usbmux endpoint check:

```powershell
Test-NetConnection 127.0.0.1 -Port 27015
```

Expected:

```text
TcpTestSucceeded : True
```

## 4. Connect and trust the iPhone

1. Connect the iPhone over USB.
2. Unlock it.
3. Tap **Trust This Computer** if prompted.
4. Verify USB discovery:

```powershell
C:\ioscam\.venv\Scripts\python.exe -m pymobiledevice3 usbmux list
```

Expected fields include:

```json
{
  "ConnectionType": "USB",
  "DeviceClass": "iPhone"
}
```

**Do not post full `lockdown info` publicly; it can contain IMEI/serial/phone data.**

## 5. Obtain an unsigned IPA

The workflow is:

```text
.github/workflows/build-ios.yml
```

It builds on a GitHub-hosted macOS/Xcode runner and packages:

```text
IosCam-unsigned.ipa
```

### If the main repository has a fresh artifact

1. Open https://github.com/markjefferson2/ioscam/actions
2. Open the latest green **Build unsigned iOS IPA** run.
3. Under **Artifacts**, download **IosCam-unsigned**.
4. Extract the downloaded ZIP to get the `.ipa`.

The current workflow retains its artifact for 7 days.

### If the artifact expired

1. Fork the repository to your GitHub account.
2. Open Actions and enable workflows if GitHub asks.
3. Select **Build unsigned iOS IPA**.
4. Run workflow.
5. Download the artifact after a green build.

GitHub Actions is only used as a free macOS/Xcode build machine. Do not put Apple passwords, PAT tokens, signing certificates, or private keys into this repository for the unsigned build.

## 6. Sign/install with Sideloadly

Download: https://sideloadly.io/

On Windows, Sideloadly officially recommends the web versions of iTunes and iCloud; links are provided on its official website.

1. Start Sideloadly.
2. Connect the iPhone over USB.
3. Drag in `IosCam-unsigned.ipa`.
4. Select your iPhone.
5. Enter your Apple ID.
6. Click Start.

With a free Apple ID, a sideloaded app is normally valid for 7 days. Sideloadly also provides auto-refresh.

## 7. Trust the app and enable Developer Mode

If iOS reports **Untrusted Developer**:

```text
Settings
→ General
→ VPN & Device Management
→ developer profile
→ Trust / Allow & Restart
```

Recent iOS versions may require a restart.

If Developer Mode is requested:

```text
Settings
→ Privacy & Security
→ Developer Mode
→ On
```

Restart and confirm when prompted. You do not need to re-enable Developer Mode every day unless you manually turn it off.

## 8. Start IosCam

On iPhone:

1. Open **IosCam**.
2. Grant camera access.
3. Tap **Start Camera**.
4. Keep the app in the foreground.

On Windows:

```text
C:\ioscam\start_ioscam.bat
```

You should get:

- **IosCam Control** — control panel
- **IosCam Preview** — video window
- OBS is also launched automatically if found in a standard installation path

## 9. Configure OBS once

1. OBS → Sources → `+` → **Window Capture**.
2. Name it `IosCam`.
3. Window → **IosCam Preview**.
4. If needed, Transform → Fit to screen.
5. Settings → Video:

```text
Base Canvas:        1920x1080
Output Resolution:  1920x1080
FPS:                60
```

6. Controls → **Start Virtual Camera**.
7. In the target browser/Discord/chat site choose **OBS Virtual Camera**.

If the browser was already open, refresh the page or restart the browser after enabling the virtual camera.

## 10. Daily workflow

```text
1. USB connected
2. iPhone unlocked
3. IosCam → Start Camera
4. C:\ioscam\start_ioscam.bat
5. OBS → Start Virtual Camera
6. target app/site → OBS Virtual Camera
```

## Developer test suite

```powershell
cd C:\ioscam
C:\ioscam\.venv\Scripts\python.exe -m pip install -r receiver\requirements-dev.txt
C:\ioscam\.venv\Scripts\python.exe -m pytest -q
```

Next: [TROUBLESHOOTING_EN.md](TROUBLESHOOTING_EN.md).

## Optional: Native Media Foundation mode (Windows 11)

For the second output mode run once:

```text
C:\ioscam\install_native_camera.bat
```

If no local installer exists, the script downloads the official OBS2MF release installer from `mbales-tech/OBS2MF`. After the UAC install, launch:

```text
C:\ioscam\start_ioscam_native.bat
```

Requires Windows 11 build 22000+ and the OBS Virtual Camera driver (normally installed with OBS Studio).
