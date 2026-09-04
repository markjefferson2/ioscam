# Security / Безопасность

## Do not publish secrets / Не публикуйте секреты

Never include GitHub PAT/token, Apple ID passwords, signing private keys, provisioning credentials, or raw device dumps in Issues, Pull Requests, commits, screenshots, or chat logs.

Никогда не публикуйте GitHub PAT/token, пароль Apple ID, приватные signing keys, provisioning credentials или полные дампы устройства в Issues, Pull Requests, коммитах, скриншотах и логах.

`pymobiledevice3 lockdown info` can expose IMEI, serial number, phone number, ICCID/IMSI, MAC addresses, UDID, and other identifiers. Prefer `pymobiledevice3 usbmux list` and redact `Identifier/UniqueDeviceID` when those values are not needed.

## If a token was exposed / Если token уже утёк

Revoke it immediately at the provider, create a replacement only if needed, and remove it from Git history if it was committed. Deleting a chat message or editing a README is not a substitute for revoking an exposed credential.

Сразу отзовите token у провайдера, при необходимости создайте новый и удалите секрет из Git history, если он попал в commit. Простого удаления сообщения или правки README недостаточно.

## Runtime privacy

The default IosCam runtime sends the camera stream over the local physical USB/usbmux path between the iPhone and Windows receiver. The receiver code does not require a cloud video relay. External tools used during setup/build/signing (GitHub Actions, Sideloadly, Apple services, package registries) have their own privacy/security policies.
