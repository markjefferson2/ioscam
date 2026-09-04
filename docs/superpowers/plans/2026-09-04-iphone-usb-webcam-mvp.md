# iPhone USB Webcam MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a zero-cost MVP that captures 1920×1080@60 H.264 on an iPhone 12 Pro, transports it over the physical USB cable through usbmux, and previews it on Windows with bounded latency.

**Architecture:** The iOS app captures NV12 frames with AVFoundation, encodes them with VideoToolbox into Annex-B H.264, frames access units with the ICAM protocol, and serves one TCP client on device port 2345. The Windows Python receiver uses `pymobiledevice3.usbmux` to connect directly to that device TCP port, parses ICAM packets, decodes H.264 with PyAV, and displays only the newest decoded frame with OpenCV. Encoded backpressure is keyframe-aware so overload returns to the live edge instead of building an unbounded queue.

**Tech Stack:** Swift 5 / SwiftUI, AVFoundation, VideoToolbox, Network.framework, Python 3.12+, asyncio, pymobiledevice3, PyAV, OpenCV, pytest, GitHub Actions macOS 26 + Xcode 26.6.

**Spec:** `docs/superpowers/specs/2026-09-04-iphone-usb-webcam-design.md`

## Global Constraints

- Budget: 0 ₽.
- Development machine: Windows only; no local Mac.
- iPhone: iPhone 12 Pro, iOS 26.6.1.
- Runtime video transport must not require GitHub, cloud services, Internet access, or Wi‑Fi.
- MVP video mode is 1920×1080 at 60 fps, H.264, 12 Mbit/s target bitrate, GOP 60, B-frames disabled.
- Device TCP port is 2345.
- ICAM packet header is exactly 24 bytes and all multi-byte integers are big-endian.
- Apple credentials, certificates, passwords, and provisioning data must never be committed.
- Windows receiver remains Python until the MVP is stable.

---

## File Structure

- `receiver/protocol.py` — ICAM packet constants, header serialization/parsing, async exact-read helper.
- `receiver/queueing.py` — bounded keyframe-aware encoded packet queue and latest-decoded-frame mailbox.
- `receiver/usb.py` — USB-only iPhone discovery and direct usbmux socket connection to device port 2345.
- `receiver/decoder.py` — H.264 Annex-B decoder wrapper around PyAV.
- `receiver/preview.py` — OpenCV preview and FPS/status reporting.
- `receiver/session.py` — one connected stream session: HELLO validation, packet ingest, decode, display queues.
- `receiver/main.py` — reconnect loop and CLI entry point.
- `receiver/requirements.txt` — runtime Python dependencies.
- `receiver/requirements-dev.txt` — test dependencies.
- `tests/test_protocol.py` — wire-format and partial-read tests.
- `tests/test_queueing.py` — overload/keyframe recovery and latest-frame tests.
- `tests/test_usb.py` — USB-only selection behavior using fakes.
- `tests/test_decoder.py` — generated H.264 integration decode test when PyAV is available.
- `ios/IPhoneCam/IPhoneCam.xcodeproj/project.pbxproj` — Xcode project.
- `ios/IPhoneCam/App/IPhoneCamApp.swift` — SwiftUI entry point.
- `ios/IPhoneCam/App/ContentView.swift` — minimal Start/Stop/status UI.
- `ios/IPhoneCam/App/CameraStreamerModel.swift` — top-level iOS streaming state coordinator.
- `ios/IPhoneCam/Camera/CameraCapture.swift` — 1080p60 rear-wide AVFoundation capture.
- `ios/IPhoneCam/Camera/H264Encoder.swift` — low-latency VideoToolbox H.264 and AVCC→Annex-B conversion.
- `ios/IPhoneCam/Network/PacketProtocol.swift` — ICAM header/HELLO/video packet serialization.
- `ios/IPhoneCam/Network/StreamServer.swift` — NWListener, single-client TCP send path, bounded pending frame.
- `ios/IPhoneCam/Info.plist` — camera permission and app metadata.
- `.github/workflows/build-ios.yml` — unsigned device build and `.ipa` packaging on macOS 26/Xcode 26.6.
- `scripts/setup_windows.ps1` — Python venv/dependency setup and Apple service check.
- `scripts/check_iphone.ps1` — verifies Apple Mobile Device Service and `pymobiledevice3 usbmux list`.
- `scripts/run_receiver.ps1` — activates venv and runs receiver.
- `docs/protocol.md` — human-readable ICAM protocol reference.
- `README.md` — build, sideload, USB setup, run, and troubleshooting instructions.

---

### Task 1: Python ICAM protocol

**Files:**
- Create: `receiver/__init__.py`
- Create: `receiver/protocol.py`
- Create: `tests/test_protocol.py`

