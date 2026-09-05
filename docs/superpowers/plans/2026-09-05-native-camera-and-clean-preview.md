# IosCam Native Camera + Clean Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the existing OBS workflow while adding a second one-click Windows 11 Media Foundation compatibility mode, plus eliminate startup H.264 decode churn and diagnose/fix the lower-frame seam seen in OBS Window Capture.

**Architecture:** OBS mode keeps the current iPhone USB receiver and branded control panel. Native compatibility mode sends the already-filtered frames directly into the installed OBS Virtual Camera driver with `pyvirtualcam`; a Media Foundation bridge (OBS2MF, built as an optional open-source dependency) republishes that DirectShow camera through `MFCreateVirtualCamera`, so browsers/apps that prefer Media Foundation can enumerate it without opening OBS Studio. The preview path normalizes decoded dimensions, captures before/after diagnostics on demand, and uses a tear-resistant display path where available.

**Tech Stack:** Python 3, asyncio, PyAV, OpenCV, pyvirtualcam, pymobiledevice3, Swift/VideoToolbox, Windows 11 Media Foundation via OBS2MF build dependency, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-04-iphone-usb-webcam-design.md`

## Global Constraints

- Budget remains 0 ₽.
- Existing OBS workflow must remain available.
- iPhone transport remains USB/usbmux only.
- Base stream remains H.264 1920×1080 @ 60 fps.
- Native compatibility mode targets Windows 11 build 22000+.
- Native compatibility mode must not require OBS Studio UI to be open.
- Existing camera controls and Windows filters must apply in both modes.
- Startup decode errors must recover without reconnect loops.
- Never hide or spoof the fact that the Media Foundation device is virtual.

---

### Task 1: H.264 startup synchronization
- [ ] Add Annex-B/IDR detection tests and decoder recovery tests.
- [ ] Make receiver wait for a keyframe before decoding and resync after invalid access units.
- [ ] Add an iOS `requestKeyframe()` path triggered when a PC connection becomes ready.
- [ ] Run Python and Swift source tests.

### Task 2: Frame normalization and seam diagnostics
- [ ] Add tests for exact-dimension normalization and aspect-preserving output fitting.
- [ ] Normalize decoded BGR frames to HELLO dimensions before rotation/filters.
- [ ] Add optional before/after debug-frame capture.
- [ ] Add a clean double-buffered preview backend when pygame is available, with OpenCV fallback.
- [ ] Run preview/filter tests.

### Task 3: Direct virtual-camera frame output
- [ ] Add tests for fan-out output and fixed 1280×720 native compatibility fitting.
- [ ] Add `pyvirtualcam` dependency and an OBS-driver frame sink.
- [ ] Wire native mode to send filtered frames directly to OBS Virtual Camera without OBS Studio UI.
- [ ] Keep normal OBS mode unchanged.

### Task 4: Media Foundation bridge packaging
- [ ] Add `build-native-camera.yml` that builds the pinned open-source OBS2MF bridge on Windows.
- [ ] Add one-time `install_native_camera.bat` and verification script.
- [ ] Add `start_ioscam_native.bat` to launch the Python feeder and installed bridge broker.
- [ ] Add Windows build/version checks and useful failure messages.

### Task 5: Documentation and verification
- [ ] Update RU/EN docs for both modes, limitations, and troubleshooting.
- [ ] Add source checks for launch scripts/workflow/native dependency attribution.
- [ ] Run full Python suite and static Swift/YAML/JSON/plist checks.
- [ ] Package full project and overlay.
