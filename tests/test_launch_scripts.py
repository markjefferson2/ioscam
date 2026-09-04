from pathlib import Path


def test_main_batch_uses_venv_python_without_activation():
    text = Path("start_ioscam.bat").read_text(encoding="utf-8")
    assert ".venv\\Scripts\\python.exe" in text
    assert "receiver.launcher" in text
    assert "--launch-obs" in text
    assert "Activate.ps1" not in text
    assert "setup_windows.ps1" in text


def test_obs_batch_enables_launch_obs_mode():
    text = Path("start_ioscam_obs.bat").read_text(encoding="utf-8")
    assert "start_ioscam.bat" in text
    assert "--launch-obs" in text


def test_preview_has_stable_obs_window_title():
    text = Path("receiver/preview.py").read_text(encoding="utf-8")
    assert '"IosCam Preview"' in text