**Interfaces:**
- Produces: `PacketType`, `Packet`, `PacketHeader`, `encode_packet(packet) -> bytes`, `decode_header(data) -> PacketHeader`, `async read_packet(reader) -> Packet`.
- `VIDEO_FLAG_KEYFRAME = 0x0001`.
- `MAX_PAYLOAD_LEN = 32 * 1024 * 1024`.

- [ ] **Step 1: Write failing protocol tests**

```python
from receiver.protocol import Packet, PacketType, decode_header, encode_packet


def test_round_trip_header_and_payload():
    packet = Packet(PacketType.VIDEO, 1, 123456789, 42, b"abc")
    wire = encode_packet(packet)
    header = decode_header(wire[:24])
    assert header.packet_type is PacketType.VIDEO
    assert header.flags == 1
    assert header.payload_len == 3
    assert header.timestamp_ns == 123456789
    assert header.sequence == 42
    assert wire[24:] == b"abc"
```

Also cover invalid magic, invalid version, payload bounds, and partial async reads with a fake reader.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_protocol.py -v`
Expected: import/module failures because implementation does not exist.

- [ ] **Step 3: Implement fixed 24-byte big-endian protocol**

Use `struct.Struct(">4sBBHIQI")`, `MAGIC=b"ICAM"`, version `1`, and reject payloads larger than 32 MiB before reading them.

- [ ] **Step 4: Run protocol tests**

Run: `python -m pytest tests/test_protocol.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add receiver tests/test_protocol.py
git commit -m "feat: add ICAM wire protocol"
```

### Task 2: Bounded live-edge queues

**Files:**
- Create: `receiver/queueing.py`
- Create: `tests/test_queueing.py`

**Interfaces:**
- Consumes: `Packet`, `PacketType`, `VIDEO_FLAG_KEYFRAME`.
- Produces: `KeyframeAwareVideoQueue(maxsize: int)`, `await put(packet)`, `await get() -> Packet`, `LatestFrameMailbox.put(frame)`, `await get()`.

- [ ] **Step 1: Write failing queue tests**

Test that normal packets remain FIFO, overflow clears stale encoded data, non-keyframes are discarded while recovering, the next keyframe resumes delivery, and the decoded-frame mailbox replaces an older unconsumed frame.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_queueing.py -v`
Expected: module/import failures.

- [ ] **Step 3: Implement keyframe-aware overload behavior**

Keep an `asyncio.Queue` bounded by `maxsize`. On overflow, drain the queue, enter `await_keyframe`, discard non-keyframes, then accept the first keyframe and return to normal operation. The decoded mailbox has capacity one and replaces the previous item before inserting a new one.

- [ ] **Step 4: Run queue tests**

Run: `python -m pytest tests/test_queueing.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add receiver/queueing.py tests/test_queueing.py
git commit -m "feat: add bounded live video queues"
```

### Task 3: USB-only iPhone transport

**Files:**
- Create: `receiver/usb.py`
- Create: `tests/test_usb.py`

**Interfaces:**
- Produces: `async find_usb_iphone() -> MuxDevice`, `async connect_device_port(port: int = 2345) -> socket.socket`.
- Uses current `pymobiledevice3.usbmux.list_devices()` and `MuxDevice.connect(port)`; only devices with `device.is_usb` are accepted.

- [ ] **Step 1: Write failing fake-device tests**

