# IosCam — русская документация

[← Главная](README.md) · [English](README_EN.md) · [Полная установка](docs/INSTALL_RU.md) · [Решение проблем](docs/TROUBLESHOOTING_RU.md)

**IosCam** превращает iPhone в проводную 1080p60-камеру для Windows без Camo Pro, DroidCam и передачи видео по Wi-Fi.

```text
iPhone
  ↓  AVCaptureSession 1920×1080 @ 60
VideoToolbox H.264
  ↓
Lightning / USB + Apple usbmux
  ↓
IosCam на Windows
  ↓
IosCam Preview
  ↓
OBS Window Capture
  ↓
OBS Virtual Camera
  ↓
браузер / Discord / чат-рулетка / видеосвязь
```

## Что умеет

### Управление камерой iPhone с Windows

- Rear Wide 1×
- Rear Ultra Wide 0.5×
- Rear Telephoto
- Front
- Zoom 1–5× с ограничением реального диапазона устройства
- Exposure bias
- Autofocus on/off
- Manual focus position

Если конкретного объектива нет на модели iPhone либо он не имеет режима 1920×1080@60, приложение вернёт ошибку — это ограничение железа/формата камеры.

### Обработка на Windows

- Blur
- Brightness
- Contrast
- Saturation
- Sharpness
- Mirror
- Rotation 0/90/180/270
- Stats overlay
- Fullscreen preview

Размытие сейчас применяется ко всему кадру. AI background blur/segmentation пока не реализован.

## Быстрый ежедневный запуск

После однократной установки:

1. Подключите iPhone data-кабелем и разблокируйте его.
2. На iPhone откройте **IosCam** → **Start Camera**.
3. На Windows запустите:

```text
C:\ioscam\start_ioscam_obs.bat
```

Для обычного preview без автозапуска OBS используйте `start_ioscam.bat`. BAT сам использует `.venv`, проверяет зависимости и запускает панель IosCam.

4. В OBS один раз создайте **Window Capture** для окна **`IosCam Preview`**.
5. Нажмите **Start Virtual Camera**.
6. На сайте или в приложении выберите **OBS Virtual Camera**.

## Что нужно

- Windows x64; проект тестировался на Windows 11
- Python 3.12+ x64
- iPhone с iOS 17+; проверено на iPhone 12 Pro / iOS 26.6.1
- data-capable USB/Lightning кабель
- Apple Mobile Device Service (ставится вместе с iTunes/Apple device support)
- Sideloadly для установки unsigned IPA
- OBS Studio для виртуальной камеры

Подробно: **[docs/INSTALL_RU.md](docs/INSTALL_RU.md)**.

## Как работает USB

IosCam не отправляет видеопоток на сервер. На iPhone приложение слушает TCP-порт `2345`, а Windows подключается к этому порту через Apple usbmux по физическому USB. На Windows `pymobiledevice3` использует Apple Mobile Device Service. Для Apple Windows stack usbmux доступен через loopback `127.0.0.1:27015`.

Проверка устройства:

```powershell
C:\ioscam\.venv\Scripts\python.exe -m pymobiledevice3 usbmux list
```

В списке должен быть iPhone с `ConnectionType: USB`.

## Сборка IPA бесплатно

В репозитории есть `.github/workflows/build-ios.yml`. Workflow собирает **unsigned** `IosCam-unsigned.ipa` на macOS/Xcode runner без Apple signing secrets.

Если в Actions есть свежий зелёный build, скачайте artifact **IosCam-unsigned**. Если artifact истёк — форкните репозиторий, включите Actions и вручную запустите **Build unsigned iOS IPA**.

Unsigned IPA затем подписывается вашим Apple ID локально через Sideloadly. Бесплатный Apple ID обычно даёт 7-дневную подпись; Sideloadly также предлагает auto-refresh.

## Два режима вывода на Windows

### 1. OBS mode — основной и самый гибкий

Запуск:

```text
C:\ioscam\start_ioscam_obs.bat
```

IosCam использует двойную буферизацию preview, поэтому OBS Window Capture не должен ловить горизонтальный tearing/seam. Поток: `IosCam Preview → OBS → OBS Virtual Camera`.

### 2. Native Media Foundation compatibility mode — Windows 11

Один раз запустите от обычного пользователя:

```text
C:\ioscam\install_native_camera.bat
```

Скрипт ищет локальный `OBS2MF-Setup-*.exe`, а если его нет — скачивает последний релиз `mbales-tech/OBS2MF` с GitHub и запускает installer с UAC. После установки ежедневный запуск:

```text
C:\ioscam\start_ioscam_native.bat
```

В этом режиме OBS Studio UI открывать не нужно. IosCam напрямую пишет обработанные кадры в установленный OBS Virtual Camera driver через `pyvirtualcam`, а OBS2MF публикует их через Windows 11 `MFCreateVirtualCamera`. В браузере камера отображается как **`OBS2MF (Windows Virtual Camera)`**. Это всё равно виртуальная камера и она не маскируется под физическое устройство.

## OBS

В IosCam должен быть виден нормальный поток в окне **`IosCam Preview`**.

В OBS:

1. Sources → `+` → **Window Capture**.
2. Window → **IosCam Preview**.
3. Settings → Video → при необходимости выставьте 1920×1080 / 60 FPS.
4. Controls → **Start Virtual Camera**.
5. В браузере выберите **OBS Virtual Camera**.

Официальный гайд OBS: https://obsproject.com/kb/virtual-camera-guide

## Приватность и секреты

**Никогда не коммитьте и не публикуйте:**

- GitHub Personal Access Token / token
- пароль Apple ID
- signing certificates / private keys
- полный вывод `pymobiledevice3 lockdown info`

`lockdown info` может содержать **IMEI, serial number, номер телефона, ICCID/IMSI, MAC-адреса и другие идентификаторы**. Перед публикацией логов удаляйте такие данные.

Если token случайно попал в чат, issue, commit или screenshot — отзовите его и создайте новый.

## Тесты

```powershell
C:\ioscam\.venv\Scripts\python.exe -m pip install -r receiver\requirements-dev.txt
C:\ioscam\.venv\Scripts\python.exe -m pytest -q
```

## Ограничения / roadmap

Сейчас:

- 1080p60 H.264
- без аудио
- без 4K60
- есть дополнительный Windows 11 Media Foundation compatibility mode
- OBS mode остаётся основным editable pipeline; native mode использует OBS camera driver как локальный frame handoff, без OBS Studio UI
- full-frame blur вместо AI background blur

Логичные следующие шаги: 4K60/HEVC, background segmentation, audio и собственный IosCam Media Foundation source без промежуточного OBS camera driver.

## Помощь

Сначала: **[docs/TROUBLESHOOTING_RU.md](docs/TROUBLESHOOTING_RU.md)**.

Если создаёте GitHub Issue, не публикуйте IMEI/serial/телефон/token. Приложите версию Windows, iPhone/iOS, команду/ошибку и укажите, видит ли `pymobiledevice3 usbmux list` устройство по USB.

## Лицензия

Исходный код IosCam — [MIT](LICENSE). Сторонние зависимости не перелицензируются проектом: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
