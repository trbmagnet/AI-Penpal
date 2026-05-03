from pathlib import Path

import customtkinter as ctk
import yaml

from gui.widgets import (create_labeled_entry, create_labeled_textbox,
                          create_labeled_switch, create_labeled_optionmenu)


SECTION_DEFS = {
    "character": {
        "label": "角色设定",
        "fields": [
            ("name", "name", "角色名称", "entry"),
            ("personality", "personality", "性格特点", "textbox"),
            ("background", "background", "背景设定", "textbox"),
            ("writing_style", "writing_style", "写作风格", "textbox"),
        ],
    },
    "model": {
        "label": "AI 模型",
        "fields": [
            ("provider", "provider", "AI 提供商", "optionmenu", ["openai", "anthropic"]),
            ("api_key", "api_key", "API 密钥", "entry_secret"),
            ("base_url", "base_url", "自定义端点 (可选)", "entry"),
            ("model_name", "model_name", "模型名称", "entry"),
            ("max_tokens", "max_tokens", "最大回复长度", "entry"),
            ("temperature", "temperature", "创造力 (0.0-2.0)", "entry"),
        ],
    },
    "email": {
        "label": "邮箱设置",
        "fields": [
            ("address", "address", "邮箱地址", "entry"),
            ("imap_server", "imap_server", "IMAP 服务器", "entry"),
            ("imap_port", "imap_port", "IMAP 端口", "entry"),
            ("smtp_server", "smtp_server", "SMTP 服务器", "entry"),
            ("smtp_port", "smtp_port", "SMTP 端口", "entry"),
            ("auth_password", "auth_password", "邮箱密码/应用密码", "entry_secret"),
            ("use_tls", "use_tls", "使用 TLS", "switch"),
        ],
    },
    "scheduler": {
        "label": "调度器",
        "fields": [
            ("check_interval_minutes", "check_interval_minutes", "检查间隔 (分钟)", "entry"),
        ],
    },
    "filters": {
        "label": "过滤规则",
        "fields": [
            ("allowed_senders", "allowed_senders", "允许的发件人 (每行一个)", "textbox_list"),
            ("ignore_older_than_minutes", "ignore_older_than_minutes", "忽略超过 N 分钟的邮件", "entry"),
        ],
    },
    "tracking": {
        "label": "数据追踪",
        "fields": [
            ("db_path", "db_path", "数据库路径", "entry"),
            ("cleanup_days", "cleanup_days", "清理天数", "entry"),
        ],
    },
    "history": {
        "label": "对话历史",
        "fields": [
            ("enabled", "enabled", "启用对话记忆", "switch"),
            ("max_recent_messages", "max_recent_messages", "保留最近消息数", "entry"),
            ("summarize_every_n", "summarize_every_n", "每 N 次对话总结一次", "entry"),
        ],
    },
    "logging": {
        "label": "日志",
        "fields": [
            ("level", "level", "日志级别", "optionmenu", ["DEBUG", "INFO", "WARNING", "ERROR"]),
            ("file", "file", "日志文件路径", "entry"),
        ],
    },
}


class ConfigEditorTab(ctk.CTkFrame):
    def __init__(self, parent, config_path: str):
        super().__init__(parent, fg_color="transparent")
        self.config_path = config_path
        self.fields: dict[str, dict[str, ctk.CTkBaseClass]] = {}
        self.raw_config: dict = {}
        self._load_config()
        self._build_ui()

    def _load_config(self):
        p = Path(self.config_path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                self.raw_config = yaml.safe_load(f) or {}
        else:
            example = Path(__file__).resolve().parent.parent / "config.example.yaml"
            if example.exists():
                with open(example, "r", encoding="utf-8") as f:
                    self.raw_config = yaml.safe_load(f) or {}
            else:
                self.raw_config = {}

    def _build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=5, pady=5)

        for section_key, section_def in SECTION_DEFS.items():
            tab = self.tabview.add(section_def["label"])
            self.fields[section_key] = {}
            self._populate_section(tab, section_key, section_def["fields"])

    def _populate_section(self, parent, section_key: str, field_defs: list):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        section_data = self.raw_config.get(section_key, {})

        for field_def in field_defs:
            yaml_key = field_def[0]
            field_name = field_def[1]
            label = field_def[2]
            widget_type = field_def[3]

            raw_value = section_data.get(field_name, "")
            if raw_value is None:
                raw_value = ""

            if widget_type == "entry":
                widget = create_labeled_entry(scroll, label, str(raw_value))
                self.fields[section_key][field_name] = widget
            elif widget_type == "entry_secret":
                widget = create_labeled_entry(scroll, label, str(raw_value), show="*")
                self.fields[section_key][field_name] = widget
            elif widget_type == "textbox":
                widget = create_labeled_textbox(scroll, label, str(raw_value))
                self.fields[section_key][field_name] = widget
            elif widget_type == "textbox_list":
                if isinstance(raw_value, list):
                    raw_value = "\n".join(raw_value)
                widget = create_labeled_textbox(scroll, label, str(raw_value))
                self.fields[section_key][field_name] = widget
            elif widget_type == "switch":
                widget = create_labeled_switch(scroll, label, bool(raw_value))
                self.fields[section_key][field_name] = widget
            elif widget_type == "optionmenu":
                options = field_def[4]
                widget = create_labeled_optionmenu(
                    scroll, label, options, default=str(raw_value) if raw_value else options[0]
                )
                self.fields[section_key][field_name] = widget

    def _get_widget_value(self, widget, widget_type: str):
        if widget_type in ("entry", "entry_secret"):
            return widget.get()
        elif widget_type == "textbox" or widget_type == "textbox_list":
            return widget.get("1.0", "end-1c")
        elif widget_type == "switch":
            return widget.get() == 1
        elif widget_type == "optionmenu":
            return widget.get()
        return ""

    def _save_config(self):
        for section_key, section_def in SECTION_DEFS.items():
            if section_key not in self.raw_config:
                self.raw_config[section_key] = {}

            for field_def in section_def["fields"]:
                field_name = field_def[1]
                widget_type = field_def[3]
                widget = self.fields.get(section_key, {}).get(field_name)
                if widget is None:
                    continue

                value = self._get_widget_value(widget, widget_type)

                if widget_type == "textbox_list":
                    lines = [line.strip() for line in value.split("\n") if line.strip()]
                    self.raw_config[section_key][field_name] = lines
                elif widget_type == "entry" and field_name in ("imap_port", "smtp_port", "max_tokens",
                                                                "check_interval_minutes", "cleanup_days",
                                                                "max_recent_messages", "summarize_every_n",
                                                                "ignore_older_than_minutes"):
                    try:
                        self.raw_config[section_key][field_name] = int(value)
                    except (ValueError, TypeError):
                        self.raw_config[section_key][field_name] = value
                elif widget_type == "entry" and field_name == "temperature":
                    try:
                        self.raw_config[section_key][field_name] = float(value)
                    except (ValueError, TypeError):
                        self.raw_config[section_key][field_name] = value
                elif widget_type == "switch":
                    self.raw_config[section_key][field_name] = bool(value)
                else:
                    self.raw_config[section_key][field_name] = value

        config_path = Path(self.config_path)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.raw_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
