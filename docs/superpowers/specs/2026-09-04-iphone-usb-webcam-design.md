# iPhone USB Webcam — Design

Date: 2026-09-04

## Goal

Build a zero-cost, self-hosted iPhone webcam pipeline for Windows, using an iPhone 12 Pro as the camera, a physical Lightning/USB cable as the transport, and no paid webcam applications.

The first milestone is a stable 1920×1080 60 fps H.264 video stream from the iPhone to a Windows PC over USB with low latency and no latency growth over time. 4K60, HEVC, virtual camera output, and audio are later milestones.

## Constraints

- Budget: 0 ₽.
- Development machine: Windows only; no local Mac.
- iPhone: iPhone 12 Pro, iOS 26.6.1.
- iOS app must be native for reliable camera control and hardware encoding.
- iOS builds are produced by a free macOS GitHub Actions runner from a public repository.
- The Apple ID, signing certificates, passwords, and provisioning data must never be committed to the public repository.
- Runtime use must not depend on GitHub, cloud services, Internet access, or Wi‑Fi.
- Initial Windows receiver is Python for iteration speed; performance-critical parts may later move to C++ or Rust.

## Architecture

### iPhone

The native Swift application uses:

- `AVCaptureSession` for camera capture.
- The rear wide camera as the initial source.
- NV12 / `CVPixelBuffer` frames at 1920×1080 60 fps.
- `VideoToolbox` (`VTCompressionSession`) for hardware H.264 encoding.
- A TCP listener on device port 2345.
- A small framed binary protocol carrying encoded H.264 access units and metadata.

Initial encoder settings:

- Resolution: 1920×1080.
- Frame rate: 60 fps.
- Codec: H.264.
- Target bitrate: 12 Mbit/s initially, tunable upward if needed.
- Real-time encoding enabled.
- Frame reordering disabled.
- B-frames disabled.
- GOP / keyframe interval: 60 frames.
- SPS/PPS repeated before each IDR so a receiver can join mid-stream.
- Hardware encoder preferred/required where supported.

### USB transport

The Windows machine uses Apple Mobile Device connectivity through usbmux.

The logical data path is:

`iOS TCP :2345 -> usbmux over Lightning/USB -> Windows localhost forwarding -> Python receiver`

The Windows implementation initially uses `pymobiledevice3` to discover the device and establish the usbmux connection/forwarding. The transport layer is isolated behind a small interface so it can be replaced later without changing decoder or preview code.

### Windows receiver

The initial Windows receiver is Python 3.12+ and uses:

- `pymobiledevice3` for iPhone discovery / usbmux transport.
- `asyncio` for networking and stream handling.
- `PyAV` / FFmpeg libraries for H.264 decode.
- OpenCV only for the first preview/debug window.

The receiver must avoid unbounded buffering. If downstream decode or display falls behind, old video frames are dropped rather than queued indefinitely.

Later milestones may replace software decode with D3D11VA/NVDEC/QSV and expose the stream through OBS or a Windows virtual camera.

## Wire protocol

All multi-byte integers are big-endian.

Every packet has a fixed 24-byte header:

| Field | Size | Description |
|---|---:|---|
| magic | 4 bytes | ASCII `ICAM` |
| version | uint8 | Protocol version, initially 1 |
| type | uint8 | Packet type |
| flags | uint16 | Type-specific flags |
| payload_len | uint32 | Payload length in bytes |
| timestamp_ns | uint64 | Monotonic capture/encode timestamp in nanoseconds |
| sequence | uint32 | Monotonic packet/frame sequence number |

Packet types:

- `0x01 HELLO` — stream metadata/capabilities.
- `0x02 VIDEO` — one encoded H.264 access unit.
- `0x03 STATS` — optional encoder/capture stats.
- `0x04 PING` — latency/health probe.
- `0x05 PONG` — response to PING.

The `VIDEO` payload is H.264 Annex-B. SPS/PPS are emitted before each IDR access unit.

The first implementation may encode `HELLO` payload data as compact JSON for ease of debugging. Video data remains binary.

## Backpressure and latency policy

Latency stability is more important than displaying every frame.

Rules:

- The iOS sender does not maintain an unbounded encoded-frame queue.
- The Windows receiver keeps only a very small decode/display queue.
- If the receiver is behind, stale frames are discarded until it approaches the live edge.
- TCP send/receive errors terminate the current connection cleanly and return both sides to a reconnectable state.
- The iPhone app keeps the camera/encoder running or restarts them predictably according to the final implementation choice, but must never accumulate seconds of buffered video.

Latency measurement uses timestamps plus a sequence counter for internal pipeline timing. True glass-to-glass latency is measured separately with a visible millisecond timer or high-frequency flashing test source in front of the iPhone and a photo/screenshot containing both the source and Windows preview.

