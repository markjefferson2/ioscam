import pytest

from receiver import decoder


def test_decoder_reports_missing_pyav(monkeypatch):
    monkeypatch.setattr(decoder, "av", None, raising=False)

    with pytest.raises(decoder.DecoderUnavailableError, match="PyAV"):
        decoder.H264Decoder()


def test_decoder_decodes_generated_h264_when_pyav_is_available():
    av = pytest.importorskip("av")
    import numpy as np

    encoder = av.CodecContext.create("libx264", "w")
    encoder.width = 64
    encoder.height = 48
    encoder.pix_fmt = "yuv420p"
    encoder.time_base = av.time_base

    access_units = []
    frame = av.VideoFrame.from_ndarray(np.zeros((48, 64, 3), dtype=np.uint8), format="bgr24")
    for packet in encoder.encode(frame):
        access_units.append(bytes(packet))
    for packet in encoder.encode(None):
        access_units.append(bytes(packet))

    h264 = decoder.H264Decoder()
    decoded = []
    for packet in access_units:
        decoded.extend(h264.decode(packet))
    decoded.extend(h264.flush())

    assert decoded
    assert decoded[0].width == 64
    assert decoded[0].height == 48
