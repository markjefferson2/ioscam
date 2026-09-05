from pathlib import Path


def test_hardware_encoder_requirement_is_guarded_for_ios_17_4():
    source = Path("ios/IPhoneCam/Camera/H264Encoder.swift").read_text(encoding="utf-8")

    key = "kVTVideoEncoderSpecification_RequireHardwareAcceleratedVideoEncoder"
    key_index = source.index(key)
    guard_index = source.rfind("if #available(iOS 17.4, *)", 0, key_index)

    assert guard_index != -1
    assert "encoderSpecification = nil" in source[key_index:]


def test_encoder_can_force_next_keyframe_on_pc_connect():
    source = Path("ios/IPhoneCam/Camera/H264Encoder.swift").read_text(encoding="utf-8")
    assert "func requestKeyframe()" in source
    assert "kVTEncodeFrameOptionKey_ForceKeyFrame" in source


def test_stream_connection_requests_immediate_keyframe():
    server = Path("ios/IPhoneCam/Network/StreamServer.swift").read_text(encoding="utf-8")
    model = Path("ios/IPhoneCam/App/CameraStreamerModel.swift").read_text(encoding="utf-8")
    assert "onClientConnected" in server
    assert "encoder.requestKeyframe()" in model


def test_stream_server_does_not_replace_pending_keyframe_with_delta_frame():
    source = Path("ios/IPhoneCam/Network/StreamServer.swift").read_text(encoding="utf-8")
    assert "pendingVideoPacket: (data: Data, isKeyframe: Bool)?" in source
    assert "pendingVideoPacket?.isKeyframe != true" in source
