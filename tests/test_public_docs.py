from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "README_RU.md",
    "README_EN.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "THIRD_PARTY_NOTICES.md",
    "SECURITY.md",
    "docs/INSTALL_RU.md",
    "docs/INSTALL_EN.md",
    "docs/TROUBLESHOOTING_RU.md",
    "docs/TROUBLESHOOTING_EN.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/pull_request_template.md",
    "docs/images/ioscam-icon.png",
]


def test_public_docs_exist():
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    assert not missing, f"missing public docs: {missing}"


def test_readmes_cross_link_languages_and_install_guides():
    root = (ROOT / "README.md").read_text(encoding="utf-8")
    ru = (ROOT / "README_RU.md").read_text(encoding="utf-8")
    en = (ROOT / "README_EN.md").read_text(encoding="utf-8")
    assert "README_RU.md" in root and "README_EN.md" in root
    assert "docs/INSTALL_RU.md" in ru and "docs/TROUBLESHOOTING_RU.md" in ru
    assert "docs/INSTALL_EN.md" in en and "docs/TROUBLESHOOTING_EN.md" in en


def test_license_is_mit_for_project_source():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in text
    assert "markjefferson2" in text


def test_docs_warn_about_secrets_and_sensitive_device_logs():
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in [
            "README_RU.md",
            "README_EN.md",
            "docs/TROUBLESHOOTING_RU.md",
            "docs/TROUBLESHOOTING_EN.md",
        ]
    ).lower()
    assert "token" in combined
    assert "imei" in combined
    assert "serial" in combined


def test_install_docs_cover_usb_obs_and_sideloading():
    ru = (ROOT / "docs/INSTALL_RU.md").read_text(encoding="utf-8")
    en = (ROOT / "docs/INSTALL_EN.md").read_text(encoding="utf-8")
    for text in (ru, en):
        assert "pymobiledevice3 usbmux list" in text
        assert "IosCam Preview" in text
        assert "OBS Virtual Camera" in text
        assert "Sideloadly" in text
        assert "Apple Mobile Device Service" in text


def test_ios_workflow_does_not_rebuild_for_docs_only_changes():
    text = (ROOT / ".github/workflows/build-ios.yml").read_text(encoding="utf-8")
    assert 'paths:' in text
    assert 'ios/**' in text
    assert '.github/workflows/build-ios.yml' in text
