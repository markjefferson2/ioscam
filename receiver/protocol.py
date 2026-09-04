from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Protocol

MAGIC = b"ICAM"
VERSION = 1
HEADER_STRUCT = struct.Struct(">4sBBHIQI")
HEADER_SIZE = HEADER_STRUCT.size
MAX_PAYLOAD_LEN = 32 * 1024 * 1024
VIDEO_FLAG_KEYFRAME = 0x0001


class ProtocolError(ValueError):
    pass


class PacketType(IntEnum):
    HELLO = 0x01
    VIDEO = 0x02
    STATS = 0x03
    PING = 0x04
    PONG = 0x05


@dataclass(frozen=True, slots=True)
class PacketHeader:
    packet_type: PacketType
    flags: int
    payload_len: int
    timestamp_ns: int
    sequence: int


@dataclass(frozen=True, slots=True)
class Packet:
    packet_type: PacketType
    flags: int
    timestamp_ns: int
    sequence: int
    payload: bytes


class AsyncExactReader(Protocol):
    async def readexactly(self, size: int) -> bytes: ...


def decode_header(data: bytes) -> PacketHeader:
    if len(data) != HEADER_SIZE:
        raise ProtocolError(f"header must be {HEADER_SIZE} bytes, got {len(data)}")
    magic, version, packet_type_raw, flags, payload_len, timestamp_ns, sequence = HEADER_STRUCT.unpack(data)
    if magic != MAGIC:
        raise ProtocolError(f"invalid magic: {magic!r}")
    if version != VERSION:
        raise ProtocolError(f"unsupported version: {version}")
    if payload_len > MAX_PAYLOAD_LEN:
        raise ProtocolError(f"payload too large: {payload_len} > {MAX_PAYLOAD_LEN}")
    try:
        packet_type = PacketType(packet_type_raw)
    except ValueError as exc:
        raise ProtocolError(f"unknown packet type: {packet_type_raw}") from exc
    return PacketHeader(packet_type, flags, payload_len, timestamp_ns, sequence)


def encode_packet(packet: Packet) -> bytes:
    payload_len = len(packet.payload)
    if payload_len > MAX_PAYLOAD_LEN:
        raise ProtocolError(f"payload too large: {payload_len} > {MAX_PAYLOAD_LEN}")
    header = HEADER_STRUCT.pack(
        MAGIC,
        VERSION,
        int(packet.packet_type),
        packet.flags,
        payload_len,
        packet.timestamp_ns,
        packet.sequence,
    )
    return header + packet.payload


async def read_packet(reader: AsyncExactReader) -> Packet:
    header_bytes = await reader.readexactly(HEADER_SIZE)
    header = decode_header(header_bytes)
    payload = await reader.readexactly(header.payload_len) if header.payload_len else b""
    return Packet(
        packet_type=header.packet_type,
        flags=header.flags,
        timestamp_ns=header.timestamp_ns,
        sequence=header.sequence,
        payload=payload,
    )
