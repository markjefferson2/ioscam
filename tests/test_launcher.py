from pathlib import Path

from receiver.launcher import find_obs_executable


def test_find_obs_executable_returns_first_existing_candidate(tmp_path):
    missing = tmp_path / "missing.exe"
    found = tmp_path / "obs64.exe"
    found.write_bytes(b"")
    assert find_obs_executable([missing, found]) == found


def test_find_obs_executable_returns_none_when_missing(tmp_path):
    assert find_obs_executable([tmp_path / "nope.exe"]) is None
