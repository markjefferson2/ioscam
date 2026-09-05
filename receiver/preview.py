from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Protocol

import numpy as np

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None

try:
    import pygame  # type: ignore
except ImportError:  # pragma: no cover
    pygame = None

try:
    import pyvirtualcam  # type: ignore
except ImportError:  # pragma: no cover
    pyvirtualcam = None

from .filters import FilterSettings, FilterState, apply_filters
from .stats import StreamStats


class PreviewUnavailableError(RuntimeError):
    pass


class PixelSink(Protocol):
    def send(self, pixels: np.ndarray) -> None: ...
    def close(self) -> None: ...


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
        return np.ascontiguousarray(np.rot90(pixels, k=3))
    if rotation == 180:
        return np.ascontiguousarray(np.rot90(pixels, k=2))
    if rotation == 270:
        return np.ascontiguousarray(np.rot90(pixels, k=1))
    raise ValueError("rotation must be one of 0, 90, 180, 270")


def normalize_bgr_dimensions(pixels: np.ndarray, *, width: int, height: int) -> np.ndarray:
    """Return exactly the dimensions announced in HELLO.

    Hardware codecs are allowed to expose padded coded heights (1088 is common
    for a 1080-line H.264 picture).  If that padding leaks into the displayed
    ndarray it can show as a bright/garbled strip at the bottom.  Crop pure
    coded padding when the decoded frame is at least the declared size; resize
    only when the decoder actually returned a different/smaller raster.
    """

    if pixels.ndim != 3 or pixels.shape[2] != 3:
        raise ValueError(f"expected BGR HxWx3 frame, got shape {pixels.shape!r}")
    actual_h, actual_w = pixels.shape[:2]
    if actual_w == width and actual_h == height:
        return np.ascontiguousarray(pixels)
    if actual_w >= width and actual_h >= height:
        return np.ascontiguousarray(pixels[:height, :width])
    if cv2 is None:
        raise PreviewUnavailableError("OpenCV is required to resize decoded frames")
    interpolation = cv2.INTER_AREA if actual_w > width or actual_h > height else cv2.INTER_LINEAR
    return np.ascontiguousarray(cv2.resize(pixels, (width, height), interpolation=interpolation))


def fit_bgr_frame(pixels: np.ndarray, *, width: int, height: int) -> np.ndarray:
    """Aspect-fit BGR pixels into an exact canvas, centered with black bars."""

    if pixels.ndim != 3 or pixels.shape[2] != 3:
        raise ValueError(f"expected BGR HxWx3 frame, got shape {pixels.shape!r}")
    source_h, source_w = pixels.shape[:2]
    if source_w <= 0 or source_h <= 0 or width <= 0 or height <= 0:
        raise ValueError("frame dimensions must be positive")
    scale = min(width / source_w, height / source_h)
    out_w = max(1, min(width, int(round(source_w * scale))))
    out_h = max(1, min(height, int(round(source_h * scale))))
    if out_w == source_w and out_h == source_h:
        resized = pixels
    else:
        if cv2 is None:
            raise PreviewUnavailableError("OpenCV is required to scale virtual-camera frames")
        interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        resized = cv2.resize(pixels, (out_w, out_h), interpolation=interpolation)
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    x = (width - out_w) // 2
    y = (height - out_h) // 2
    canvas[y : y + out_h, x : x + out_w] = resized
    return np.ascontiguousarray(canvas)


@dataclass(slots=True)
class PreviewFrame:
    frame: object
    received_ns: int
    decode_ms: float


class FrameDiagnostics:
    def __init__(self, directory: str | Path | None = None):
        self.directory = Path(directory) if directory else None
        self._captured = False

    def capture_once(self, source: np.ndarray, processed: np.ndarray) -> None:
        if self.directory is None or self._captured or cv2 is None:
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(self.directory / "01-decoded-before-filters.png"), source)
        cv2.imwrite(str(self.directory / "02-processed-output.png"), processed)
        (self.directory / "dimensions.txt").write_text(
            f"decoded={source.shape[1]}x{source.shape[0]}\n"
            f"processed={processed.shape[1]}x{processed.shape[0]}\n",
            encoding="utf-8",
        )
        self._captured = True


