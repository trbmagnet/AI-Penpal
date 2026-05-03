import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


def _substitute_env_vars(value: str) -> str:
    pattern = re.compile(r"\$\{(\w+)\}")

    def replacer(match):
        var_name = match.group(1)
        env_value = os.environ.get(var_name)
        if env_value is None:
            raise ValueError(f"Environment variable '{var_name}' is not set")
        return env_value

    return pattern.sub(replacer, value)


def _process_config(obj):
    if isinstance(obj, str):
        return _substitute_env_vars(obj)
    if isinstance(obj, dict):
        return {k: _process_config(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_process_config(item) for item in obj]
    return obj


@dataclass
class CharacterConfig:
    name: str
    personality: str
    background: str = ""
    writing_style: str = ""


@dataclass
class ModelConfig:
    provider: str  # "openai" or "anthropic"
    api_key: str
    model_name: str
    base_url: str | None = None
    max_tokens: int = 1024
    temperature: float = 0.8


@dataclass
class EmailConfig:
    address: str
    imap_server: str
    imap_port: int
    smtp_server: str
    smtp_port: int
    auth_password: str
    use_tls: bool = True


@dataclass
class SchedulerConfig:
    check_interval_minutes: int = 5


@dataclass
class FiltersConfig:
    allowed_senders: list[str] = field(default_factory=list)
    ignore_older_than_minutes: int = 60


@dataclass
class TrackingConfig:
    db_path: str = "replied.db"
    cleanup_days: int = 30


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str | None = None


@dataclass
class HistoryConfig:
    enabled: bool = True
    max_recent_messages: int = 10
    summarize_every_n: int = 5


@dataclass
class AppConfig:
    character: CharacterConfig
    model: ModelConfig
    email: EmailConfig
    scheduler: SchedulerConfig
    filters: FiltersConfig
    tracking: TrackingConfig
    logging: LoggingConfig
    history: HistoryConfig


def load_config(path: str = "config.yaml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    raw = _process_config(raw)

    char_raw = raw.get("character", {})
    model_raw = raw.get("model", {})
    email_raw = raw.get("email", {})
    sched_raw = raw.get("scheduler", {})
    filter_raw = raw.get("filters", {})
    track_raw = raw.get("tracking", {})
    log_raw = raw.get("logging", {})
    hist_raw = raw.get("history", {})

    character = CharacterConfig(
        name=char_raw.get("name", ""),
        personality=char_raw.get("personality", ""),
        background=char_raw.get("background", ""),
        writing_style=char_raw.get("writing_style", ""),
    )

    model = ModelConfig(
        provider=model_raw.get("provider", "openai"),
        api_key=model_raw.get("api_key", ""),
        model_name=model_raw.get("model_name", ""),
        base_url=model_raw.get("base_url"),
        max_tokens=model_raw.get("max_tokens", 1024),
        temperature=model_raw.get("temperature", 0.8),
    )

    email = EmailConfig(
        address=email_raw.get("address", ""),
        imap_server=email_raw.get("imap_server", ""),
        imap_port=email_raw.get("imap_port", 993),
        smtp_server=email_raw.get("smtp_server", ""),
        smtp_port=email_raw.get("smtp_port", 587),
        auth_password=email_raw.get("auth_password", ""),
        use_tls=email_raw.get("use_tls", True),
    )

    scheduler = SchedulerConfig(
        check_interval_minutes=sched_raw.get("check_interval_minutes", 5),
    )

    filters = FiltersConfig(
        allowed_senders=filter_raw.get("allowed_senders", []),
        ignore_older_than_minutes=filter_raw.get("ignore_older_than_minutes", 60),
    )

    tracking = TrackingConfig(
        db_path=track_raw.get("db_path", "replied.db"),
        cleanup_days=track_raw.get("cleanup_days", 30),
    )

    logging_cfg = LoggingConfig(
        level=log_raw.get("level", "INFO"),
        file=log_raw.get("file"),
    )

    history = HistoryConfig(
        enabled=hist_raw.get("enabled", True),
        max_recent_messages=hist_raw.get("max_recent_messages", 10),
        summarize_every_n=hist_raw.get("summarize_every_n", 5),
    )

    return AppConfig(
        character=character,
        model=model,
        email=email,
        scheduler=scheduler,
        filters=filters,
        tracking=tracking,
        logging=logging_cfg,
        history=history,
    )
