"""User configuration (TOML). Never stores API keys — those live in the OS keychain."""

from __future__ import annotations

import copy
import json
import os
import tempfile
import tomllib
from pathlib import Path
from typing import Any

import tomli_w
from platformdirs import user_cache_path, user_config_path, user_data_path

from kunji.constants import APP_NAME

DEFAULTS: dict[str, Any] = {
    "default_model": "",
    "fallback": [],
    "chat": {"system_prompt": "", "max_tokens": 4096, "history": True},
    "display": {"currency": "USD", "usd_rate": 1.0, "max_width": 100},
    "budget": {"daily": {}},
    "updates": {"check": True},
    "network": {"catalog": True},
    "cloud": {"url": "", "checkin": True},
    "providers": {},
    "custom_providers": {},
    "pricing": {},
}


def _home_override() -> Path | None:
    value = os.environ.get("KUNJI_HOME")
    return Path(value) if value else None


def config_dir() -> Path:
    home = _home_override()
    return home / "config" if home else user_config_path(APP_NAME, appauthor=False)


def data_dir() -> Path:
    home = _home_override()
    return home / "data" if home else user_data_path(APP_NAME, appauthor=False)


def cache_dir() -> Path:
    home = _home_override()
    return home / "cache" if home else user_cache_path(APP_NAME, appauthor=False)


def config_path() -> Path:
    return config_dir() / "config.toml"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        try:
            path.chmod(0o700)
        except OSError:
            pass
    return path


def atomic_write(path: Path, data: bytes) -> None:
    """Write a file atomically so a crash never leaves a half-written config."""
    ensure_dir(path.parent)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        if os.name == "posix":
            os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def coerce(value: str) -> Any:
    """Turn a CLI string into bool/int/float/list where that is clearly intended."""
    lowered = value.strip().lower()
    if lowered in {"true", "on", "yes"}:
        return True
    if lowered in {"false", "off", "no"}:
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    if value.strip().startswith("["):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
    return value


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, data: dict[str, Any], path: Path):
        self.data = data
        self.path = path

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        path = path or config_path()
        user: dict[str, Any] = {}
        if path.exists():
            try:
                user = tomllib.loads(path.read_text(encoding="utf-8"))
            except tomllib.TOMLDecodeError as exc:
                raise ConfigError(f"Config file is not valid TOML: {path}\n{exc}") from exc
        return cls(_deep_merge(DEFAULTS, user), path)

    def save(self) -> None:
        atomic_write(self.path, tomli_w.dumps(self.data).encode("utf-8"))

    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, dotted: str, value: Any) -> None:
        parts = dotted.split(".")
        node = self.data
        for part in parts[:-1]:
            child = node.get(part)
            if not isinstance(child, dict):
                child = {}
                node[part] = child
            node = child
        node[parts[-1]] = value

    def unset(self, dotted: str) -> bool:
        parts = dotted.split(".")
        node = self.data
        for part in parts[:-1]:
            node = node.get(part)
            if not isinstance(node, dict):
                return False
        return node.pop(parts[-1], None) is not None

    # Convenience accessors ---------------------------------------------------
    @property
    def max_width(self) -> int:
        try:
            return max(40, int(self.get("display.max_width", 100)))
        except (TypeError, ValueError):
            return 100

    def provider_entry(self, provider_id: str) -> dict[str, Any]:
        entry = self.data.setdefault("providers", {}).get(provider_id)
        return entry if isinstance(entry, dict) else {}
