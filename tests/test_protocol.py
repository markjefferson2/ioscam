import asyncio
import struct

import pytest

from receiver.protocol import (
    HEADER_SIZE,
    MAX_PAYLOAD_LEN,
    Packet,
    PacketType,
    ProtocolError,
    decode_header,
    encode_packet,
    read_packet,
)


def test_round_trip_header_and_payload():
    packet = Packet(
        packet_type=PacketType.VIDEO,
        flags=1,
        timestamp_ns=123456789,
        sequence=42,
        payload=b"abc",
    )

    wire = encode_packet(packet)
    header = decode_header(wire[:HEADER_SIZE])

    assert HEADER_SIZE == 24
    assert header.packet_type is PacketType.VIDEO
    assert header.flags == 1
    assert header.payload_len == 3
    assert header.timestamp_ns == 123456789
    assert header.sequence == 42
    assert wire[HEADER_SIZE:] == b"abc"


def test_header_is_big_endian():
    packet = Packet(PacketType.VIDEO, 0x1234, 0x0102030405060708, 0x11223344, b"x")
    wire = encode_packet(packet)

    assert wire[:4] == b"ICAM"
    assert wire[4] == 1
    assert wire[5] == int(PacketType.VIDEO)
    assert wire[6:8] == b"\x12\x34"
    assert wire[8:12] == b"\x00\x00\x00\x01"
    assert wire[12:20] == bytes.fromhex("0102030405060708")
    assert wire[20:24] == bytes.fromhex("11223344")


def test_invalid_magic_is_rejected():
    raw = bytearray(encode_packet(Packet(PacketType.HELLO, 0, 0, 0, b""))[:HEADER_SIZE])
    raw[:4] = b"NOPE"

    with pytest.raises(ProtocolError, match="magic"):
        decode_header(bytes(raw))


def test_invalid_version_is_rejected():
    raw = bytearray(encode_packet(Packet(PacketType.HELLO, 0, 0, 0, b""))[:HEADER_SIZE])
    raw[4] = 9

    with pytest.raises(ProtocolError, match="version"):
        decode_header(bytes(raw))


def test_absurd_payload_length_is_rejected_before_allocation():
    raw = struct.pack(
        ">4sBBHIQI",
        b"ICAM",
        1,
        int(PacketType.VIDEO),
        0,
        MAX_PAYLOAD_LEN + 1,
        0,
        0,
    )

    with pytest.raises(ProtocolError, match="payload"):
        decode_header(raw)


class ChunkedReader:
    def __init__(self, data: bytes, chunks: list[int]):
        self._data = bytearray(data)
        self._chunks = iter(chunks)

    async def readexactly(self, size: int) -> bytes:
        out = bytearray()
        while len(out) < size:
            if not self._data:
                raise asyncio.IncompleteReadError(bytes(out), size)
            try:
                chunk_size = next(self._chunks)
            except StopIteration:
                chunk_size = size - len(out)
            take = min(chunk_size, size - len(out), len(self._data))
            out += self._data[:take]
            del self._data[:take]
            await asyncio.sleep(0)
        return bytes(out)


def test_read_packet_handles_partial_tcp_reads():
    expected = Packet(PacketType.VIDEO, 1, 900, 7, b"abcdef")
    reader = ChunkedReader(encode_packet(expected), [1, 2, 3, 1, 4, 2, 1, 8])

    actual = asyncio.run(read_packet(reader))

    assert actual == expected
