import logging
import sys
import queue
from pathlib import Path

import customtkinter as ctk

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import load_config
from logger import setup_logger
from gui.config_editor import ConfigEditorTab
from gui.log_viewer import LogViewerTab
from gui.history_viewer import HistoryViewerTab
from gui.scheduler_control import SchedulerControl
from gui.log_handler import TkinterLogHandler


class AIPenpalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI 笔友 - 自动邮件回复机器人")
        self.geometry("1100x750")
        self.minsize(900, 600)

        ctk.set_default_color_theme("blue")
        ctk.set_appearance_mode("system")

        self.config_path = self._find_config_path()

        self.log_queue: queue.Queue = queue.Queue()
        self._setup_logging()

        self.config = self._load_initial_config()

        self._build_ui()

        self.log_viewer.poll_queue()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _find_config_path(self) -> str:
        candidates = [
            Path(project_root) / "config.yaml",
            Path.cwd() / "config.yaml",
        ]
        for p in candidates:
            if p.exists():
                return str(p)
        return str(Path(project_root) / "config.yaml")

    def _setup_logging(self):
        self.logger = setup_logger("INFO", "ai_penpal.log")

        gui_handler = TkinterLogHandler(self.log_queue)
        gui_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        self.logger.addHandler(gui_handler)

    def _load_initial_config(self):
        try:
            return load_config(self.config_path)
        except Exception:
            self.logger.warning("无法加载配置文件，将使用默认配置")
            return None

    def _build_ui(self):
        control_frame = ctk.CTkFrame(self, height=50)
        control_frame.pack(fill="x", padx=10, pady=(10, 0))

        ctk.CTkLabel(
            control_frame, text="AI 笔友",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", padx=10)

        self.scheduler_control = SchedulerControl(control_frame)
        self.scheduler_control.pack(side="right", padx=10)
        if self.config:
            self.scheduler_control.set_config(self.config)

        ctk.CTkButton(
            control_frame, text="加载配置", width=100,
            command=self._reload_config,
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            control_frame, text="保存配置", width=100,
            command=self._save_config,
        ).pack(side="right", padx=5)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        config_tab = self.tabview.add("配置编辑")
        self.config_editor = ConfigEditorTab(config_tab, self.config_path)
        self.config_editor.pack(fill="both", expand=True)

        log_tab = self.tabview.add("运行日志")
        self.log_viewer = LogViewerTab(log_tab, self.log_queue)
        self.log_viewer.pack(fill="both", expand=True)

        history_tab = self.tabview.add("对话历史")
        db_path = self.config.tracking.db_path if self.config else "replied.db"
        self.history_viewer = HistoryViewerTab(history_tab, db_path)
        self.history_viewer.pack(fill="both", expand=True)

    def _reload_config(self):
        self.config = load_config(self.config_path)
        self.scheduler_control.set_config(self.config)
        self.config_editor._load_config()
        self.config_editor._build_ui()
        self.logger.info("配置已重新加载")

    def _save_config(self):
        self.config_editor._save_config()
        self.logger.info("配置已保存")
        self._reload_config()

    def _on_close(self):
        if self.scheduler_control.is_running:
            self.scheduler_control._stop()
        self.history_viewer.close()
        self.destroy()


def main():
    app = AIPenpalApp()
    app.mainloop()


if __name__ == "__main__":
    main()
