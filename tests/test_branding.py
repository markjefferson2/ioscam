import json
import plistlib
from pathlib import Path


def test_ios_display_name_is_ioscam():
    data = plistlib.loads(Path("ios/IPhoneCam/Info.plist").read_bytes())
    assert data["CFBundleDisplayName"] == "IosCam"
    assert "IPhoneCam" not in data["NSLocalNetworkUsageDescription"]


def test_app_icon_catalog_contains_marketing_icon():
    path = Path("ios/IPhoneCam/Assets.xcassets/AppIcon.appiconset/Contents.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    images = data["images"]
    assert any(item.get("idiom") == "ios-marketing" and item.get("filename") for item in images)
    for item in images:
        if "filename" in item:
            assert (path.parent / item["filename"]).is_file()


def test_xcode_project_wires_app_icon_asset_catalog():
    source = Path("ios/IPhoneCam/IPhoneCam.xcodeproj/project.pbxproj").read_text(encoding="utf-8")
    assert "Assets.xcassets" in source
    assert "ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon" in source


def test_workflow_uploads_ioscam_named_artifact():
    source = Path(".github/workflows/build-ios.yml").read_text(encoding="utf-8")
    assert "IosCam-unsigned.ipa" in source
    assert "name: IosCam-unsigned" in source


def test_branded_swift_ui_uses_ioscam_and_lime_accent():
    source = Path("ios/IPhoneCam/App/ContentView.swift").read_text(encoding="utf-8")
    assert 'Text("IosCam")' in source
    assert "brandLime" in source


def test_windows_gui_uses_brand_icon_when_available():
    source = Path("receiver/gui.py").read_text(encoding="utf-8")
    assert "IosCamIcon-1024.png" in source
    assert "iconphoto" in source
