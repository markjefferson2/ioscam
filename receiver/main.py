from __future__ import annotations

import argparse
import asyncio
import contextlib
import socket
from collections.abc import Awaitable, Callable

from .control import ControlChannel
from .decoder import DecoderUnavailableError
from .filters import FilterSettings, FilterState
from .preview import PreviewUnavailableError
from .runtime import RuntimeState
from .session import StreamMetadata, StreamSession, StreamSessionError
from .stats import StreamStats
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
    control_channel: ControlChannel | None = None,
    filter_state: FilterState | None = None,
    stats: StreamStats | None = None,
    runtime_state: RuntimeState | None = None,
) -> None:
    if stop_event is None:
        stop_event = asyncio.Event()
    stats = stats or StreamStats()

    while not stop_event.is_set():
        sock: socket.socket | None = None
        try:
            if runtime_state:
                runtime_state.set_status("searching", "Searching for USB iPhone…")
            print("[IosCam] Searching for USB iPhone...")
            sock = await connect_fn(port)
            if runtime_state:
                runtime_state.set_status("connecting", f"Opening device TCP :{port}…")
            print(f"[IosCam] USB device connected; opening device TCP :{port}")
            session = session_factory(
                preview_enabled=preview_enabled,
                control_channel=control_channel,
                filter_state=filter_state,
                stats=stats,
                preview_title="IosCam Preview",
                metadata_callback=runtime_state.set_metadata if runtime_state else None,
            )
            metadata = await session.run_socket(sock)
            print(f"[IosCam] Stream ended ({metadata.width}x{metadata.height}@{metadata.fps} {metadata.codec})")
            if runtime_state:
                runtime_state.set_status("reconnecting", "Stream ended; reconnecting…")
        except AppleMobileDeviceSupportError as exc:
            if runtime_state:
                runtime_state.set_status("error", str(exc))
            raise
        except IPhoneNotFoundError as exc:
            if runtime_state:
                runtime_state.set_status("waiting", str(exc))
            print(f"[IosCam] {exc}")
        except UsbTransportError as exc:
            if runtime_state:
                runtime_state.set_status("waiting", str(exc))
            print(f"[IosCam] USB transport: {exc}")
        except StreamSessionError as exc:
            if runtime_state:
                runtime_state.set_status("error", str(exc))
            print(f"[IosCam] Stream error: {exc}")
        except (DecoderUnavailableError, PreviewUnavailableError):
            raise
        except (ConnectionError, OSError, asyncio.IncompleteReadError) as exc:
            if runtime_state:
                runtime_state.set_status("reconnecting", f"Connection lost: {exc}")
            print(f"[IosCam] Connection lost: {exc}")
        finally:
            if sock is not None:
                with contextlib.suppress(OSError):
                    sock.close()

        if not stop_event.is_set():
            await sleep_fn(retry_delay)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Receive IosCam video over USB/usbmux")
    parser.add_argument("--port", type=int, default=2345, help="device TCP port (default: 2345)")
    parser.add_argument("--retry-delay", type=float, default=1.0)
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument("--rotate", type=int, choices=(0, 90, 180, 270), default=90)
    parser.add_argument("--virtual-camera", action="store_true", help="reserved optional direct virtual-camera mode")
    parser.add_argument("--no-overlay", action="store_true")
    return parser


async def async_main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    filters = FilterState(FilterSettings(rotation=args.rotate, show_stats=not args.no_overlay))
    try:
        await receiver_loop(
            port=args.port,
            retry_delay=max(0.0, args.retry_delay),
            preview_enabled=not args.no_preview,
            filter_state=filters,
            control_channel=ControlChannel(),
        )
    except AppleMobileDeviceSupportError as exc:
        print(f"[IosCam] FATAL: {exc}")
        return 2
    except (DecoderUnavailableError, PreviewUnavailableError) as exc:
        print(f"[IosCam] FATAL: {exc}")
        return 3
    return 0


def main() -> int:
    try:
        return asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n[IosCam] Stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
