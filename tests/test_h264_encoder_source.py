from pathlib import Path


def test_hardware_encoder_requirement_is_guarded_for_ios_17_4():
    source = Path("ios/IPhoneCam/Camera/H264Encoder.swift").read_text(encoding="utf-8")

    key = "kVTVideoEncoderSpecification_RequireHardwareAcceleratedVideoEncoder"
    key_index = source.index(key)
    guard_index = source.rfind("if #available(iOS 17.4, *)", 0, key_index)

    assert guard_index != -1
    assert "encoderSpecification = nil" in source[key_index:]
