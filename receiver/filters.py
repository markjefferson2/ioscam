from __future__ import annotations

from dataclasses import dataclass, replace
from threading import RLock

import cv2  # type: ignore
import numpy as np


@dataclass(frozen=True, slots=True)
class FilterSettings:
    blur: float = 0.0
    brightness: float = 0.0
    contrast: float = 1.0
    saturation: float = 1.0
    sharpness: float = 0.0
    mirror: bool = False
    rotation: int = 90
    show_stats: bool = True
    fullscreen: bool = False

    def validated(self) -> "FilterSettings":
        rotation = int(self.rotation) % 360
        if rotation not in (0, 90, 180, 270):
            raise ValueError("rotation must be one of 0, 90, 180, 270")
        return FilterSettings(
            blur=max(0.0, min(float(self.blur), 30.0)),
            brightness=max(-100.0, min(float(self.brightness), 100.0)),
            contrast=max(0.25, min(float(self.contrast), 3.0)),
            saturation=max(0.0, min(float(self.saturation), 3.0)),
            sharpness=max(0.0, min(float(self.sharpness), 3.0)),
            mirror=bool(self.mirror),
            rotation=rotation,
            show_stats=bool(self.show_stats),
            fullscreen=bool(self.fullscreen),
        )


class FilterState:
    def __init__(self, initial: FilterSettings | None = None):
        self._lock = RLock()
        self._settings = (initial or FilterSettings()).validated()

    def snapshot(self) -> FilterSettings:
        with self._lock:
            return self._settings

    def update(self, **changes) -> FilterSettings:
        with self._lock:
            self._settings = replace(self._settings, **changes).validated()
            return self._settings


def apply_filters(pixels: np.ndarray, settings: FilterSettings) -> np.ndarray:
    cfg = settings.validated()
    out = np.ascontiguousarray(pixels)

    if cfg.mirror:
        out = cv2.flip(out, 1)

    if cfg.contrast != 1.0 or cfg.brightness != 0.0:
        work = out.astype(np.float32) * cfg.contrast + cfg.brightness
        out = np.clip(work, 0, 255).astype(np.uint8)

    if cfg.saturation != 1.0:
        hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] *= cfg.saturation
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    if cfg.blur > 0.0:
        height, width = out.shape[:2]
        scale = 0.25 if min(width, height) >= 720 else 0.5
        small = cv2.resize(out, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        radius = max(1, int(round(cfg.blur)))
        kernel = radius * 2 + 1
        if kernel % 2 == 0:
            kernel += 1
        small = cv2.GaussianBlur(small, (kernel, kernel), 0)
        out = cv2.resize(small, (width, height), interpolation=cv2.INTER_LINEAR)

    if cfg.sharpness > 0.0:
        softened = cv2.GaussianBlur(out, (0, 0), 1.0)
        out = cv2.addWeighted(out, 1.0 + cfg.sharpness, softened, -cfg.sharpness, 0)

    return np.ascontiguousarray(out)
