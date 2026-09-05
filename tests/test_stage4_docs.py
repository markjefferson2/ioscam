from pathlib import Path


def test_russian_docs_describe_both_obs_and_native_modes():
    text = Path("README_RU.md").read_text(encoding="utf-8")
    assert "start_ioscam_obs.bat" in text
    assert "start_ioscam_native.bat" in text
    assert "OBS2MF (Windows Virtual Camera)" in text


def test_english_docs_describe_both_obs_and_native_modes():
    text = Path("README_EN.md").read_text(encoding="utf-8")
    assert "start_ioscam_obs.bat" in text
    assert "start_ioscam_native.bat" in text
    assert "OBS2MF (Windows Virtual Camera)" in text


def test_third_party_notice_mentions_obs2mf():
    text = Path("THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert "OBS2MF" in text
    assert "mbales-tech/OBS2MF" in text
