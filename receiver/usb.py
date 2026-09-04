from __future__ import annotations

import socket
from typing import Any, Awaitable, Callable


class UsbTransportError(RuntimeError):
    pass


class AppleMobileDeviceSupportError(UsbTransportError):
    pass


class IPhoneNotFoundError(UsbTransportError):
    pass


async def _default_list_devices() -> list[Any]:
    try:
        from pymobiledevice3.usbmux import list_devices
    except ImportError as exc:
        raise AppleMobileDeviceSupportError(
            "pymobiledevice3 is not installed; run scripts/setup_windows.ps1"
        ) from exc

    try:
        return await list_devices()
    except Exception as exc:
        raise AppleMobileDeviceSupportError(
            "Cannot reach Apple Mobile Device Service/usbmux. Install Apple Devices or iTunes support and ensure the Apple Mobile Device Service is running."
        ) from exc


_list_devices: Callable[[], Awaitable[list[Any]]] = _default_list_devices


async def find_usb_iphone() -> Any:
    devices = await _list_devices()
    for device in devices:
        if bool(getattr(device, "is_usb", False)):
            return device
    raise IPhoneNotFoundError(
        "No iPhone connected over USB. Unlock it, tap Trust, and reconnect the cable."
    )


async def connect_device_port(port: int = 2345) -> socket.socket:
    device = await find_usb_iphone()
    try:
        sock = await device.connect(port)
    except Exception as exc:
        raise UsbTransportError(
            f"USB iPhone found, but device TCP port {port} is not reachable. Start streaming in IPhoneCam first."
        ) from exc
    sock.setblocking(False)
    return sock
