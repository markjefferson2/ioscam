from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from .control import ControlChannel
from .filters import FilterState
from .runtime import RuntimeState
from .stats import StreamStats

BG = "#080A08"
PANEL = "#11140F"
PANEL_2 = "#171B13"
ACCENT = "#C8FF2E"
TEXT = "#F4F5F0"
MUTED = "#8C9385"
DANGER = "#FF5A64"

CAMERA_LABELS = {
    "Rear Wide 1×": "rearWide",
    "Rear Ultra Wide 0.5×": "rearUltraWide",
    "Rear Telephoto": "rearTelephoto",
    "Front": "front",
}


class IosCamGUI:
    def __init__(
        self,
        *,
        control: ControlChannel,
        filters: FilterState,
        runtime: RuntimeState,
        stats: StreamStats,
        on_launch_obs=None,
    ):
        self.control = control
        self.filters = filters
        self.runtime = runtime
        self.stats = stats
        self.on_launch_obs = on_launch_obs

        self.root = tk.Tk()
        self.root.title("IosCam Control")
        self.root.geometry("520x860")
        self.root.minsize(480, 720)
        self.root.configure(bg=BG)

        self._brand_icon = None
        icon_path = Path(__file__).resolve().parent.parent / "branding" / "IosCamIcon-1024.png"
        if icon_path.is_file():
            try:
                self._brand_icon = tk.PhotoImage(file=str(icon_path)).subsample(8, 8)
                self.root.iconphoto(True, self._brand_icon)
            except tk.TclError:
                self._brand_icon = None

        self._status_var = tk.StringVar(value="STARTING")
        self._status_detail = tk.StringVar(value="Preparing USB receiver…")
        self._stream_var = tk.StringVar(value="—")
        self._stats_var = tk.StringVar(value="FPS —   |   Mb/s —   |   RX→screen —")

        self._build()
        self.root.after(200, self._poll)

    def run(self) -> None:
        self.root.mainloop()

    def _build(self) -> None:
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True, padx=24, pady=20)

        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x", pady=(0, 18))
        tk.Label(header, text="IosCam", bg=BG, fg=TEXT, font=("Segoe UI", 30, "bold")).pack(side="left")
        tk.Label(header, text="/ BRNDBST STUDIO TOOL", bg=BG, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(side="left", padx=(10, 0), pady=(12, 0))

        status = self._panel(outer)
        status.pack(fill="x", pady=(0, 12))
        line = tk.Frame(status, bg=PANEL)
        line.pack(fill="x", padx=16, pady=(14, 4))
        self.status_dot = tk.Canvas(line, width=12, height=12, bg=PANEL, highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 8))
        self.dot = self.status_dot.create_oval(2, 2, 10, 10, fill=MUTED, outline="")
        tk.Label(line, textvariable=self._status_var, bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Label(status, textvariable=self._status_detail, bg=PANEL, fg=MUTED, anchor="w").pack(fill="x", padx=16)
        tk.Label(status, textvariable=self._stream_var, bg=PANEL, fg=ACCENT, anchor="w", font=("Consolas", 9, "bold")).pack(fill="x", padx=16, pady=(6, 0))
        tk.Label(status, textvariable=self._stats_var, bg=PANEL, fg=MUTED, anchor="w", font=("Consolas", 9)).pack(fill="x", padx=16, pady=(3, 14))

        self._section_title(outer, "SOURCE")
        source = self._panel(outer)
        source.pack(fill="x", pady=(0, 12))
        self.camera_var = tk.StringVar(value="Rear Wide 1×")
        self._dropdown(source, "Camera", self.camera_var, list(CAMERA_LABELS), self._camera_changed)
        self.zoom_var = tk.DoubleVar(value=1.0)
        self._scale(source, "Zoom", self.zoom_var, 1.0, 5.0, 0.1, self._camera_controls_changed, suffix="×")
        self.exposure_var = tk.DoubleVar(value=0.0)
        self._scale(source, "Exposure", self.exposure_var, -2.0, 2.0, 0.1, self._camera_controls_changed)
        self.autofocus_var = tk.BooleanVar(value=True)
        self._check(source, "Autofocus", self.autofocus_var, self._autofocus_changed)
        self.focus_var = tk.DoubleVar(value=0.5)
        self.focus_scale = self._scale(source, "Focus", self.focus_var, 0.0, 1.0, 0.01, self._camera_controls_changed)
        self.focus_scale.configure(state="disabled")

        self._section_title(outer, "IMAGE / WINDOWS")
        image = self._panel(outer)
        image.pack(fill="x", pady=(0, 12))
        self.blur_var = tk.DoubleVar(value=0.0)
        self._scale(image, "Blur", self.blur_var, 0, 20, 1, self._filters_changed)
        self.brightness_var = tk.DoubleVar(value=0.0)
        self._scale(image, "Brightness", self.brightness_var, -60, 60, 1, self._filters_changed)
        self.contrast_var = tk.DoubleVar(value=1.0)
        self._scale(image, "Contrast", self.contrast_var, 0.5, 2.0, 0.05, self._filters_changed)
        self.saturation_var = tk.DoubleVar(value=1.0)
        self._scale(image, "Saturation", self.saturation_var, 0.0, 2.0, 0.05, self._filters_changed)
        self.sharpness_var = tk.DoubleVar(value=0.0)
        self._scale(image, "Sharpness", self.sharpness_var, 0.0, 1.5, 0.05, self._filters_changed)

        self._section_title(outer, "OUTPUT / OBS")
        output = self._panel(outer)
        output.pack(fill="x")
        row = tk.Frame(output, bg=PANEL)
        row.pack(fill="x", padx=14, pady=(12, 4))
        self.mirror_var = tk.BooleanVar(value=False)
        self.stats_var = tk.BooleanVar(value=True)
        self.fullscreen_var = tk.BooleanVar(value=False)
        self._inline_check(row, "Mirror", self.mirror_var, self._filters_changed)
        self._inline_check(row, "Stats", self.stats_var, self._filters_changed)
        self._inline_check(row, "Fullscreen", self.fullscreen_var, self._filters_changed)

        self.rotation_var = tk.StringVar(value="90")
        self._dropdown(output, "Rotation", self.rotation_var, ["0", "90", "180", "270"], self._filters_changed)

        buttons = tk.Frame(output, bg=PANEL)
        buttons.pack(fill="x", padx=14, pady=(8, 14))
        self._button(buttons, "OPEN OBS", self._launch_obs, accent=True).pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._button(buttons, "RESET IMAGE", self._reset_image).pack(side="left", fill="x", expand=True, padx=(6, 0))

        tk.Label(
            outer,
            text="OBS: add Window Capture → ‘IosCam Preview’ → Start Virtual Camera → select ‘OBS Virtual Camera’ in the site.",
            bg=BG,
            fg=MUTED,
            wraplength=460,
            justify="left",
            font=("Segoe UI", 8),
        ).pack(fill="x", pady=(12, 0))

    def _panel(self, parent):
        return tk.Frame(parent, bg=PANEL, highlightbackground="#242A20", highlightthickness=1)

    def _section_title(self, parent, text: str) -> None:
        tk.Label(parent, text=text, bg=BG, fg=ACCENT, font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(3, 6))

    def _dropdown(self, parent, label, var, values, command):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", padx=14, pady=7)
        tk.Label(row, text=label, bg=PANEL, fg=MUTED, width=12, anchor="w").pack(side="left")
        menu = tk.OptionMenu(row, var, *values, command=lambda _=None: command())
        menu.configure(bg=PANEL_2, fg=TEXT, activebackground=ACCENT, activeforeground=BG, bd=0, highlightthickness=0)
        menu["menu"].configure(bg=PANEL_2, fg=TEXT, activebackground=ACCENT, activeforeground=BG)
        menu.pack(side="right", fill="x", expand=True)
        return menu

    def _scale(self, parent, label, var, lo, hi, resolution, command, suffix=""):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", padx=14, pady=5)
        tk.Label(row, text=label, bg=PANEL, fg=MUTED, width=12, anchor="w").pack(side="left")
        value = tk.Label(row, text="", bg=PANEL, fg=TEXT, width=7, anchor="e", font=("Consolas", 9, "bold"))
        value.pack(side="right")

        def changed(raw):
            number = float(raw)
            shown = f"{number:.2f}" if resolution < 0.1 else f"{number:.1f}"
            value.configure(text=shown + suffix)
            command()

        scale = tk.Scale(
            row,
            variable=var,
            from_=lo,
            to=hi,
            resolution=resolution,
            orient="horizontal",
            showvalue=False,
            command=changed,
            bg=PANEL,
            fg=TEXT,
            troughcolor="#2A3025",
            activebackground=ACCENT,
            highlightthickness=0,
            bd=0,
            sliderrelief="flat",
            length=250,
        )
        scale.pack(side="left", fill="x", expand=True)
        initial = float(var.get())
        shown = f"{initial:.2f}" if resolution < 0.1 else f"{initial:.1f}"
        value.configure(text=shown + suffix)
        return scale

    def _check(self, parent, label, var, command):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", padx=14, pady=6)
        tk.Label(row, text=label, bg=PANEL, fg=MUTED, width=12, anchor="w").pack(side="left")
        self._inline_check(row, "ON", var, command).pack(side="right")

    def _inline_check(self, parent, text, var, command):
        check = tk.Checkbutton(
            parent,
            text=text,
            variable=var,
            command=command,
            bg=PANEL,
            fg=TEXT,
            activebackground=PANEL,
            activeforeground=ACCENT,
            selectcolor=PANEL_2,
            highlightthickness=0,
            bd=0,
        )
        check.pack(side="left", padx=(0, 14))
        return check

    def _button(self, parent, text, command, accent=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=ACCENT if accent else PANEL_2,
            fg=BG if accent else TEXT,
            activebackground="#D8FF68" if accent else "#242A20",
            activeforeground=BG if accent else TEXT,
            relief="flat",
            bd=0,
            padx=12,
            pady=10,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )

    def _camera_changed(self) -> None:
        self._camera_controls_changed()

    def _camera_controls_changed(self) -> None:
        self.control.update(
            camera=CAMERA_LABELS[self.camera_var.get()],
            zoom=float(self.zoom_var.get()),
            exposure_bias=float(self.exposure_var.get()),
            autofocus=bool(self.autofocus_var.get()),
            focus_position=float(self.focus_var.get()),
        )

    def _autofocus_changed(self) -> None:
        self.focus_scale.configure(state="disabled" if self.autofocus_var.get() else "normal")
        self._camera_controls_changed()

    def _filters_changed(self) -> None:
        self.filters.update(
            blur=float(self.blur_var.get()),
            brightness=float(self.brightness_var.get()),
            contrast=float(self.contrast_var.get()),
            saturation=float(self.saturation_var.get()),
            sharpness=float(self.sharpness_var.get()),
            mirror=bool(self.mirror_var.get()),
            rotation=int(self.rotation_var.get()),
            show_stats=bool(self.stats_var.get()),
            fullscreen=bool(self.fullscreen_var.get()),
        )

    def _reset_image(self) -> None:
        self.blur_var.set(0.0)
        self.brightness_var.set(0.0)
        self.contrast_var.set(1.0)
        self.saturation_var.set(1.0)
        self.sharpness_var.set(0.0)
        self.mirror_var.set(False)
        self.rotation_var.set("90")
        self._filters_changed()

    def _launch_obs(self) -> None:
        if self.on_launch_obs is not None:
            self.on_launch_obs()

    def _poll(self) -> None:
        runtime = self.runtime.snapshot()
        stat = self.stats.snapshot()
        status = runtime.status.upper()
        self._status_var.set(status)
        self._status_detail.set(runtime.detail)
        if runtime.width:
            self._stream_var.set(f"{runtime.width}×{runtime.height} @ {runtime.fps} fps   H.264")
        else:
            self._stream_var.set("Waiting for stream metadata…")
        self._stats_var.set(
            f"FPS {stat.display_fps:4.1f} / {stat.ingress_fps:4.1f}   |   "
            f"{stat.bitrate_mbps:4.1f} Mb/s   |   Q {stat.queue_depth} / drop {stat.dropped_packets}   |   "
            f"RX→screen {stat.receiver_latency_ms:3.1f} ms"
        )
        color = ACCENT if runtime.status == "connected" else (DANGER if runtime.status == "error" else MUTED)
        self.status_dot.itemconfigure(self.dot, fill=color)
        self.root.after(250, self._poll)
