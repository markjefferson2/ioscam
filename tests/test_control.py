import json

from receiver.control import CameraSettings, ControlChannel


def test_camera_settings_json_line_uses_expected_wire_schema():
    settings = CameraSettings(
        camera="rearUltraWide",
        zoom=1.5,
        exposure_bias=-0.7,
        autofocus=False,
        focus_position=0.25,
    )
    payload = json.loads(settings.to_json_line().decode("utf-8"))
    assert payload == {
        "camera": "rearUltraWide",
        "zoom": 1.5,
        "exposureBias": -0.7,
        "autofocus": False,
        "focusPosition": 0.25,
    }
    assert settings.to_json_line().endswith(b"\n")


def test_camera_settings_clamp_values_and_reject_bad_camera():
    settings = CameraSettings(zoom=99, exposure_bias=-99, focus_position=2).validated()
    assert settings.zoom == 5.0
    assert settings.exposure_bias == -2.0
    assert settings.focus_position == 1.0

    try:
        CameraSettings(camera="banana").validated()
    except ValueError as exc:
        assert "camera" in str(exc)
    else:
        raise AssertionError("invalid camera should be rejected")


def test_control_channel_tracks_latest_state_and_version():
    channel = ControlChannel()
    version0, state0 = channel.snapshot_versioned()
    assert version0 == 0
    assert state0.camera == "rearWide"

    state1 = channel.update(camera="front", zoom=2.0)
    version1, current = channel.snapshot_versioned()
    assert version1 == 1
    assert state1 == current
    assert current.camera == "front"
    assert current.zoom == 2.0
