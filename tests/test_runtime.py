from receiver.runtime import RuntimeState
from receiver.session import StreamMetadata


def test_runtime_state_tracks_status_and_stream_metadata():
    state = RuntimeState()
    state.set_status("connected", "USB stream active")
    state.set_metadata(StreamMetadata("h264", 1920, 1080, 60, 12_000_000))

    snapshot = state.snapshot()
    assert snapshot.status == "connected"
    assert snapshot.detail == "USB stream active"
    assert snapshot.width == 1920
    assert snapshot.height == 1080
    assert snapshot.fps == 60
    assert snapshot.bitrate == 12_000_000