Monkeypatch `receiver.usb.list_devices` to return fake Network and USB devices. Assert USB is preferred, no-device raises `IPhoneNotFoundError`, and the selected device receives port 2345.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_usb.py -v`
Expected: import/module failures.

- [ ] **Step 3: Implement direct usbmux connection**

Call `await list_devices()`, choose the first `is_usb` device, call `await device.connect(port)`, then `sock.setblocking(False)` so `asyncio` can use it directly. Do not use Wi‑Fi devices as a fallback.

- [ ] **Step 4: Run USB tests**

Run: `python -m pytest tests/test_usb.py -v`
Expected: all pass without a physical phone.

- [ ] **Step 5: Commit**

```bash
git add receiver/usb.py tests/test_usb.py
git commit -m "feat: add direct usbmux iPhone transport"
```

### Task 4: H.264 decoder and connected stream session

**Files:**
- Create: `receiver/decoder.py`
- Create: `receiver/session.py`
- Create: `receiver/preview.py`
- Create: `tests/test_decoder.py`

**Interfaces:**
- Consumes: ICAM `HELLO` and `VIDEO` packets, bounded queues, connected nonblocking socket.
- Produces: `H264Decoder.decode(access_unit: bytes) -> list[VideoFrame]`, `StreamSession.run(sock)`, `OpenCVPreview.show(frame)`.

- [ ] **Step 1: Write decoder integration test**

If PyAV is importable, generate a tiny in-memory H.264 stream using PyAV's H.264 encoder, feed encoded packets to `H264Decoder`, and assert at least one decoded frame has the expected width/height. Use `pytest.importorskip("av")` so protocol/queue tests remain runnable before runtime dependencies are installed.

- [ ] **Step 2: Run test and verify failure**

Run: `python -m pytest tests/test_decoder.py -v`
Expected: implementation failure or skip if PyAV is absent.

- [ ] **Step 3: Implement decoder and session**

Create an H.264 `av.CodecContext`, decode each Annex-B access unit, convert displayed frames to `bgr24`, and use a one-item decoded mailbox. `StreamSession` must require a valid HELLO before video, parse compact JSON metadata, feed only VIDEO packets into the keyframe-aware queue, and cancel worker tasks cleanly on EOF/error.

- [ ] **Step 4: Run receiver tests**

Run: `python -m pytest tests -v`
Expected: all non-skipped tests pass.

- [ ] **Step 5: Commit**

```bash
git add receiver/decoder.py receiver/session.py receiver/preview.py tests/test_decoder.py
git commit -m "feat: decode and preview ICAM H264 streams"
```

### Task 5: Receiver CLI and reconnect loop

**Files:**
- Create: `receiver/main.py`
- Create: `receiver/requirements.txt`
- Create: `receiver/requirements-dev.txt`

**Interfaces:**
- Consumes: `connect_device_port()` and `StreamSession`.
- Produces: `python -m receiver.main` entry point that keeps retrying on cable/app disconnect until Ctrl+C.

- [ ] **Step 1: Add reconnect behavior test using monkeypatched transport/session**

Add a focused test that makes the first connection attempt fail and the second succeed, asserting the loop retries after the configured delay and does not terminate permanently.

- [ ] **Step 2: Run the focused test and verify failure**

Run: `python -m pytest tests/test_main.py -v`
Expected: failure because `receiver.main` does not exist.

- [ ] **Step 3: Implement CLI**

Use `argparse` options `--port` (2345), `--retry-delay` (1.0), and `--no-preview`. Print clear errors for missing Apple Mobile Device support, no USB iPhone, refused device port, malformed ICAM packets, and decoder failures.

- [ ] **Step 4: Run all Python tests**

Run: `python -m pytest tests -v`
Expected: all pass except explicitly dependency-skipped integration tests.

- [ ] **Step 5: Commit**

```bash
git add receiver tests/test_main.py
git commit -m "feat: add reconnecting Windows receiver CLI"
```

### Task 6: iOS ICAM serialization and H.264 encoder

**Files:**
- Create: `ios/IPhoneCam/Network/PacketProtocol.swift`
- Create: `ios/IPhoneCam/Camera/H264Encoder.swift`

**Interfaces:**
- Produces: `ICAMPacket.video(...) -> Data`, `ICAMPacket.hello(...) -> Data`, `H264Encoder.encode(sampleBuffer:)`, and callback `onAccessUnit(data: Data, timestampNs: UInt64, sequence: UInt32, isKeyframe: Bool)`.

- [ ] **Step 1: Implement ICAM serializer with exact 24-byte header**

Serialize magic/version/type/flags/payload length/timestamp/sequence explicitly in network byte order. `VIDEO` sets bit `0x0001` for IDR/keyframes.

- [ ] **Step 2: Implement VideoToolbox session**

Create a 1920×1080 H.264 compression session with hardware acceleration requested, real-time mode true, frame reordering false, average bitrate 12,000,000, expected FPS 60, and keyframe interval 60.

- [ ] **Step 3: Convert VideoToolbox AVCC output to Annex-B**

For keyframes, extract SPS/PPS from `CMVideoFormatDescriptionGetH264ParameterSetAtIndex` and prefix them with `00 00 00 01`. Parse each length-prefixed NAL unit from the block buffer and emit the same start code before its bytes.

- [ ] **Step 4: Add defensive encoder errors**

Fail clearly when session creation/property setup/encode fails, and invalidate the compression session on stop/deinit.

- [ ] **Step 5: Commit**

```bash
git add ios/IPhoneCam/Network/PacketProtocol.swift ios/IPhoneCam/Camera/H264Encoder.swift
git commit -m "feat: add iOS ICAM H264 encoder"
```

### Task 7: iOS capture, TCP server, and SwiftUI app

**Files:**
- Create: `ios/IPhoneCam/Camera/CameraCapture.swift`
- Create: `ios/IPhoneCam/Network/StreamServer.swift`
- Create: `ios/IPhoneCam/App/CameraStreamerModel.swift`
- Create: `ios/IPhoneCam/App/IPhoneCamApp.swift`
- Create: `ios/IPhoneCam/App/ContentView.swift`
- Create: `ios/IPhoneCam/Info.plist`
- Create: `ios/IPhoneCam/IPhoneCam.xcodeproj/project.pbxproj`

**Interfaces:**
- Consumes: `H264Encoder` and `ICAMPacket`.
- Produces: an installable iOS app that exposes TCP 2345 while streaming is active.

- [ ] **Step 1: Implement 1080p60 rear-wide capture**

Request camera permission, select `.builtInWideAngleCamera` on `.back`, find a format whose dimensions are exactly 1920×1080 and whose video-supported frame-rate range includes 60, set min/max frame duration to 1/60, and output NV12 sample buffers on a dedicated serial queue.

- [ ] **Step 2: Implement single-client `NWListener` server**

Listen on TCP 2345, replace any prior client when a new one becomes ready, send HELLO immediately, and serialize sends on one queue. Keep at most one pending encoded frame while another send is in flight; replacement drops the stale pending frame.

- [ ] **Step 3: Wire capture → encoder → server**

Start listener and camera from the model, route encoded access units to the server, and expose stopped / camera active / waiting / connected / error state to SwiftUI.

- [ ] **Step 4: Create minimal SwiftUI UI and Info.plist**

Show rear wide, 1920×1080@60, H.264, port 2345, Start/Stop button, and status. Include `NSCameraUsageDescription`.

- [ ] **Step 5: Create minimal Xcode project**

Create one iOS application target named `IPhoneCam`, deployment target 17.0, Swift 5, device architectures standard, bundle ID `dev.local.IPhoneCam`, and all source files/resources included.

- [ ] **Step 6: Commit**

```bash
git add ios/IPhoneCam
git commit -m "feat: add native iPhone streaming app"
```

### Task 8: Free GitHub Actions unsigned IPA build

**Files:**
- Create: `.github/workflows/build-ios.yml`

**Interfaces:**
- Produces: artifact `IPhoneCam-unsigned.ipa` containing `Payload/IPhoneCam.app` built for `iphoneos` arm64 without Apple credentials.

- [ ] **Step 1: Add macOS 26 workflow**

Use `runs-on: macos-26`, select `/Applications/Xcode_26.6.app`, print `xcodebuild -version`, and build Release with `CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY=""`.

- [ ] **Step 2: Package unsigned IPA**

Copy the built `.app` into `Payload/IPhoneCam.app`, zip `Payload` into `IPhoneCam-unsigned.ipa`, and upload it with `actions/upload-artifact@v4`.

- [ ] **Step 3: Validate YAML locally**

Parse `.github/workflows/build-ios.yml` with Python/PyYAML or a lightweight syntax check and inspect all paths against the project layout.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/build-ios.yml
git commit -m "ci: build unsigned iPhone IPA"
```

