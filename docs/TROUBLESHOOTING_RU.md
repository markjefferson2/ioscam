# IosCam — решение проблем

[← README RU](../README_RU.md) · [Установка](INSTALL_RU.md)

## Быстрая диагностика

Выполните по порядку:

```powershell
Get-Service "Apple Mobile Device Service"
Test-NetConnection 127.0.0.1 -Port 27015
C:\ioscam\.venv\Scripts\python.exe -m pymobiledevice3 usbmux list
```

Потом запустите iPhone IosCam → Start Camera и:

```text
C:\ioscam\start_ioscam.bat
```

## `Failed to connect to usbmuxd socket`

Причина: `pymobiledevice3` не может достучаться до Apple usbmux/Apple Mobile Device Service.

Проверьте:

```powershell
Get-Service "Apple Mobile Device Service"
```

Если сервиса нет — установите Apple device support/iTunes. Для совместимости с Sideloadly на Windows удобнее web iTunes + web iCloud со страницы https://sideloadly.io/.

Если сервис остановлен:

```powershell
Start-Service "Apple Mobile Device Service"
```

из PowerShell администратора.

Порт:

```powershell
Test-NetConnection 127.0.0.1 -Port 27015
```

Нужно `TcpTestSucceeded : True`.

## `usbmux list` не видит iPhone

```powershell
C:\ioscam\.venv\Scripts\python.exe -m pymobiledevice3 usbmux list
```

Если список пустой:

- разблокируйте iPhone;
- переподключите кабель;
- нажмите Trust This Computer;
- попробуйте другой USB-порт без хаба;
- проверьте data-capable кабель;
- убедитесь, что iTunes/Apple stack сам видит устройство.

## `H.264 decode failed ... Invalid data found when processing input`

Если это появляется только сразу после подключения и через короткое время видео начинает работать, receiver подключился между H.264 keyframes и синхронизировался на следующем чистом ключевом кадре.

Если ошибка **не проходит**:

1. На iPhone Stop Camera → Start Camera.
2. Закройте и перезапустите `start_ioscam.bat`.
3. Убедитесь, что одновременно нет второго receiver процесса.
4. Не запускайте отдельный `usbmux forward` параллельно с IosCam receiver.
5. Если воспроизводится стабильно — создайте Issue и приложите только очищенный фрагмент ошибки, без device identifiers.

## Preview повёрнут боком

В **IosCam Control** → OUTPUT / OBS → Rotation:

```text
0 / 90 / 180 / 270
```

Для текущей базовой конфигурации default — `90`.

## Камера/объектив не переключается

IosCam требует для выбранной камеры формат **1920×1080 @ 60 fps**.

Возможные причины:

- на модели нет Ultra Wide/Telephoto;
- конкретный объектив не имеет нужного 1080p60 format;
- камера временно недоступна системе.

Вернитесь на **Rear Wide 1×**. Это основной тестовый путь.

## Blur сильно грузит CPU

Blur применяется на Windows. Уменьшите Blur либо выключите его. Sharpness и другие фильтры также добавляют обработку.

Для проверки чистого transport/decode сначала выставьте:

```text
Blur 0
Brightness 0
Contrast 1
Saturation 1
Sharpness 0
```

## FPS не 60

Проверьте отдельно:

- IosCam Control telemetry;
- загрузку CPU/GPU;
- включённые Windows filters;
- OBS Settings → Video → FPS = 60;
- источник Window Capture не должен быть ограничен другим сценарием.

Счётчик `RX→screen` — receiver-side latency, а не полная задержка камера→глаз.

## OBS не видит `IosCam Preview`

1. Сначала запустите IosCam и дождитесь preview.
2. OBS → Source → Window Capture.
3. Выберите **IosCam Preview**.
4. Если окно не появилось в старом source, откройте Properties и выберите его заново.
5. На Windows 11 попробуйте современный Windows Graphics Capture method, если он доступен в OBS.

## В OBS нет кнопки Start Virtual Camera

Используйте актуальный OBS Studio: https://obsproject.com/download

Официальная инструкция/восстановление Virtual Camera: https://obsproject.com/kb/virtual-camera-troubleshooting

## Сайт не видит `OBS Virtual Camera`

1. В OBS нажмите **Start Virtual Camera**.
2. Закройте/обновите вкладку сайта.
3. Проверьте browser camera permissions.
4. В списке камер выберите **OBS Virtual Camera**.
5. Если браузер продолжает держать старый device list — полностью перезапустите браузер.

## `.venv` / pytest / зависимости сломались

Не используйте глобальный `pip` для IosCam.

Можно пересоздать окружение:

```powershell
cd C:\ioscam
Remove-Item -Recurse -Force .venv
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Для тестов:

```powershell
C:\ioscam\.venv\Scripts\python.exe -m pip install -r receiver\requirements-dev.txt
C:\ioscam\.venv\Scripts\python.exe -m pytest -q
```

## `Python 3.12+ x64 was not found`

Поставьте x64 Python 3.12/3.13 с https://www.python.org/downloads/windows/ и повторно запустите BAT.

## Sideloadly не видит iPhone / ошибки Anisette

Проверьте требования текущей версии Sideloadly: https://sideloadly.io/faq

На Windows его официальный сайт рекомендует web iTunes + web iCloud. Устройство должно быть разблокировано и первоначально подключено USB.

## Приложение пишет `Untrusted Developer`

На iPhone:

```text
Settings → General → VPN & Device Management
```

Выберите профиль, затем Trust / Allow & Restart и подтвердите после перезагрузки.

## Приложение перестало запускаться через несколько дней

Для бесплатного Apple ID Sideloadly указывает срок подписи 7 дней. Переподпишите/обновите приложение либо используйте auto-refresh Sideloadly.

## GitHub Actions IPA artifact исчез

Текущий workflow IosCam использует `retention-days: 7`. Если artifact истёк, запустите workflow снова в своём fork через `workflow_dispatch`.

## Безопасность логов

Перед Issue/чатом **не публикуйте**:

- GitHub token / PAT
- Apple ID password
- IMEI
- serial number
- номер телефона
- ICCID / IMSI
- полные `lockdown info`

Команда `pymobiledevice3 lockdown info` выводит много приватных device fields. Для диагностики обычно достаточно `usbmux list`, а оттуда тоже можно скрыть `Identifier/UniqueDeviceID`.
