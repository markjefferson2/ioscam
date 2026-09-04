import asyncio

from receiver.protocol import Packet, PacketType, VIDEO_FLAG_KEYFRAME
from receiver.queueing import KeyframeAwareVideoQueue, LatestFrameMailbox


def video(sequence: int, *, keyframe: bool = False) -> Packet:
    return Packet(
        packet_type=PacketType.VIDEO,
        flags=VIDEO_FLAG_KEYFRAME if keyframe else 0,
        timestamp_ns=sequence,
        sequence=sequence,
        payload=f"frame-{sequence}".encode(),
    )


def test_video_queue_preserves_fifo_without_overload():
    async def scenario():
        queue = KeyframeAwareVideoQueue(maxsize=3)
        await queue.put(video(1, keyframe=True))
        await queue.put(video(2))
        return (await queue.get()).sequence, (await queue.get()).sequence

    assert asyncio.run(scenario()) == (1, 2)


def test_overflow_drops_to_live_edge_and_waits_for_keyframe():
    async def scenario():
        queue = KeyframeAwareVideoQueue(maxsize=2)
        await queue.put(video(1, keyframe=True))
        await queue.put(video(2))
        accepted_overflow = await queue.put(video(3))
        accepted_non_key = await queue.put(video(4))
        accepted_key = await queue.put(video(5, keyframe=True))
        packet = await asyncio.wait_for(queue.get(), timeout=0.1)
        return accepted_overflow, accepted_non_key, accepted_key, packet.sequence, queue.recovering

    assert asyncio.run(scenario()) == (False, False, True, 5, False)


def test_latest_frame_mailbox_replaces_unconsumed_frame():
    async def scenario():
        mailbox = LatestFrameMailbox()
        mailbox.put("old")
        mailbox.put("new")
        return await asyncio.wait_for(mailbox.get(), timeout=0.1)

    assert asyncio.run(scenario()) == "new"
