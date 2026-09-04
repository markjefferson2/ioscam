from __future__ import annotations

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None


class PreviewUnavailableError(RuntimeError):
    pass


class OpenCVPreview:
    def __init__(self, title: str = "iPhone USB Webcam"):
        if cv2 is None:
            raise PreviewUnavailableError(
                "OpenCV is not installed. Run scripts/setup_windows.ps1 or use --no-preview."
            )
        self.title = title
        cv2.namedWindow(self.title)

    def show(self, frame) -> bool:
        pixels = frame.to_ndarray(format="bgr24")
        cv2.imshow(self.title, pixels)
        key = cv2.waitKey(1) & 0xFF
        return key not in (ord("q"), 27)

    def close(self) -> None:
        if cv2 is not None:
            cv2.destroyWindow(self.title)


class NullPreview:
    def show(self, frame) -> bool:
        return True

    def close(self) -> None:
        return None
