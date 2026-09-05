from __future__ import annotations

from typing import Any, Callable, Protocol

try:
    import av  # type: ignore
except ImportError:  # pragma: no cover - exercised via monkeypatch too
    av = None


class DecoderUnavailableError(RuntimeError):
    pass


class DecoderLike(Protocol):
    def decode(self, access_unit: bytes) -> list[Any]: ...


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


class ResilientH264Decoder:
    """Decoder guard that only enters the H.264 reference chain at a keyframe.

    A newly connected receiver can land between IDRs. Feeding those P-frames to
    a fresh FFmpeg decoder creates noisy ``Invalid data found`` errors and, in
    the old implementation, caused a reconnect loop.  This wrapper waits for a
    keyframe and returns to that state after any decoder error.
    """

    def __init__(self, factory: Callable[[], DecoderLike] = H264Decoder):
        self._factory = factory
        self._decoder: DecoderLike | None = None
        self._synced = False
        self._recoveries = 0
        self._last_error: Exception | None = None

    @property
    def synced(self) -> bool:
        return self._synced

    @property
    def recoveries(self) -> int:
        return self._recoveries

    @property
    def last_error(self) -> Exception | None:
        return self._last_error

    def decode(self, access_unit: bytes, *, is_keyframe: bool) -> list[Any]:
        if not access_unit:
            return []

        if not self._synced:
            if not is_keyframe:
                return []
            self._decoder = self._factory()

        assert self._decoder is not None
        try:
            frames = self._decoder.decode(access_unit)
        except Exception as exc:  # PyAV raises multiple FFmpeg-derived types.
            self._last_error = exc
            self._recoveries += 1
            self._decoder = None
            self._synced = False
            return []

        # A keyframe access unit includes SPS/PPS in our iOS protocol.  Once it
        # decodes successfully, subsequent delta frames are safe to feed.
        if is_keyframe:
            self._synced = True
            self._last_error = None
        return frames
