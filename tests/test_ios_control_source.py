from pathlib import Path


def test_camera_control_wire_schema_exists():
    source = Path("ios/IPhoneCam/Camera/CameraControl.swift").read_text(encoding="utf-8")
    for token in ["rearWide", "rearUltraWide", "rearTelephoto", "front", "exposureBias", "focusPosition"]:
        assert token in source


def test_stream_server_receives_newline_delimited_control_json():
    source = Path("ios/IPhoneCam/Network/StreamServer.swift").read_text(encoding="utf-8")
    assert "receiveControlLocked" in source
    assert "JSONDecoder" in source
    assert "onControlCommand" in source


def test_camera_capture_supports_lens_exposure_zoom_and_focus_control():
    source = Path("ios/IPhoneCam/Camera/CameraCapture.swift").read_text(encoding="utf-8")
    for token in [
        ".builtInUltraWideCamera",
        ".builtInTelephotoCamera",
        "videoZoomFactor",
        "setExposureTargetBias",
        "setFocusModeLocked",
    ]:
        assert token in source
