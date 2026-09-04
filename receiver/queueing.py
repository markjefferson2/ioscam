from __future__ import annotations

import asyncio
from typing import Generic, TypeVar

from .protocol import Packet, VIDEO_FLAG_KEYFRAME

T = TypeVar("T")


class KeyframeAwareVideoQueue:
    """Bounded encoded-video queue that recovers at the next keyframe.

    Dropping arbitrary P-frames would poison the decoder reference chain, so an
    overflow clears the queue and discards packets until the next IDR/keyframe.
    """

    def __init__(self, maxsize: int = 8):
        if maxsize < 1:
            raise ValueError("maxsize must be >= 1")
        self._queue: asyncio.Queue[Packet] = asyncio.Queue(maxsize=maxsize)
        self._recovering = False
        self._dropped_total = 0

    @property
    def recovering(self) -> bool:
        return self._recovering

    @property
    def qsize(self) -> int:
        return self._queue.qsize()

    @property
    def dropped_total(self) -> int:
        return self._dropped_total

    async def put(self, packet: Packet) -> bool:
        is_keyframe = bool(packet.flags & VIDEO_FLAG_KEYFRAME)

        if self._recovering:
            if not is_keyframe:
                self._dropped_total += 1
                return False
            self._recovering = False
            self._queue.put_nowait(packet)
            return True

        if self._queue.full():
            dropped = self._drain()
            self._dropped_total += dropped + 1
            self._recovering = True
            if not is_keyframe:
                return False
            self._recovering = False
            self._queue.put_nowait(packet)
            return True

        self._queue.put_nowait(packet)
        return True

    async def get(self) -> Packet:
        return await self._queue.get()

    def _drain(self) -> int:
        count = 0
        while True:
            try:
                self._queue.get_nowait()
                count += 1
            except asyncio.QueueEmpty:
                return count


class LatestFrameMailbox(Generic[T]):
    """A one-slot mailbox: producer always replaces an unconsumed old frame."""

    def __init__(self):
        self._queue: asyncio.Queue[T] = asyncio.Queue(maxsize=1)

    def put(self, item: T) -> None:
        if self._queue.full():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        self._queue.put_nowait(item)

    async def get(self) -> T:
        return await self._queue.get()
