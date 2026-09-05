import numpy as np

from receiver.preview import fit_bgr_frame, normalize_bgr_dimensions


def test_normalize_crops_decoder_padding_to_declared_size():
    frame = np.zeros((1088, 1920, 3), dtype=np.uint8)
    frame[1080:, :, :] = 255

    normalized = normalize_bgr_dimensions(frame, width=1920, height=1080)

    assert normalized.shape == (1080, 1920, 3)
    assert normalized.max() == 0
    assert normalized.flags.c_contiguous


def test_normalize_resizes_when_frame_is_smaller_than_declared_size():
    frame = np.zeros((540, 960, 3), dtype=np.uint8)
    normalized = normalize_bgr_dimensions(frame, width=1920, height=1080)
    assert normalized.shape == (1080, 1920, 3)


def test_fit_frame_letterboxes_portrait_into_native_720p_canvas():
    portrait = np.full((1920, 1080, 3), 127, dtype=np.uint8)
    fitted = fit_bgr_frame(portrait, width=1280, height=720)

    assert fitted.shape == (720, 1280, 3)
    assert fitted.flags.c_contiguous
    # Portrait content is centered, leaving black side bars.
    assert fitted[:, 0].max() == 0
    assert fitted[:, -1].max() == 0
    assert fitted[:, 640].mean() > 0
