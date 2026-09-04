from __future__ import annotations

import asyncio
import json
import socket
from dataclasses import dataclass
from typing import Callable

from .decoder import H264Decoder
from .preview import NullPreview, OpenCVPreview
from .protocol import PacketType, ProtocolError, read_packet
from .queueing import KeyframeAwareVideoQueue, LatestFrameMailbox


class StreamSessionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class StreamMetadata:
    codec: str
    width: int
    height: int
    fps: int
    bitrate: int


def parse_hello_payload(payload: bytes) -> StreamMetadata:
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StreamSessionError("HELLO payload is not valid UTF-8 JSON") from exc

    required = ("codec", "width", "height", "fps", "bitrate")
    missing = [key for key in required if key not in raw]
    if missing:
        raise StreamSessionError(f"HELLO missing fields: {', '.join(missing)}")

    codec = str(raw["codec"]).lower()
    if codec != "h264":
        raise StreamSessionError(f"unsupported codec: {codec}")

    numeric: dict[str, int] = {}
    for name in ("width", "height", "fps", "bitrate"):
        value = raw[name]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise StreamSessionError(f"invalid {name}: {value!r}")
        numeric[name] = value

    return StreamMetadata(codec, numeric["width"], numeric["height"], numeric["fps"], numeric["bitrate"])


class StreamSession:
    def __init__(
        self,
        *,
        preview_enabled: bool = True,
        encoded_queue_size: int = 8,
        decoder_factory: Callable[[], H264Decoder] = H264Decoder,
    ):
        self.preview_enabled = preview_enabled
        self.encoded_queue_size = encoded_queue_size
        self.decoder_factory = decoder_factory

    async def run_socket(self, sock: socket.socket) -> StreamMetadata:
        reader, writer = await asyncio.open_connection(sock=sock)
        try:
            return await self.run_reader(reader)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except (ConnectionError, OSError):
                pass

    async def run_reader(self, reader: asyncio.StreamReader) -> StreamMetadata:
        try:
            first = await read_packet(reader)
        except (asyncio.IncompleteReadError, ProtocolError) as exc:
            raise StreamSessionError(f"failed to read HELLO: {exc}") from exc
        if first.packet_type is not PacketType.HELLO:
            raise StreamSessionError(f"expected HELLO first, got {first.packet_type.name}")

        metadata = parse_hello_payload(first.payload)
        decoder = self.decoder_factory()
        preview = OpenCVPreview() if self.preview_enabled else NullPreview()
        encoded = KeyframeAwareVideoQueue(maxsize=self.encoded_queue_size)
        decoded = LatestFrameMailbox()

        tasks = [
            asyncio.create_task(self._ingest_loop(reader, encoded), name="icam-ingest"),
            asyncio.create_task(self._decode_loop(encoded, decoded, decoder), name="icam-decode"),
        ]
        if self.preview_enabled:
            tasks.append(asyncio.create_task(self._preview_loop(decoded, preview), name="icam-preview"))

        try:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                await task
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            preview.close()

        return metadata

    async def _ingest_loop(self, reader: asyncio.StreamReader, encoded: KeyframeAwareVideoQueue) -> None:
        while True:
            try:
                packet = await read_packet(reader)
            except asyncio.IncompleteReadError:
                return
            except ProtocolError as exc:
                raise StreamSessionError(str(exc)) from exc

            if packet.packet_type is PacketType.VIDEO:
                await encoded.put(packet)
            elif packet.packet_type in (PacketType.STATS, PacketType.PONG):
                continue
            elif packet.packet_type is PacketType.HELLO:
                continue

    async def _decode_loop(self, encoded: KeyframeAwareVideoQueue, decoded: LatestFrameMailbox, decoder: H264Decoder) -> None:
        while True:
            packet = await encoded.get()
            try:
                frames = decoder.decode(packet.payload)
            except Exception as exc:
                raise StreamSessionError(f"H.264 decode failed at sequence {packet.sequence}: {exc}") from exc
            for frame in frames:
                decoded.put(frame)

    async def _preview_loop(self, decoded: LatestFrameMailbox, preview) -> None:
        while True:
            frame = await decoded.get()
            if not preview.show(frame):
                return
