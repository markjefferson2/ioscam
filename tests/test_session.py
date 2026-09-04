import json

import pytest

from receiver.session import StreamMetadata, StreamSessionError, parse_hello_payload


def test_parse_hello_payload_accepts_expected_h264_stream():
    payload = json.dumps({
        "codec": "h264",
        "width": 1920,
        "height": 1080,
        "fps": 60,
        "bitrate": 12_000_000,
    }).encode()

    assert parse_hello_payload(payload) == StreamMetadata(
        codec="h264",
        width=1920,
        height=1080,
        fps=60,
        bitrate=12_000_000,
    )


def test_parse_hello_payload_rejects_wrong_codec():
    payload = json.dumps({
        "codec": "hevc",
        "width": 1920,
        "height": 1080,
        "fps": 60,
        "bitrate": 12_000_000,
    }).encode()

    with pytest.raises(StreamSessionError, match="codec"):
        parse_hello_payload(payload)


def test_parse_hello_payload_rejects_invalid_dimensions():
    payload = json.dumps({
        "codec": "h264",
        "width": 0,
        "height": 1080,
        "fps": 60,
        "bitrate": 12_000_000,
    }).encode()

    with pytest.raises(StreamSessionError, match="width"):
        parse_hello_payload(payload)
