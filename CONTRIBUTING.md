# Contributing to IosCam / Участие в разработке

Thank you for improving IosCam. Спасибо за вклад в IosCam.

## Before opening an issue / Перед Issue

- Search existing issues first.
- Use the provided Bug report or Feature request template.
- Remove secrets and personal device identifiers from logs.
- Never paste GitHub PAT/token, Apple ID password, IMEI, serial number, phone number, ICCID/IMSI, or raw `pymobiledevice3 lockdown info`.

## Development setup

Windows receiver tests:

```powershell
cd C:\ioscam
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
C:\ioscam\.venv\Scripts\python.exe -m pip install -r receiver\requirements-dev.txt
C:\ioscam\.venv\Scripts\python.exe -m pytest -q
```

The iOS app is under `ios/IPhoneCam/`. GitHub Actions builds an unsigned device IPA with Xcode on macOS.

## Pull requests

1. Keep changes focused.
2. Add/update tests for behavior changes.
3. Run the full Python test suite.
4. If the ICAM wire format changes, update `docs/protocol.md` in the same PR.
5. If setup/user behavior changes, update both RU and EN docs.
6. Do not commit `.venv`, build outputs, signing identities, provisioning profiles, PATs, or Apple credentials.

## Architecture boundaries

- iOS capture: `ios/IPhoneCam/Camera/`
- iOS USB/TCP framing: `ios/IPhoneCam/Network/`
- Windows usbmux: `receiver/usb.py`
- ICAM parser: `receiver/protocol.py`
- H.264 decode: `receiver/decoder.py`
- image filters: `receiver/filters.py`
- GUI: `receiver/gui.py`
- launcher/OBS discovery: `receiver/launcher.py`

Keep transport, codec, filters, and GUI as separate responsibilities.

## Coding style

- Prefer small, testable functions.
- Keep the latency-first behavior: bounded queues should drop stale data rather than accumulate seconds of delay.
- Do not silently add cloud/network video transport to the default runtime path.
- Preserve USB-only behavior unless a new transport is explicitly optional.

## Languages

Public user-facing documentation is maintained in Russian and English. A PR that changes installation or runtime behavior should update both versions.
