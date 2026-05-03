import queue

import customtkinter as ctk


class LogViewerTab(ctk.CTkFrame):
    def __init__(self, parent, log_queue: queue.Queue):
        super().__init__(parent, fg_color="transparent")
        self.log_queue = log_queue
        self.auto_scroll = True
        self._build_ui()

    def _build_ui(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=5, pady=(5, 0))

        ctk.CTkButton(toolbar, text="清空日志", width=80, command=self._clear_log).pack(side="left", padx=5)

        self.auto_scroll_switch = ctk.CTkSwitch(
            toolbar, text="自动滚动", command=self._toggle_auto_scroll
        )
        self.auto_scroll_switch.select()
        self.auto_scroll_switch.pack(side="left", padx=5)

        self.level_filter = ctk.CTkOptionMenu(
            toolbar, width=120,
            values=["全部", "DEBUG", "INFO", "WARNING", "ERROR"],
            command=self._on_level_change,
        )
        self.level_filter.set("全部")
        self.level_filter.pack(side="left", padx=5)

        self.log_text = ctk.CTkTextbox(
            self, state="disabled", wrap="word",
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    def poll_queue(self):
        count = 0
        while count < 50:
            try:
                msg = self.log_queue.get_nowait()
                self._append_log(msg)
                count += 1
            except queue.Empty:
                break
        self.after(100, self.poll_queue)

    def _append_log(self, msg: str):
        if self._should_display(msg):
            self.log_text.configure(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.configure(state="disabled")
            if self.auto_scroll:
                self.log_text.see("end")

    def _should_display(self, msg: str) -> bool:
        level = self.level_filter.get()
        if level == "全部":
            return True
        return f"[{level}]" in msg

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _toggle_auto_scroll(self):
        self.auto_scroll = self.auto_scroll_switch.get() == 1

    def _on_level_change(self, choice):
        pass
