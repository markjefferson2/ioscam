from __future__ import annotations

from dataclasses import dataclass
import time

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None

try:
    import pyvirtualcam  # type: ignore
except ImportError:  # pragma: no cover
    pyvirtualcam = None

from .filters import FilterSettings, FilterState, apply_filters
from .stats import StreamStats


class PreviewUnavailableError(RuntimeError):
    pass


def rotated_dimensions(width: int, height: int, rotation: int) -> tuple[int, int]:
    rotation = int(rotation) % 360
    if rotation not in (0, 90, 180, 270):
        raise ValueError("rotation must be one of 0, 90, 180, 270")
    return (height, width) if rotation in (90, 270) else (width, height)


def rotate_bgr(pixels, rotation: int):
    rotation = int(rotation) % 360
    if rotation == 0:
        return pixels
    if rotation == 90:
        return __import__("numpy").ascontiguousarray(__import__("numpy").rot90(pixels, k=3))
    if rotation == 180:
        return __import__("numpy").ascontiguousarray(__import__("numpy").rot90(pixels, k=2))
    if rotation == 270:
        return __import__("numpy").ascontiguousarray(__import__("numpy").rot90(pixels, k=1))
    raise ValueError("rotation must be one of 0, 90, 180, 270")


@dataclass(slots=True)
class PreviewFrame:
    frame: object
    received_ns: int
    decode_ms: float


class OpenCVPreview:
    def __init__(
        self,
        title: str = "IosCam Preview",
        *,
        filters: FilterState | None = None,
        stats: StreamStats | None = None,
    ):
        if cv2 is None:
            raise PreviewUnavailableError(
                "OpenCV is not installed. Run scripts/setup_windows.ps1 or use --no-preview."
            )
        self.title = title
        self.filters = filters
        self.stats = stats
        self._fullscreen = False
        cv2.namedWindow(self.title)

    def show(self, frame) -> bool:
        if isinstance(frame, PreviewFrame):
            av_frame = frame.frame
            received_ns = frame.received_ns
            decode_ms = frame.decode_ms
        else:
            av_frame = frame
            received_ns = time.perf_counter_ns()
            decode_ms = 0.0

        pixels = av_frame.to_ndarray(format="bgr24")
        settings = self.filters.snapshot() if self.filters is not None else FilterSettings(rotation=0)
        pixels = rotate_bgr(pixels, settings.rotation)
        if self.filters is not None:
            # Rotation is already handled above.
            pixels = apply_filters(pixels, FilterSettings(
                blur=settings.blur,
                brightness=settings.brightness,
                contrast=settings.contrast,
                saturation=settings.saturation,
                sharpness=settings.sharpness,
                mirror=settings.mirror,
                rotation=0,
                show_stats=settings.show_stats,
                fullscreen=settings.fullscreen,
            ))

        now_ns = time.perf_counter_ns()
        if self.stats is not None:
            self.stats.on_presented_frame(received_ns=received_ns, decode_ms=decode_ms, now_ns=now_ns)
            if settings.show_stats:
                self._draw_overlay(pixels, self.stats.snapshot(now_ns=now_ns).overlay_text())

        self._apply_fullscreen(settings.fullscreen)
        cv2.imshow(self.title, pixels)
        key = cv2.waitKey(1) & 0xFF
        return key not in (ord("q"), 27)

    def _draw_overlay(self, pixels, text: str) -> None:
        if cv2 is None or not hasattr(cv2, "putText"):
            return
        font = getattr(cv2, "FONT_HERSHEY_SIMPLEX", 0)
        if hasattr(cv2, "rectangle"):
            cv2.rectangle(pixels, (12, 12), (min(pixels.shape[1] - 12, 980), 54), (0, 0, 0), -1)
        cv2.putText(pixels, text, (24, 42), font, 0.65, (230, 255, 90), 1, getattr(cv2, "LINE_AA", 8))

    def _apply_fullscreen(self, enabled: bool) -> None:
        if cv2 is None or enabled == self._fullscreen or not hasattr(cv2, "setWindowProperty"):
            return
        prop = getattr(cv2, "WND_PROP_FULLSCREEN", 0)
        mode = getattr(cv2, "WINDOW_FULLSCREEN", 1) if enabled else getattr(cv2, "WINDOW_NORMAL", 0)
        cv2.setWindowProperty(self.title, prop, mode)
        self._fullscreen = enabled

    def close(self) -> None:
        if cv2 is not None:
            cv2.destroyWindow(self.title)


class NullPreview:
    def show(self, frame) -> bool:
        return True

    def close(self) -> None:
        return None


class VirtualCameraSink:
    def __init__(self, *, width: int, height: int, fps: int):
        if pyvirtualcam is None:
            raise PreviewUnavailableError("pyvirtualcam is not installed")
        self.camera = pyvirtualcam.Camera(
            width=width,
            height=height,
            fps=fps,
            fmt=pyvirtualcam.PixelFormat.BGR,
        )

    @property
    def device(self) -> str:
        return self.camera.device

    def send(self, pixels) -> None:
        self.camera.send(pixels)

    def close(self) -> None:
        self.camera.close()
