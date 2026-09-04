# IosCam Stage 3 Design

## Goal
Turn the working iPhone→USB→Windows MVP into a branded, single-launch desktop tool for OBS workflows while keeping the existing low-latency H.264 transport.

## User flow
1. Start `IosCam` on the iPhone and leave Developer Mode enabled.
2. Run `start_ioscam.bat` on Windows.
3. The Windows GUI finds the USB iPhone, connects to device TCP port 2345, and opens `IosCam Preview`.
4. The GUI controls lens, zoom, exposure and focus on the iPhone over the same full-duplex TCP connection.
5. Windows applies image filters and orientation after H.264 decode.
6. OBS captures the `IosCam Preview` window; OBS Virtual Camera is selected in the browser/site.

## iOS branding
- Display name: `IosCam`.
- Dark/black visual language with acid-lime accent inspired by the supplied studio site.
- App icon: black field, neon lime lens/orb, subtle orbital ring/grid motif, no text.
- Keep the internal Xcode target name `IPhoneCam` to avoid unnecessary build-system churn.

## iPhone camera controls
The Windows client sends newline-delimited UTF-8 JSON on the client→device half of the existing TCP connection. Video remains ICAM-framed binary on device→client.

Control state fields:
- `camera`: `rearWide`, `rearUltraWide`, `rearTelephoto`, `front`
- `zoom`: 1.0–5.0, clamped by the selected AVCaptureDevice
- `exposureBias`: -2.0–2.0, clamped to device limits
- `autofocus`: boolean
- `focusPosition`: 0.0–1.0 when autofocus is off

The iPhone reconfigures AVCaptureSession inputs when lens selection changes and preserves 1920×1080 @ 60 fps where supported.

## Windows GUI
Use Tkinter from the standard Windows Python distribution so no heavyweight GUI dependency is added. The control panel and preview are separate windows: Tkinter for controls and OpenCV HighGUI for the 60 fps preview.

Style:
- background approximately `#080A08`
- panel background approximately `#11140F`
- acid-lime accent approximately `#C8FF2E`
- white primary type and muted gray secondary type

Controls:
- Lens selector
- Zoom
- Exposure bias
- Autofocus toggle
- Manual focus position
- Blur
- Brightness
- Contrast
- Saturation
- Sharpness
- Mirror
- Rotation 0/90/180/270
- Stats overlay
- Fullscreen preview
- Launch OBS button

Runtime card shows connection state, resolution, ingress/display FPS, bitrate, queue depth, dropped packets, decode time and receiver-side RX→screen latency.

## Windows image pipeline
H.264 → PyAV frame → BGR ndarray → rotation/mirror → brightness/contrast/saturation → optional blur → optional sharpening → stats overlay → `IosCam Preview`.

Blur uses a reduced-resolution intermediate to keep 1080p60 practical on typical CPUs.

## Launchers
- `start_ioscam.bat`: creates `.venv` if absent, installs requirements if imports fail, then starts the GUI.
- `start_ioscam_obs.bat`: same launcher plus best-effort OBS launch.
- Primary Python entrypoint: `python -m receiver.launcher`.

## OBS integration
Stage 3 intentionally does not install a custom camera driver. OBS uses Window Capture on `IosCam Preview`; the user starts OBS Virtual Camera and selects `OBS Virtual Camera` in a browser/chat site. This is the reliability-first path.

## Non-goals
- 4K60 in this stage
- HEVC
- native OBS source plugin
- custom Windows virtual-camera driver
- audio

## Success criteria
- Existing 1080p60 USB stream remains functional.
- Lens switching works from Windows on iPhone 12 Pro.
- Filters and orientation update live without reconnecting.
- GUI can run from one BAT file.
- Preview title is stable for OBS Window Capture.
- Python test suite passes and iOS project remains CI-buildable with Xcode 26.x.
