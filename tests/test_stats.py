from receiver.stats import StreamStats


def test_stats_reports_one_second_fps_bitrate_and_latency():
    stats = StreamStats(window_seconds=1.0)
    start = 10_000_000_000

    for index in range(60):
        now = start + index * (1_000_000_000 // 60)
        stats.on_video_packet(
            payload_bytes=25_000,
            queue_depth=1,
            dropped_total=2,
            now_ns=now,
        )
        stats.on_presented_frame(
            received_ns=now - 8_000_000,
            decode_ms=2.0,
            now_ns=now,
        )

    snapshot = stats.snapshot(now_ns=start + 1_000_000_000)

    assert 59.0 <= snapshot.ingress_fps <= 60.0
    assert 59.0 <= snapshot.display_fps <= 60.0
    assert 11.8 <= snapshot.bitrate_mbps <= 12.1
    assert snapshot.queue_depth == 1
    assert snapshot.dropped_packets == 2
    assert snapshot.decode_ms == 2.0
    assert snapshot.receiver_latency_ms == 8.0


def test_stats_overlay_is_compact_and_contains_core_metrics():
    stats = StreamStats(window_seconds=1.0)
    stats.on_video_packet(payload_bytes=1000, queue_depth=3, dropped_total=4, now_ns=1_000_000_000)
    stats.on_presented_frame(received_ns=995_000_000, decode_ms=1.5, now_ns=1_000_000_000)

    text = stats.snapshot(now_ns=1_500_000_000).overlay_text()

    assert "FPS" in text
    assert "Mb/s" in text
    assert "Q 3" in text
    assert "drop 4" in text
    assert "rx→screen" in text


def test_stats_can_be_read_while_another_thread_updates():
    import threading

    stats = StreamStats(window_seconds=1.0)
    errors = []

    def writer():
        try:
            for i in range(5000):
                now = 1_000_000_000 + i * 1000
                stats.on_video_packet(payload_bytes=1000, queue_depth=i % 4, dropped_total=0, now_ns=now)
                stats.on_presented_frame(received_ns=now - 1000, decode_ms=1.0, now_ns=now)
        except Exception as exc:  # pragma: no cover - regression guard
            errors.append(exc)

    thread = threading.Thread(target=writer)
    thread.start()
    while thread.is_alive():
        stats.snapshot(now_ns=2_000_000_000)
    thread.join()
    assert errors == []
