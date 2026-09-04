# IosCam Stage 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add branded iOS assets, bidirectional camera controls, a styled Windows GUI, live filters/stats, one-click launchers and an OBS-friendly preview to the working IosCam USB webcam MVP.

**Architecture:** Keep the existing H.264 binary stream device→PC. Add newline-delimited JSON control messages PC→device on the same TCP socket. Run the async receiver on a background thread while Tkinter owns the Windows main thread; OpenCV remains the high-FPS preview surface OBS captures.

**Tech Stack:** Swift/SwiftUI, AVFoundation, Network.framework, VideoToolbox, Python 3, asyncio, Tkinter, PyAV, OpenCV, pymobiledevice3, NumPy.

**Spec:** `docs/superpowers/specs/2026-09-04-ioscam-stage3-design.md`

## Global Constraints
- Keep current 1920×1080 @ 60 fps H.264 USB transport.
- Keep device TCP port 2345.
- Budget remains 0 ₽.
- Windows launch must work without activating the venv manually.
- OBS integration uses Window Capture + OBS Virtual Camera, not a custom driver.
- App display name is `IosCam`.
- Do not add 4K60, HEVC, audio or an OBS plugin in this stage.

---

### Task 1: Receiver stats and image transforms

**Files:**
- Create: `receiver/stats.py`
- Create: `receiver/filters.py`
- Modify: `receiver/preview.py`
- Modify: `receiver/queueing.py`
- Test: `tests/test_stats.py`
- Test: `tests/test_video_output.py`
- Create: `tests/test_filters.py`

**Interfaces:**
- Produces `StreamStats`, `StatsSnapshot`, `FilterSettings`, `apply_filters`, `rotate_bgr`, `rotated_dimensions`, `OpenCVPreview`.

- [ ] Write/confirm failing tests for stats, rotation and filters.
- [ ] Run those tests and confirm RED because production APIs are absent.
- [ ] Implement stats, queue counters, rotation and filter pipeline.
- [ ] Run focused tests and confirm GREEN.
- [ ] Commit `feat: add live video filters and stream stats`.

### Task 2: Bidirectional camera control channel

**Files:**
- Create: `receiver/control.py`
- Modify: `receiver/session.py`
- Create: `tests/test_control.py`
- Modify: `ios/IPhoneCam/Network/StreamServer.swift`
- Create: `ios/IPhoneCam/Camera/CameraControl.swift`
- Modify: `ios/IPhoneCam/Camera/CameraCapture.swift`
- Modify: `ios/IPhoneCam/App/CameraStreamerModel.swift`
- Modify: `ios/IPhoneCam/IPhoneCam.xcodeproj/project.pbxproj`
- Create: `tests/test_ios_control_source.py`

**Interfaces:**
- Produces `CameraSettings`, `ControlChannel.update()`, newline JSON control transport, and Swift `CameraControlCommand` handling.

- [ ] Write failing Python and source-level Swift tests for control schema and camera switching hooks.
- [ ] Run focused tests and confirm RED.
- [ ] Implement Windows control state/channel and session writer task.
- [ ] Implement Swift receive loop and AVFoundation lens/zoom/exposure/focus application.
- [ ] Run focused tests and syntax checks.
- [ ] Commit `feat: control iPhone camera from Windows`.

### Task 3: Styled Windows GUI and service launcher

**Files:**
- Create: `receiver/runtime.py`
- Create: `receiver/gui.py`
- Create: `receiver/launcher.py`
- Modify: `receiver/main.py`
- Create: `tests/test_runtime.py`
- Create: `tests/test_launcher.py`

**Interfaces:**
- Produces `RuntimeState`, `IosCamGUI`, `ReceiverWorker`, and `python -m receiver.launcher`.

- [ ] Write failing tests for state snapshots, settings updates and OBS executable discovery.
- [ ] Run focused tests and confirm RED.
- [ ] Implement thread-safe runtime state, receiver worker, Tkinter GUI and optional OBS launch.
- [ ] Run focused tests and confirm GREEN.
- [ ] Commit `feat: add branded Windows control panel`.

### Task 4: One-click Windows scripts and OBS-friendly preview

**Files:**
- Create: `start_ioscam.bat`
- Create: `start_ioscam_obs.bat`
- Modify: `scripts/setup_windows.ps1`
- Modify: `receiver/requirements.txt`
- Modify: `README.md`
- Create: `tests/test_launch_scripts.py`

**Interfaces:**
- Produces double-clickable BAT entrypoints with no manual venv activation.

- [ ] Write failing static tests for launcher scripts and preview title.
- [ ] Run tests and confirm RED.
- [ ] Implement BAT bootstrap and README OBS instructions.
- [ ] Run focused tests and confirm GREEN.
- [ ] Commit `feat: add one-click OBS workflow`.

### Task 5: IosCam branding and app icon assets

**Files:**
- Create: `ios/IPhoneCam/Assets.xcassets/Contents.json`
- Create: `ios/IPhoneCam/Assets.xcassets/AppIcon.appiconset/Contents.json`
- Create: app icon PNGs in the AppIcon set
- Create: `branding/IosCamIcon-1024.png`
- Modify: `ios/IPhoneCam/Info.plist`
- Modify: `ios/IPhoneCam/App/ContentView.swift`
- Modify: `ios/IPhoneCam/IPhoneCam.xcodeproj/project.pbxproj`
- Modify: `.github/workflows/build-ios.yml`
- Create: `tests/test_branding.py`

**Interfaces:**
- Produces iOS display name `IosCam`, compiled AppIcon asset and branded in-app UI.

- [ ] Write failing branding/asset catalog tests.
- [ ] Run tests and confirm RED.
- [ ] Generate the icon source and required iPhone icon sizes.
- [ ] Wire the asset catalog into Xcode and update display copy/workflow artifact naming.
- [ ] Run plist/asset/static project checks.
- [ ] Commit `feat: brand iOS app as IosCam`.

### Task 6: Full verification and packaging

**Files:**
- Modify only files needed to fix verification failures.
- Create: `ioscam-stage3.zip` outside the repo.

**Interfaces:**
- Produces a drop-in project archive for `C:\ioscam`.

- [ ] Run full Python tests.
- [ ] Run `python -m compileall receiver tests`.
- [ ] Run Swift syntax/static checks available on Linux.
- [ ] Validate plist, JSON, YAML and Xcode project references.
- [ ] Create clean zip excluding caches and `.git`.
- [ ] Record exact Windows update/push commands for the user.
