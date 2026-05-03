import threading

import customtkinter as ctk

from config import AppConfig
from scheduler import run_scheduler


class SchedulerControl(ctk.CTkFrame):
    def __init__(self, parent, on_status_change=None):
        super().__init__(parent, fg_color="transparent")
        self._stop_event: threading.Event | None = None
        self._thread: threading.Thread | None = None
        self._config: AppConfig | None = None
        self.on_status_change = on_status_change
        self._build_ui()

    def _build_ui(self):
        self.status_label = ctk.CTkLabel(
            self, text="状态: 已停止",
            font=ctk.CTkFont(size=14),
            text_color="red",
        )
        self.status_label.pack(side="left", padx=10)

        self.start_btn = ctk.CTkButton(
            self, text="启动", command=self._start,
            fg_color="green", hover_color="darkgreen", width=80,
        )
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ctk.CTkButton(
            self, text="停止", command=self._stop,
            fg_color="red", hover_color="darkred", width=80,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=5)

    def set_config(self, config: AppConfig):
        self._config = config

    def _start(self):
        if self._config is None:
            return
        if self._thread and self._thread.is_alive():
            return

        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=run_scheduler,
            args=(self._config, self._stop_event),
            daemon=True,
        )
        self._thread.start()

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text="状态: 运行中", text_color="green")
        if self.on_status_change:
            self.on_status_change("运行中")

    def _stop(self):
        if self._stop_event:
            self._stop_event.set()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="状态: 已停止", text_color="red")
        if self.on_status_change:
            self.on_status_change("已停止")

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
