from receiver import preview


class FakeFrame:
    def __init__(self):
        self.formats = []

    def to_ndarray(self, *, format):
        self.formats.append(format)
        return "pixels"


class FakeCV2:
    WND_PROP_VISIBLE = 0

    def __init__(self):
        self.shown = []
        self.keys = []

    def namedWindow(self, title):
        pass

    def imshow(self, title, pixels):
        self.shown.append((title, pixels))

    def waitKey(self, delay):
        self.keys.append(delay)
        return -1

    def destroyWindow(self, title):
        pass


def test_opencv_preview_converts_to_bgr24_and_displays(monkeypatch):
    fake_cv2 = FakeCV2()
    monkeypatch.setattr(preview, "cv2", fake_cv2, raising=False)
    frame = FakeFrame()
    p = preview.OpenCVPreview(title="ICAM test")

    keep_running = p.show(frame)

    assert keep_running is True
    assert frame.formats == ["bgr24"]
    assert fake_cv2.shown == [("ICAM test", "pixels")]
    assert fake_cv2.keys == [1]