## Reconnect behavior

- iPhone listens continuously on port 2345 while streaming mode is active.
- Windows searches for an attached trusted iPhone.
- On cable disconnect or socket failure, Windows returns to device search/reconnect state rather than exiting permanently.
- A new receiver connection receives sufficient codec configuration (HELLO + SPS/PPS with the next IDR) to begin decoding without restarting the application.
- MVP reconnect logic may be simple, but it must not require reinstalling or rebuilding either side.

## iOS UI

The MVP UI is intentionally minimal:

- App title.
- Camera: rear wide.
- Mode: 1920×1080 @ 60.
- Codec: H.264.
- Port: 2345.
- Start/Stop button.
- Status text: stopped / camera active / waiting for PC / connected / error.

Camera controls, lens selection, exposure, focus, white balance, HEVC, and 4K modes are deferred.

## Repository layout

```text
iphone-usb-webcam/
├─ ios/
│  └─ IPhoneCam/
│     ├─ IPhoneCam.xcodeproj/
│     ├─ App/
│     ├─ Camera/
│     ├─ Network/
│     └─ Info.plist
├─ receiver/
│  ├─ main.py
│  ├─ usb.py
│  ├─ protocol.py
│  ├─ decoder.py
│  ├─ preview.py
│  └─ requirements.txt
├─ scripts/
│  ├─ setup_windows.ps1
│  ├─ run_receiver.ps1
│  └─ check_iphone.ps1
├─ .github/
│  └─ workflows/
│     └─ build-ios.yml
├─ docs/
│  └─ protocol.md
├─ docs/superpowers/specs/
│  └─ 2026-09-04-iphone-usb-webcam-design.md
└─ README.md
```

## Build and signing strategy

### CI build

A public GitHub repository uses a free GitHub-hosted macOS runner to invoke Xcode and build the iOS project.

CI must not contain Apple account secrets. It produces an unsigned/ad-hoc build artifact suitable for later local signing, or another artifact format that can be packaged for sideloading on Windows.

### Windows sideloading

The built artifact is downloaded to Windows and signed/installed using a zero-cost sideloading workflow such as Sideloadly or AltStore with the user's own Apple ID.

The exact artifact packaging/signing command is an implementation concern and will be validated early because unsigned iOS CI artifacts and Windows-side signing tools have compatibility constraints.

## Error handling

### iPhone

The app surfaces clear errors for:

- Camera permission denied.
- Requested 1080p60 format unavailable.
- Encoder creation/configuration failure.
- TCP listener failure.
- Client disconnect.
- Encode/send failure.

### Windows

The receiver surfaces clear errors for:

- Apple Mobile Device support missing.
- No trusted/unlocked iPhone detected.
- usbmux connection failure.
- Protocol magic/version mismatch.
- Malformed packet length.
- H.264 decoder initialization/decode failure.
- Stream timeout or cable disconnect.

Malformed packets and absurd payload lengths are rejected before allocation/use.

## Testing

### Protocol tests

Python unit tests cover:

- Header encode/decode.
- Big-endian field handling.
- Invalid magic/version.
- Partial TCP reads.
- Payload length bounds.
- Sequence/timestamp parsing.

Swift protocol serialization should have equivalent focused tests if practical in the CI project.

### Receiver tests

- Feed a prerecorded Annex-B H.264 stream through the same packet parser without an iPhone.
- Verify decoder produces frames.
- Verify bounded-queue/drop behavior when the consumer is intentionally slowed.
- Verify reconnect path after simulated EOF/socket error.

### End-to-end acceptance

MVP is accepted when:

- iPhone 12 Pro streams 1920×1080 60 fps H.264 over the physical cable.
- Wi‑Fi is not required for the video transport.
- Windows preview remains near 60 fps.
- Stream is stable for at least 10 minutes.
- Latency does not steadily increase over time.
- Cable unplug/replug can recover without rebuilding/reinstalling.

## Deferred milestones

After MVP validation:

1. Measure and reduce latency with hardware decode where useful.
2. OBS source and/or Windows virtual camera output.
3. 4K60 capture if exposed by the selected iPhone camera format.
4. HEVC transport/decoding.
5. Camera controls (lens, focus, ISO/exposure, white balance).
6. Optional audio with explicit A/V synchronization.
7. Packaging the Windows receiver as an `.exe` only after the Python pipeline is stable.

## Scope exclusions for MVP

The first milestone does not include:

- 4K.
- HEVC.
- Audio.
- OBS integration.
- Windows virtual camera registration.
- Automatic exposure/focus UI controls.
- Production installer.
- Python-to-EXE packaging.
