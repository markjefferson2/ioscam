from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from threading import RLock


@dataclass(frozen=True, slots=True)
class StatsSnapshot:
    ingress_fps: float = 0.0
    display_fps: float = 0.0
    bitrate_mbps: float = 0.0
    queue_depth: int = 0
    dropped_packets: int = 0
    decode_ms: float = 0.0
    receiver_latency_ms: float = 0.0

    def overlay_text(self) -> str:
        return (
            f"FPS {self.display_fps:4.1f} in {self.ingress_fps:4.1f} | "
            f"{self.bitrate_mbps:4.1f} Mb/s | Q {self.queue_depth} | "
            f"drop {self.dropped_packets} | dec {self.decode_ms:3.1f} ms | "
            f"rx→screen {self.receiver_latency_ms:3.1f} ms"
        )


class StreamStats:
    def __init__(self, window_seconds: float = 1.0):
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self.window_ns = int(window_seconds * 1_000_000_000)
        self._lock = RLock()
        self._video_events: deque[tuple[int, int]] = deque()
        self._display_events: deque[int] = deque()
        self._queue_depth = 0
        self._dropped_packets = 0
        self._decode_ms = 0.0
        self._receiver_latency_ms = 0.0

    def on_video_packet(
        self,
        *,
        payload_bytes: int,
        queue_depth: int,
        dropped_total: int,
        now_ns: int | None = None,
    ) -> None:
        now = time.perf_counter_ns() if now_ns is None else now_ns
        with self._lock:
            self._video_events.append((now, max(0, int(payload_bytes))))
            self._queue_depth = max(0, int(queue_depth))
            self._dropped_packets = max(0, int(dropped_total))
            self._prune(now)

    def on_presented_frame(
        self,
        *,
        received_ns: int,
        decode_ms: float,
        now_ns: int | None = None,
    ) -> None:
        now = time.perf_counter_ns() if now_ns is None else now_ns
        with self._lock:
            self._display_events.append(now)
            self._decode_ms = max(0.0, float(decode_ms))
            self._receiver_latency_ms = max(0.0, (now - received_ns) / 1_000_000)
            self._prune(now)

    def snapshot(self, *, now_ns: int | None = None) -> StatsSnapshot:
        now = time.perf_counter_ns() if now_ns is None else now_ns
        with self._lock:
            self._prune(now)
            window_seconds = self.window_ns / 1_000_000_000
            ingress_fps = len(self._video_events) / window_seconds
            display_fps = len(self._display_events) / window_seconds
            payload_bytes = sum(size for _, size in self._video_events)
            bitrate_mbps = payload_bytes * 8 / self.window_ns * 1000
            return StatsSnapshot(
                ingress_fps=ingress_fps,
                display_fps=display_fps,
                bitrate_mbps=bitrate_mbps,
                queue_depth=self._queue_depth,
                dropped_packets=self._dropped_packets,
                decode_ms=self._decode_ms,
                receiver_latency_ms=self._receiver_latency_ms,
            )

    def _prune(self, now_ns: int) -> None:
        cutoff = now_ns - self.window_ns
        while self._video_events and self._video_events[0][0] < cutoff:
            self._video_events.popleft()
        while self._display_events and self._display_events[0] < cutoff:
            self._display_events.popleft()