### Task 9: Windows setup scripts, docs, and verification

**Files:**
- Create: `scripts/setup_windows.ps1`
- Create: `scripts/check_iphone.ps1`
- Create: `scripts/run_receiver.ps1`
- Create: `docs/protocol.md`
- Create: `README.md`
- Create: `.gitignore`

**Interfaces:**
- Produces: reproducible zero-cost setup and run instructions.

- [ ] **Step 1: Add PowerShell setup**

Create `.venv` with Python 3.12, upgrade pip, install `receiver/requirements.txt`, and print a clear warning if `Apple Mobile Device Service` is not installed/running.

- [ ] **Step 2: Add iPhone connectivity check**

Run `python -m pymobiledevice3 usbmux list` and explain that the phone must be unlocked and trusted. Fail nonzero if no USB device is returned.

- [ ] **Step 3: Add receiver launcher**

Activate `.venv` and run `python -m receiver.main` with passthrough arguments.

- [ ] **Step 4: Document build/sideload/run flow**

Document public GitHub push → Actions artifact → Sideloadly/AltStore signing on Windows → Start Camera on phone → USB connection → receiver. State that free Apple-ID signing may need periodic refresh and that no Apple credentials belong in GitHub.

- [ ] **Step 5: Verify repository**

Run:

```bash
python -m pytest tests -v
python -m compileall receiver tests
python - <<'PY'
from pathlib import Path
import struct
assert struct.calcsize(">4sBBHIQI") == 24
for p in [
    Path("ios/IPhoneCam/IPhoneCam.xcodeproj/project.pbxproj"),
    Path(".github/workflows/build-ios.yml"),
    Path("README.md"),
]:
    assert p.exists(), p
print("static checks: OK")
PY
```

Expected: Python tests pass (PyAV integration may skip only when PyAV is not installed), compileall succeeds, header size is 24, and required project files exist.

- [ ] **Step 6: Commit**

```bash
git add scripts docs/protocol.md README.md .gitignore
git commit -m "docs: add zero-cost build and run workflow"
```
