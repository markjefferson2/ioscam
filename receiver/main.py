from __future__ import annotations

import argparse
import asyncio
import contextlib
import socket
from collections.abc import Awaitable, Callable

from .decoder import DecoderUnavailableError
from .preview import PreviewUnavailableError
from .session import StreamSession, StreamSessionError
from .usb import (
    AppleMobileDeviceSupportError,
    IPhoneNotFoundError,
    UsbTransportError,
    connect_device_port,
)


async def receiver_loop(
    *,
    port: int = 2345,
    retry_delay: float = 1.0,
    preview_enabled: bool = True,
    stop_event: asyncio.Event | None = None,
    connect_fn: Callable[[int], Awaitable[socket.socket]] = connect_device_port,
    session_factory: Callable[..., StreamSession] = StreamSession,
    sleep_fn: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> None:
    """Reconnect forever until stopped.

    `connect_fn`, `session_factory`, and `sleep_fn` are injectable so the
    reconnect policy is testable without a physical iPhone.
    """

    if stop_event is None:
        stop_event = asyncio.Event()

    while not stop_event.is_set():
        sock: socket.socket | None = None
        try:
            print("[IPhoneCam] Searching for USB iPhone...")
            sock = await connect_fn(port)
            print(f"[IPhoneCam] USB device connected; opening device TCP :{port}")
            session = session_factory(preview_enabled=preview_enabled)
            metadata = await session.run_socket(sock)
            print(
                "[IPhoneCam] Stream ended "
                f"({metadata.width}x{metadata.height}@{metadata.fps} {metadata.codec})"
            )
        except AppleMobileDeviceSupportError:
            raise
        except IPhoneNotFoundError as exc:
            print(f"[IPhoneCam] {exc}")
        except UsbTransportError as exc:
            print(f"[IPhoneCam] USB transport: {exc}")
        except StreamSessionError as exc:
            print(f"[IPhoneCam] Stream error: {exc}")
        except (DecoderUnavailableError, PreviewUnavailableError):
            raise
        except (ConnectionError, OSError, asyncio.IncompleteReadError) as exc:
            print(f"[IPhoneCam] Connection lost: {exc}")
        finally:
            if sock is not None:
                with contextlib.suppress(OSError):
                    sock.close()

        if not stop_event.is_set():
            await sleep_fn(retry_delay)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Receive IPhoneCam video over USB/usbmux")
    parser.add_argument("--port", type=int, default=2345, help="device TCP port (default: 2345)")
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=1.0,
        help="seconds between reconnect attempts (default: 1.0)",
    )
    parser.add_argument("--no-preview", action="store_true", help="decode without an OpenCV preview window")
    return parser


async def async_main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        await receiver_loop(
            port=args.port,
            retry_delay=max(0.0, args.retry_delay),
            preview_enabled=not args.no_preview,
        )
    except AppleMobileDeviceSupportError as exc:
        print(f"[IPhoneCam] FATAL: {exc}")
        return 2
    except (DecoderUnavailableError, PreviewUnavailableError) as exc:
        print(f"[IPhoneCam] FATAL: {exc}")
        return 3
    return 0


def main() -> int:
    try:
        return asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n[IPhoneCam] Stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
