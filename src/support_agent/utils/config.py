"""Configuration management."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path = "config/config.yaml") -> dict[str, Any]:
    """Load configuration from YAML file with env var substitution."""
    config_path = Path(path)

    if not config_path.exists():
        return _default_config()

    with open(config_path, "r") as f:
        raw = f.read()

    # Substitute environment variables
    raw = _substitute_env_vars(raw)
    config = yaml.safe_load(raw) or {}

    return _merge_with_defaults(config)


def _substitute_env_vars(text: str) -> str:
    """Replace ${VAR} patterns with environment variable values."""
    import re

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return re.sub(r"\$\{(\w+)\}", replacer, text)


def _default_config() -> dict[str, Any]:
    """Return default configuration."""
    return {
        "mimo": {
            "api_key": os.environ.get("MIMO_API_KEY", ""),
            "model": os.environ.get("MIMO_MODEL", "MiMo-V2.5-Pro"),
            "base_url": os.environ.get("MIMO_BASE_URL", "https://api.mimo.xiaomi.com/v1"),
            "max_tokens": 4096,
            "temperature": 0.3,
        },
        "knowledge": {
            "embedding_model": "text-embedding-3-small",
            "chunk_size": 512,
            "top_k": 5,
        },
        "channels": {
            "email": {
                "imap_host": os.environ.get("IMAP_HOST", "imap.gmail.com"),
                "smtp_host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
            },
            "chat": {
                "websocket_url": os.environ.get("CHAT_WEBSOCKET_URL", ""),
            },
            "discord": {
                "token": os.environ.get("DISCORD_BOT_TOKEN", ""),
            },
        },
        "database": {
            "url": os.environ.get("DATABASE_URL", "postgresql://localhost:5432/support_agent"),
        },
        "redis": {
            "url": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        },
    }


def _merge_with_defaults(config: dict[str, Any]) -> dict[str, Any]:
    """Merge loaded config with defaults."""
    defaults = _default_config()

    def merge(base: dict, override: dict) -> dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge(result[key], value)
            else:
                result[key] = value
        return result

    return merge(defaults, config)
