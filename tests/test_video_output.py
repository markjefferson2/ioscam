import numpy as np
import pytest

from receiver import preview


def test_rotated_dimensions_swap_for_quarter_turns():
    assert preview.rotated_dimensions(1920, 1080, 0) == (1920, 1080)
    assert preview.rotated_dimensions(1920, 1080, 90) == (1080, 1920)
    assert preview.rotated_dimensions(1920, 1080, 180) == (1920, 1080)
    assert preview.rotated_dimensions(1920, 1080, 270) == (1080, 1920)


def test_rotate_bgr_90_clockwise():
    pixels = np.array(
        [
            [[1, 0, 0], [2, 0, 0], [3, 0, 0]],
            [[4, 0, 0], [5, 0, 0], [6, 0, 0]],
        ],
        dtype=np.uint8,
    )

    rotated = preview.rotate_bgr(pixels, 90)

    assert rotated[:, :, 0].tolist() == [[4, 1], [5, 2], [6, 3]]
    assert rotated.flags.c_contiguous


def test_invalid_rotation_is_rejected():
    with pytest.raises(ValueError, match="rotation"):
        preview.rotated_dimensions(1920, 1080, 45)


class FakeCamera:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.sent = []
        self.closed = False
        self.device = "OBS Virtual Camera"

    def send(self, pixels):
        self.sent.append(pixels.copy())

    def close(self):
        self.closed = True


class FakePyVirtualCam:
    class PixelFormat:
        BGR = "BGR"

    def __init__(self):
        self.created = []

    def Camera(self, **kwargs):
        camera = FakeCamera(**kwargs)
        self.created.append(camera)
        return camera


def test_virtual_camera_sink_uses_bgr_and_stream_dimensions(monkeypatch):
    fake_module = FakePyVirtualCam()
    monkeypatch.setattr(preview, "pyvirtualcam", fake_module, raising=False)
    sink = preview.VirtualCameraSink(width=1080, height=1920, fps=60)
    pixels = np.zeros((1920, 1080, 3), dtype=np.uint8)

    sink.send(pixels)
    sink.close()

    camera = fake_module.created[0]
    assert camera.kwargs == {
        "width": 1080,
        "height": 1920,
        "fps": 60,
        "fmt": "BGR",
    }
    assert len(camera.sent) == 1
    assert camera.closed is True
