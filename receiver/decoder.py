from __future__ import annotations

from typing import Any

try:
    import av  # type: ignore
except ImportError:  # pragma: no cover - exercised via monkeypatch too
    av = None


class DecoderUnavailableError(RuntimeError):
    pass


class H264Decoder:
    def __init__(self):
        if av is None:
            raise DecoderUnavailableError(
                "PyAV is not installed. Run scripts/setup_windows.ps1 or pip install av."
            )
        self._codec = av.CodecContext.create("h264", "r")

    def decode(self, access_unit: bytes) -> list[Any]:
        if not access_unit:
            return []
        packet = av.Packet(access_unit)
        return list(self._codec.decode(packet))

    def flush(self) -> list[Any]:
        return list(self._codec.decode(None))
