import numpy as np

from receiver.filters import FilterSettings, apply_filters


def solid(value: int = 100):
    return np.full((8, 8, 3), value, dtype=np.uint8)


def test_default_filters_leave_pixels_unchanged():
    frame = solid(100)
    result = apply_filters(frame, FilterSettings())
    assert np.array_equal(result, frame)


def test_brightness_and_contrast_are_applied_without_absolute_value_artifacts():
    frame = solid(50)
    result = apply_filters(frame, FilterSettings(brightness=10, contrast=2.0))
    assert result[0, 0].tolist() == [110, 110, 110]


def test_saturation_zero_produces_grayscale_channels():
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    frame[:, :] = [10, 100, 200]
    result = apply_filters(frame, FilterSettings(saturation=0.0))
    b, g, r = [int(v) for v in result[0, 0]]
    assert abs(b - g) <= 1
    assert abs(g - r) <= 1


def test_mirror_flips_horizontally():
    frame = np.array([[[1, 0, 0], [2, 0, 0], [3, 0, 0]]], dtype=np.uint8)
    result = apply_filters(frame, FilterSettings(mirror=True))
    assert result[0, :, 0].tolist() == [3, 2, 1]
