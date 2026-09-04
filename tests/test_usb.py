import asyncio

import pytest

from receiver import usb


class FakeSocket:
    def __init__(self):
        self.blocking = True

    def setblocking(self, value: bool):
        self.blocking = value


class FakeDevice:
    def __init__(self, *, serial: str, is_usb: bool):
        self.serial = serial
        self.is_usb = is_usb
        self.connected_ports: list[int] = []
        self.sock = FakeSocket()

    async def connect(self, port: int):
        self.connected_ports.append(port)
        return self.sock


def test_find_usb_iphone_ignores_network_devices(monkeypatch):
    network = FakeDevice(serial="wifi", is_usb=False)
    cable = FakeDevice(serial="usb", is_usb=True)

    async def fake_list_devices():
        return [network, cable]

    monkeypatch.setattr(usb, "_list_devices", fake_list_devices)

    found = asyncio.run(usb.find_usb_iphone())

    assert found is cable


def test_find_usb_iphone_raises_when_only_network_device_exists(monkeypatch):
    async def fake_list_devices():
        return [FakeDevice(serial="wifi", is_usb=False)]

    monkeypatch.setattr(usb, "_list_devices", fake_list_devices)

    with pytest.raises(usb.IPhoneNotFoundError, match="USB"):
        asyncio.run(usb.find_usb_iphone())


def test_connect_device_port_connects_to_2345_and_sets_nonblocking(monkeypatch):
    cable = FakeDevice(serial="usb", is_usb=True)

    async def fake_find():
        return cable

    monkeypatch.setattr(usb, "find_usb_iphone", fake_find)

    sock = asyncio.run(usb.connect_device_port())

    assert cable.connected_ports == [2345]
    assert sock is cable.sock
    assert sock.blocking is False
