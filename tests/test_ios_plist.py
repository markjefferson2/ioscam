import plistlib
from pathlib import Path


def test_ios_plist_declares_camera_and_local_network_usage():
    with Path('ios/IPhoneCam/Info.plist').open('rb') as f:
        plist = plistlib.load(f)

    assert plist['NSCameraUsageDescription']
    assert plist['NSLocalNetworkUsageDescription']
