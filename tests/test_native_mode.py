from pathlib import Path

from receiver.launcher import build_parser


def test_launcher_accepts_native_media_foundation_mode():
    args = build_parser().parse_args(["--native-mf"])
    assert args.native_mf is True


def test_native_launch_and_install_scripts_exist():
    native = Path("start_ioscam_native.bat").read_text(encoding="utf-8")
    install = Path("install_native_camera.bat").read_text(encoding="utf-8")
    assert "--native-mf" in native
    assert "Vcam.Broker.exe" in native
    assert "install_native_camera.ps1" in install


def test_native_bridge_build_workflow_fetches_media_foundation_bridge():
    workflow = Path(".github/workflows/build-native-camera.yml").read_text(encoding="utf-8")
    assert "mbales-tech/OBS2MF" in workflow
    assert "msbuild" in workflow.lower()
    assert "upload-artifact" in workflow


def test_native_installer_can_download_latest_obs2mf_release():
    script = Path("scripts/install_native_camera.ps1").read_text(encoding="utf-8")
    assert "api.github.com/repos/mbales-tech/OBS2MF/releases/latest" in script
    assert "OBS2MF-Setup-" in script
    assert "Invoke-WebRequest" in script


def test_launcher_defaults_to_double_buffered_auto_preview():
    args = build_parser().parse_args([])
    assert args.preview_backend == "auto"
