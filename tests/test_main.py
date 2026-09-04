import asyncio

from receiver.main import receiver_loop
from receiver.session import StreamMetadata
from receiver.usb import IPhoneNotFoundError


class FakeSocket:
    def close(self):
        pass


def test_receiver_loop_retries_after_missing_phone_then_runs_session():
    async def scenario():
        attempts = []
        stop_event = asyncio.Event()

        async def fake_connect(port):
            attempts.append(port)
            if len(attempts) == 1:
                raise IPhoneNotFoundError("no USB phone")
            return FakeSocket()

        class FakeSession:
            async def run_socket(self, sock):
                stop_event.set()
                return StreamMetadata("h264", 1920, 1080, 60, 12_000_000)

        async def no_sleep(delay):
            assert delay == 0

        await receiver_loop(
            port=2345,
            retry_delay=0,
            preview_enabled=False,
            stop_event=stop_event,
            connect_fn=fake_connect,
            session_factory=lambda **kwargs: FakeSession(),
            sleep_fn=no_sleep,
        )
        return attempts

    assert asyncio.run(scenario()) == [2345, 2345]


def test_receiver_loop_propagates_missing_apple_support_as_fatal():
    from receiver.usb import AppleMobileDeviceSupportError

    async def scenario():
        async def fake_connect(port):
            raise AppleMobileDeviceSupportError("service missing")

        async def must_not_sleep(delay):
            raise AssertionError("fatal Apple support error must not enter retry sleep")

        with pytest.raises(AppleMobileDeviceSupportError, match="service missing"):
            await receiver_loop(
                port=2345,
                retry_delay=1,
                preview_enabled=False,
                connect_fn=fake_connect,
                sleep_fn=must_not_sleep,
            )

    import pytest
    asyncio.run(scenario())