class _FrameProcessor:
    def __init__(
        self,
        *,
        filters: FilterState | None,
        stats: StreamStats | None,
        expected_width: int | None,
        expected_height: int | None,
        pixel_sink: PixelSink | None,
        diagnostics: FrameDiagnostics | None,
    ):
        self.filters = filters
        self.stats = stats
        self.expected_width = expected_width
        self.expected_height = expected_height
        self.pixel_sink = pixel_sink
        self.diagnostics = diagnostics

    def prepare(self, frame) -> tuple[np.ndarray, FilterSettings, int]:
        if isinstance(frame, PreviewFrame):
            av_frame = frame.frame
            received_ns = frame.received_ns
            decode_ms = frame.decode_ms
        else:
            av_frame = frame
            received_ns = time.perf_counter_ns()
            decode_ms = 0.0

        pixels = av_frame.to_ndarray(format="bgr24")
        if (
            isinstance(pixels, np.ndarray)
            and self.expected_width is not None
            and self.expected_height is not None
        ):
            pixels = normalize_bgr_dimensions(
                pixels,
                width=self.expected_width,
                height=self.expected_height,
            )
        source_pixels = np.ascontiguousarray(pixels) if isinstance(pixels, np.ndarray) else pixels

        settings = self.filters.snapshot() if self.filters is not None else FilterSettings(rotation=0)
        pixels = rotate_bgr(pixels, settings.rotation)
        if self.filters is not None:
            pixels = apply_filters(
                pixels,
                FilterSettings(
                    blur=settings.blur,
                    brightness=settings.brightness,
                    contrast=settings.contrast,
                    saturation=settings.saturation,
                    sharpness=settings.sharpness,
                    mirror=settings.mirror,
                    rotation=0,
                    show_stats=settings.show_stats,
                    fullscreen=settings.fullscreen,
                ),
            )

        if self.pixel_sink is not None:
            self.pixel_sink.send(pixels)

        now_ns = time.perf_counter_ns()
        if self.stats is not None:
            self.stats.on_presented_frame(received_ns=received_ns, decode_ms=decode_ms, now_ns=now_ns)

        if (
            self.diagnostics is not None
            and isinstance(source_pixels, np.ndarray)
            and isinstance(pixels, np.ndarray)
        ):
            self.diagnostics.capture_once(source_pixels, pixels)

        return pixels, settings, now_ns


class OpenCVPreview:
    def __init__(
        self,
        title: str = "IosCam Preview",
        *,
        filters: FilterState | None = None,
        stats: StreamStats | None = None,
        expected_width: int | None = None,
        expected_height: int | None = None,
        pixel_sink: PixelSink | None = None,
        diagnostics: FrameDiagnostics | None = None,
    ):
        if cv2 is None:
            raise PreviewUnavailableError(
                "OpenCV is not installed. Run scripts/setup_windows.ps1 or use --no-preview."
            )
        self.title = title
        self.stats = stats
        self._processor = _FrameProcessor(
            filters=filters,
            stats=stats,
            expected_width=expected_width,
            expected_height=expected_height,
            pixel_sink=pixel_sink,
            diagnostics=diagnostics,
        )
        self._fullscreen = False
        cv2.namedWindow(self.title)

    def show(self, frame) -> bool:
        pixels, settings, now_ns = self._processor.prepare(frame)
        display_pixels = pixels
        if self.stats is not None and settings.show_stats and isinstance(pixels, np.ndarray):
            display_pixels = pixels.copy()
            self._draw_overlay(display_pixels, self.stats.snapshot(now_ns=now_ns).overlay_text())

        self._apply_fullscreen(settings.fullscreen)
        cv2.imshow(self.title, display_pixels)
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


class PygamePreview:
    """Double-buffered preview intended for OBS Window Capture.

    OpenCV's Win32 window can expose a partially-updated backing surface to a
    compositor capture, which looks like a horizontal seam/strip. SDL/pygame's
    double-buffered display commits the whole rendered frame on ``flip``.
    """

    def __init__(
        self,
        title: str = "IosCam Preview",
        *,
        filters: FilterState | None = None,
        stats: StreamStats | None = None,
        expected_width: int | None = None,
        expected_height: int | None = None,
        pixel_sink: PixelSink | None = None,
        diagnostics: FrameDiagnostics | None = None,
    ):
        if pygame is None:
            raise PreviewUnavailableError("pygame is not installed")
        self.title = title
        self.stats = stats
        self._processor = _FrameProcessor(
            filters=filters,
            stats=stats,
            expected_width=expected_width,
            expected_height=expected_height,
            pixel_sink=pixel_sink,
            diagnostics=diagnostics,
        )
        pygame.init()
        pygame.display.set_caption(title)
        rotation = filters.snapshot().rotation if filters is not None else 0
        source_w = expected_width or 1280
        source_h = expected_height or 720
        frame_w, frame_h = rotated_dimensions(source_w, source_h, rotation)
        # Keep a reasonable initial desktop footprint while preserving aspect.
        max_h = 900
        scale = min(1.0, max_h / frame_h)
        initial = (max(320, int(frame_w * scale)), max(240, int(frame_h * scale)))
        flags = getattr(pygame, "RESIZABLE", 0) | getattr(pygame, "DOUBLEBUF", 0)
        self._screen = pygame.display.set_mode(initial, flags)
        self._fullscreen = False

    def show(self, frame) -> bool:
        pixels, settings, now_ns = self._processor.prepare(frame)
        display_pixels = pixels
        if self.stats is not None and settings.show_stats:
            display_pixels = pixels.copy()
            _draw_cv_overlay(display_pixels, self.stats.snapshot(now_ns=now_ns).overlay_text())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                return False

        if settings.fullscreen != self._fullscreen:
            try:
                pygame.display.toggle_fullscreen()
                self._fullscreen = settings.fullscreen
            except Exception:
                self._fullscreen = settings.fullscreen

        rgb = np.ascontiguousarray(display_pixels[:, :, ::-1])
        h, w = rgb.shape[:2]
        surface = pygame.image.frombuffer(rgb.tobytes(), (w, h), "RGB")
        screen_w, screen_h = self._screen.get_size()
        target = _fit_dimensions(w, h, screen_w, screen_h)
        if target != (w, h):
            surface = pygame.transform.smoothscale(surface, target)
        self._screen.fill((0, 0, 0))
        x = (screen_w - target[0]) // 2
        y = (screen_h - target[1]) // 2
        self._screen.blit(surface, (x, y))
        pygame.display.flip()
        return True

    def close(self) -> None:
        if pygame is not None:
            pygame.display.quit()


