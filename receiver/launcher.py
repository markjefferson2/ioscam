from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import threading
from pathlib import Path
from typing import Iterable

from .control import ControlChannel
from .filters import FilterState, FilterSettings
from .gui import IosCamGUI
from .main import receiver_loop
from .runtime import RuntimeState
from .stats import StreamStats


class ReceiverWorker:
    def __init__(
        self,
        *,
        port: int,
        control: ControlChannel,
        filters: FilterState,
        stats: StreamStats,
        runtime: RuntimeState,
        preview_backend: str = "opencv",
        native_mf: bool = False,
        debug_frames: bool = False,
    ):
        self.port = port
        self.control = control
        self.filters = filters
        self.stats = stats
        self.runtime = runtime
        self.preview_backend = preview_backend
        self.native_mf = native_mf
        self.debug_frames = debug_frames
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._thread_main, name="IosCamReceiver", daemon=True)
        self.thread.start()

    def _thread_main(self) -> None:
        try:
            asyncio.run(
                receiver_loop(
                    port=self.port,
                    control_channel=self.control,
                    filter_state=self.filters,
                    stats=self.stats,
                    runtime_state=self.runtime,
                    preview_backend=self.preview_backend,
                    virtual_camera_enabled=self.native_mf,
                    debug_frames_dir="debug_frames" if self.debug_frames else None,
                )
            )
        except Exception as exc:
            self.runtime.set_status("error", str(exc))


def default_obs_candidates() -> list[Path]:
    candidates: list[Path] = []
    for env_name in ("PROGRAMFILES", "PROGRAMFILES(X86)"):
        base = os.environ.get(env_name)
        if base:
            candidates.append(Path(base) / "obs-studio" / "bin" / "64bit" / "obs64.exe")
    candidates.extend([
        Path(r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"),
        Path(r"C:\Program Files (x86)\obs-studio\bin\64bit\obs64.exe"),
    ])
    return candidates


def find_obs_executable(candidates: Iterable[Path] | None = None) -> Path | None:
    for candidate in candidates or default_obs_candidates():
        path = Path(candidate)
        if path.is_file():
            return path
    return None


def launch_obs() -> bool:
    executable = find_obs_executable()
    if executable is None:
        return False
    subprocess.Popen([str(executable)], cwd=str(executable.parent))
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="IosCam Windows control panel")
    parser.add_argument("--port", type=int, default=2345)
    parser.add_argument("--launch-obs", action="store_true")
    parser.add_argument("--native-mf", action="store_true", help="feed OBS Virtual Camera for the Media Foundation bridge")
    parser.add_argument("--preview-backend", choices=("auto", "pygame", "opencv"), default="auto")
    parser.add_argument("--debug-frames", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    control = ControlChannel()
    filters = FilterState(FilterSettings(rotation=90, show_stats=True))
    stats = StreamStats()
    runtime = RuntimeState()
    worker = ReceiverWorker(
        port=args.port,
        control=control,
        filters=filters,
        stats=stats,
        runtime=runtime,
        preview_backend=args.preview_backend,
        native_mf=args.native_mf,
        debug_frames=args.debug_frames,
    )
    worker.start()

    if args.launch_obs and not args.native_mf:
        launch_obs()

    gui = IosCamGUI(
        control=control,
        filters=filters,
        runtime=runtime,
        stats=stats,
        on_launch_obs=launch_obs,
    )
    gui.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
