# Установка IosCam с нуля — Windows + iPhone + OBS

[← README RU](../README_RU.md) · [Troubleshooting](TROUBLESHOOTING_RU.md)

Ниже — путь от чистого Windows до камеры **OBS Virtual Camera**.

## 0. Что понадобится

- Windows 10/11 x64; основная тестовая система — Windows 11
- Python 3.12 или 3.13 x64: https://www.python.org/downloads/windows/
- Git for Windows, если используете `git clone`: https://git-scm.com/download/win
- iPhone с iOS 17+; проверено на iPhone 12 Pro / iOS 26.6.1
- USB/Lightning кабель с data lines
- Apple Mobile Device Service
- Sideloadly: https://sideloadly.io/
- OBS Studio: https://obsproject.com/download
- бесплатный Apple ID подходит

### Важный момент про iTunes/iCloud на Windows

Для IosCam нужен Apple Mobile Device Service. `pymobiledevice3` на Windows использует Apple usbmux/Apple Mobile Device Service. Для Sideloadly на Windows официальный сайт Sideloadly рекомендует **web version of iTunes & iCloud**, а не Store-версии. Самый простой совместимый вариант — использовать ссылки Web iTunes / Web iCloud со страницы https://sideloadly.io/.

Если `Apple Mobile Device Service` уже есть и запускается, переустанавливать Apple stack без причины не надо.

## 1. Получить исходники

### Вариант A — Git

```powershell
cd C:\
git clone https://github.com/markjefferson2/ioscam.git
cd C:\ioscam
```

Если папка уже существует:

```powershell
cd C:\ioscam
git pull
```

### Вариант B — Download ZIP

GitHub → Code → Download ZIP → распаковать проект в:

```text
C:\ioscam
```

## 2. Подготовить Windows receiver

Самый простой способ:

```text
C:\ioscam\start_ioscam.bat
```

При первом запуске BAT вызывает `scripts/setup_windows.ps1`, создаёт:

```text
C:\ioscam\.venv
```

и ставит `pymobiledevice3`, `av`, `opencv-python`.

Можно запустить setup вручную:

```powershell
cd C:\ioscam
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Не ставьте зависимости в глобальный Python проекта — `.venv` изолирует IosCam от aiogram/ботов/других Python-проектов.

## 3. Проверить Apple Mobile Device Service

```powershell
Get-Service "Apple Mobile Device Service"
```

Ожидается `Running`.

Если сервис есть, но остановлен, из PowerShell администратора:

```powershell
Start-Service "Apple Mobile Device Service"
```

Можно проверить usbmux loopback endpoint:

```powershell
Test-NetConnection 127.0.0.1 -Port 27015
```

Ожидается:

```text
TcpTestSucceeded : True
```

## 4. Подключить и доверить iPhone

1. Подключите iPhone кабелем.
2. Разблокируйте экран.
3. Нажмите **Trust / Доверять этому компьютеру**, если iPhone спрашивает.
4. Проверьте USB:

```powershell
C:\ioscam\.venv\Scripts\python.exe -m pymobiledevice3 usbmux list
```

Пример нужного результата:

```json
{
  "ConnectionType": "USB",
  "DeviceClass": "iPhone"
}
```

**Не публикуйте полный `lockdown info`: он может содержать IMEI/serial/номер телефона.**

## 5. Получить unsigned IPA

Workflow находится в:

```text
.github/workflows/build-ios.yml
```

Он собирает iOS app на macOS runner через Xcode и пакует:

```text
IosCam-unsigned.ipa
```

### Если в основном репозитории есть свежий artifact

1. Откройте https://github.com/markjefferson2/ioscam/actions
2. Откройте последний зелёный **Build unsigned iOS IPA**.
3. В секции **Artifacts** скачайте **IosCam-unsigned**.
4. Распакуйте ZIP — внутри `.ipa`.

Текущий workflow хранит artifact 7 дней.

### Если artifact истёк

1. Fork репозитория в свой GitHub.
2. Откройте вкладку Actions и разрешите workflows, если GitHub попросит.
3. Выберите **Build unsigned iOS IPA**.
4. Run workflow.
5. Скачайте artifact после зелёной сборки.

GitHub Actions используется только как бесплатная macOS/Xcode build machine. Не добавляйте Apple ID, PAT, сертификаты или private keys в repository secrets для этой unsigned-сборки.

## 6. Подписать и установить IPA через Sideloadly

Скачайте: https://sideloadly.io/

На Windows Sideloadly официально рекомендует web-версии iTunes и iCloud; ссылки есть внизу его официальной страницы.

1. Запустите Sideloadly.
2. Подключите iPhone USB.
3. Перетащите `IosCam-unsigned.ipa`.
4. Выберите iPhone.
5. Введите свой Apple ID.
6. Нажмите Start.

С бесплатным Apple ID sideloaded app обычно действителен 7 дней. Sideloadly также имеет auto-refresh.

## 7. Доверие приложению и Developer Mode

Если iPhone показывает **Untrusted Developer / Недоверенный разработчик**:

```text
Settings / Настройки
→ General / Основные
→ VPN & Device Management / VPN и управление устройством
→ профиль разработчика
→ Trust / Allow & Restart
```

На новых версиях iOS может потребоваться перезапуск.

Если iPhone требует Developer Mode:

```text
Settings
→ Privacy & Security
→ Developer Mode
→ On
```

После перезагрузки подтвердите включение. В обычной ежедневной работе Developer Mode не нужно включать заново, пока вы сами его не выключите.

## 8. Запустить IosCam

На iPhone:

1. Откройте **IosCam**.
2. Разрешите Camera permission.
3. Нажмите **Start Camera**.
4. Оставьте приложение в foreground.

На Windows:

```text
C:\ioscam\start_ioscam.bat
```

Откроются:

- **IosCam Control** — настройки
- **IosCam Preview** — видео
- OBS также запускается автоматически, если найден в стандартной папке

## 9. Настроить OBS один раз

1. OBS → Sources → `+` → **Window Capture**.
2. Название, например `IosCam`.
3. Window → **IosCam Preview**.
4. При необходимости Transform → Fit to screen.
5. Settings → Video:

```text
Base Canvas:        1920x1080
Output Resolution:  1920x1080
FPS:                60
```

6. Controls → **Start Virtual Camera**.
7. В браузере/Discord/чат-сайте выберите **OBS Virtual Camera**.

Если браузер был открыт до запуска virtual camera, обновите страницу или перезапустите браузер.

## 10. Ежедневное использование

```text
1. USB подключён
2. iPhone разблокирован
3. IosCam → Start Camera
4. C:\ioscam\start_ioscam.bat
5. OBS → Start Virtual Camera
6. сайт → OBS Virtual Camera
```

## Проверка тестов для разработчиков

```powershell
cd C:\ioscam
C:\ioscam\.venv\Scripts\python.exe -m pip install -r receiver\requirements-dev.txt
C:\ioscam\.venv\Scripts\python.exe -m pytest -q
```

Следующий документ: [TROUBLESHOOTING_RU.md](TROUBLESHOOTING_RU.md).
