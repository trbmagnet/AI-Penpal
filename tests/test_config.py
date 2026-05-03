import os
import tempfile
from pathlib import Path

import pytest
import yaml

from config import load_config, _substitute_env_vars


def test_load_valid_config(tmp_path):
    config_data = {
        "character": {"name": "Test", "personality": "Friendly"},
        "model": {"provider": "openai", "api_key": "sk-test", "model_name": "gpt-4o"},
        "email": {
            "address": "test@example.com",
            "imap_server": "imap.example.com",
            "imap_port": 993,
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "auth_password": "pass",
        },
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")

    config = load_config(str(config_file))
    assert config.character.name == "Test"
    assert config.model.provider == "openai"
    assert config.email.address == "test@example.com"


def test_env_var_substitution():
    os.environ["TEST_API_KEY"] = "sk-env-test"
    result = _substitute_env_vars("key=${TEST_API_KEY}")
    assert result == "key=sk-env-test"
    del os.environ["TEST_API_KEY"]


def test_env_var_missing():
    with pytest.raises(ValueError, match="not set"):
        _substitute_env_vars("${NONEXISTENT_VAR_12345}")


def test_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.yaml")


def test_load_config_with_history(tmp_path):
    config_data = {
        "character": {"name": "Test", "personality": "Friendly"},
        "model": {"provider": "openai", "api_key": "sk-test", "model_name": "gpt-4o"},
        "email": {
            "address": "test@example.com",
            "imap_server": "imap.example.com",
            "imap_port": 993,
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "auth_password": "pass",
        },
        "history": {
            "enabled": True,
            "max_recent_messages": 5,
            "summarize_every_n": 3,
        },
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")

    config = load_config(str(config_file))
    assert config.history.enabled is True
    assert config.history.max_recent_messages == 5
    assert config.history.summarize_every_n == 3


def test_load_config_history_defaults(tmp_path):
    config_data = {
        "character": {"name": "Test", "personality": "Friendly"},
        "model": {"provider": "openai", "api_key": "sk-test", "model_name": "gpt-4o"},
        "email": {
            "address": "test@example.com",
            "imap_server": "imap.example.com",
            "imap_port": 993,
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "auth_password": "pass",
        },
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")

    config = load_config(str(config_file))
    assert config.history.enabled is True
    assert config.history.max_recent_messages == 10
    assert config.history.summarize_every_n == 5
