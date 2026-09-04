from __future__ import annotations

import json
from dataclasses import dataclass, replace
from threading import RLock

CAMERAS = ("rearWide", "rearUltraWide", "rearTelephoto", "front")


@dataclass(frozen=True, slots=True)
class CameraSettings:
    camera: str = "rearWide"
    zoom: float = 1.0
    exposure_bias: float = 0.0
    autofocus: bool = True
    focus_position: float = 0.5

    def validated(self) -> "CameraSettings":
        if self.camera not in CAMERAS:
            raise ValueError(f"camera must be one of {', '.join(CAMERAS)}")
        return CameraSettings(
            camera=self.camera,
            zoom=max(1.0, min(float(self.zoom), 5.0)),
            exposure_bias=max(-2.0, min(float(self.exposure_bias), 2.0)),
            autofocus=bool(self.autofocus),
            focus_position=max(0.0, min(float(self.focus_position), 1.0)),
        )

    def to_json_line(self) -> bytes:
        cfg = self.validated()
        payload = {
            "camera": cfg.camera,
            "zoom": cfg.zoom,
            "exposureBias": cfg.exposure_bias,
            "autofocus": cfg.autofocus,
            "focusPosition": cfg.focus_position,
        }
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"


class ControlChannel:
    """Thread-safe latest-value control state.

    The GUI updates this object from the Tk thread. The asyncio stream task
    polls a monotonically increasing version and sends only when state changes.
    """

    def __init__(self, initial: CameraSettings | None = None):
        self._lock = RLock()
        self._state = (initial or CameraSettings()).validated()
        self._version = 0

    def update(self, **changes) -> CameraSettings:
        with self._lock:
            self._state = replace(self._state, **changes).validated()
            self._version += 1
            return self._state

    def snapshot(self) -> CameraSettings:
        with self._lock:
            return self._state

    def snapshot_versioned(self) -> tuple[int, CameraSettings]:
        with self._lock:
            return self._version, self._state
