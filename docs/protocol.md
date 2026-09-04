# ICAM protocol v1

ICAM is the deliberately small protocol between the native iPhone app and the Windows receiver. It runs over one full-duplex TCP connection on device port `2345`. The Windows client reaches that port directly through Apple usbmux over the physical USB cable; no Wi‑Fi forwarding is required.

## Header

Every packet begins with exactly 24 bytes. Multi-byte integers are unsigned and big-endian/network byte order.

| Offset | Size | Field | Value / meaning |
|---:|---:|---|---|
| 0 | 4 | `magic` | ASCII `ICAM` |
| 4 | 1 | `version` | `1` |
| 5 | 1 | `type` | packet type |
| 6 | 2 | `flags` | type-specific flags |
| 8 | 4 | `payload_len` | bytes following the header |
| 12 | 8 | `timestamp_ns` | capture presentation timestamp converted to ns |
| 20 | 4 | `sequence` | monotonically increasing frame/packet sequence |

The receiver rejects payloads above 32 MiB before allocating/reading them.

## Packet types

- `0x01 HELLO`: compact UTF-8 JSON metadata. It must be the first packet after a connection becomes ready.
- `0x02 VIDEO`: one complete H.264 access unit in Annex-B byte-stream form.
- `0x03 STATS`: reserved for later telemetry.
- `0x04 PING`: reserved for later clock/latency probing.
- `0x05 PONG`: reserved for later clock/latency probing.

The v1 receiver ignores `STATS` and `PONG`. `PING` is reserved and is not emitted by the MVP receiver.

## HELLO payload

Example:

```json
{"codec":"h264","width":1920,"height":1080,"fps":60,"bitrate":12000000}
```

The MVP receiver accepts only `codec = "h264"` and positive integer dimensions/FPS/bitrate.

## VIDEO payload

The payload is H.264 Annex-B. Each NAL unit begins with the four-byte start code:

```text
00 00 00 01
```

VideoToolbox normally emits AVCC/length-prefixed H.264. The iOS app converts every encoded sample to Annex-B before packetization.

For an IDR/keyframe, the app prepends the parameter sets from the H.264 format description, typically:

```text
00 00 00 01 <SPS>
00 00 00 01 <PPS>
00 00 00 01 <IDR...>
```

`VIDEO.flags & 0x0001 != 0` means the access unit is a keyframe/IDR. This flag lets the Windows side recover cleanly after overload: if its bounded encoded queue overflows, it discards stale dependent P-frames until the next keyframe rather than accumulating latency.

## Backpressure

There are two bounded points:

1. iOS keeps at most one pending video packet while an `NWConnection.send` is in flight. A newer frame replaces that pending packet.
2. Windows has a small encoded queue. On overflow it clears the queue and waits for the next keyframe. The decoded preview is a one-frame mailbox where a newer decoded frame replaces an old unconsumed frame.

This intentionally prefers a visible frame drop/recovery over latency that grows for seconds.


## Windows → iPhone control channel

The TCP connection is full duplex. The device→Windows direction remains ICAM-framed H.264 binary. The Windows→device direction is intentionally simpler: newline-delimited UTF-8 JSON, one complete camera state per line.

Example:

```json
{"camera":"rearWide","zoom":1.0,"exposureBias":0.0,"autofocus":true,"focusPosition":0.5}
```

`camera` is one of `rearWide`, `rearUltraWide`, `rearTelephoto`, or `front`. The iPhone clamps zoom, exposure bias and manual focus to the selected AVCaptureDevice's supported ranges. Sending complete state instead of deltas makes reconnect behavior deterministic.
