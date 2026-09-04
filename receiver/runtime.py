from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

from .session import StreamMetadata


@dataclass(frozen=True, slots=True)
class RuntimeSnapshot:
    status: str = "idle"
    detail: str = "Ready"
    width: int = 0
    height: int = 0
    fps: int = 0
    bitrate: int = 0


class RuntimeState:
    def __init__(self):
        self._lock = RLock()
        self._status = "idle"
        self._detail = "Ready"
        self._metadata: StreamMetadata | None = None

    def set_status(self, status: str, detail: str = "") -> None:
        with self._lock:
            self._status = status
            self._detail = detail or status

    def set_metadata(self, metadata: StreamMetadata) -> None:
        with self._lock:
            self._metadata = metadata
            self._status = "connected"
            self._detail = "USB stream active"

    def snapshot(self) -> RuntimeSnapshot:
        with self._lock:
            metadata = self._metadata
            return RuntimeSnapshot(
                status=self._status,
                detail=self._detail,
                width=metadata.width if metadata else 0,
                height=metadata.height if metadata else 0,
                fps=metadata.fps if metadata else 0,
                bitrate=metadata.bitrate if metadata else 0,
            )