class NullPreview:
    def __init__(
        self,
        *,
        filters: FilterState | None = None,
        stats: StreamStats | None = None,
        expected_width: int | None = None,
        expected_height: int | None = None,
        pixel_sink: PixelSink | None = None,
        diagnostics: FrameDiagnostics | None = None,
    ):
        self._processor = _FrameProcessor(
            filters=filters,
            stats=stats,
            expected_width=expected_width,
            expected_height=expected_height,
            pixel_sink=pixel_sink,
            diagnostics=diagnostics,
        )

    def show(self, frame) -> bool:
        self._processor.prepare(frame)
        return True

    def close(self) -> None:
        return None


class VirtualCameraSink:
    def __init__(
        self,
        *,
        width: int,
        height: int,
        fps: int,
        backend: str | None = None,
        fit_output: bool = False,
    ):
        if pyvirtualcam is None:
            raise PreviewUnavailableError("pyvirtualcam is not installed")
        self.width = width
        self.height = height
        self.fit_output = fit_output
        kwargs = {
            "width": width,
            "height": height,
            "fps": fps,
            "fmt": pyvirtualcam.PixelFormat.BGR,
        }
        if backend is not None:
            kwargs["backend"] = backend
        self.camera = pyvirtualcam.Camera(**kwargs)

    @property
    def device(self) -> str:
        return self.camera.device

    def send(self, pixels) -> None:
        if self.fit_output:
            pixels = fit_bgr_frame(pixels, width=self.width, height=self.height)
        self.camera.send(np.ascontiguousarray(pixels))

    def close(self) -> None:
        self.camera.close()


def create_preview(
    *,
    title: str,
    backend: str = "auto",
    filters: FilterState | None = None,
    stats: StreamStats | None = None,
    expected_width: int | None = None,
    expected_height: int | None = None,
    pixel_sink: PixelSink | None = None,
    diagnostics: FrameDiagnostics | None = None,
):
    choice = backend.lower()
    kwargs = dict(
        title=title,
        filters=filters,
        stats=stats,
        expected_width=expected_width,
        expected_height=expected_height,
        pixel_sink=pixel_sink,
        diagnostics=diagnostics,
    )
    if choice not in {"auto", "pygame", "opencv"}:
        raise ValueError("preview backend must be auto, pygame, or opencv")
    if choice in {"auto", "pygame"} and pygame is not None:
        return PygamePreview(**kwargs)
    if choice == "pygame":
        raise PreviewUnavailableError("pygame preview requested but pygame is not installed")
    return OpenCVPreview(**kwargs)


def _draw_cv_overlay(pixels: np.ndarray, text: str) -> None:
    if cv2 is None:
        return
    font = getattr(cv2, "FONT_HERSHEY_SIMPLEX", 0)
    cv2.rectangle(pixels, (12, 12), (min(pixels.shape[1] - 12, 980), 54), (0, 0, 0), -1)
    cv2.putText(pixels, text, (24, 42), font, 0.65, (230, 255, 90), 1, getattr(cv2, "LINE_AA", 8))


def _fit_dimensions(source_w: int, source_h: int, target_w: int, target_h: int) -> tuple[int, int]:
    scale = min(target_w / source_w, target_h / source_h)
    return max(1, int(source_w * scale)), max(1, int(source_h * scale))
