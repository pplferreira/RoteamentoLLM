from __future__ import annotations

import os
from pathlib import Path

import yaml

from .models import AppConfig, DireciondorConfig, LLMEntry

CONFIG_DIR = Path.home() / ".rllm"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> AppConfig:
    _ensure_config_dir()
    if not CONFIG_FILE.exists():
        return AppConfig()
    with open(CONFIG_FILE) as f:
        data = yaml.safe_load(f) or {}
    return AppConfig.model_validate(data)


def save_config(config: AppConfig) -> None:
    _ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        # mode='json' serializes enums to their string values (not Python objects)
        yaml.dump(config.model_dump(mode="json"), f, default_flow_style=False, allow_unicode=True)


def resolve_api_key(raw: str) -> str:
    """Resolve 'env:VAR_NAME' or return the value as-is."""
    if raw.startswith("env:"):
        var = raw[4:]
        value = os.environ.get(var)
        if not value:
            raise EnvironmentError(f"Variável de ambiente '{var}' não está definida.")
        return value
    return raw


def add_llm(entry: LLMEntry) -> None:
    config = load_config()
    config.arsenal = [llm for llm in config.arsenal if llm.alias != entry.alias]
    config.arsenal.append(entry)
    save_config(config)


def remove_llm(alias: str) -> bool:
    config = load_config()
    before = len(config.arsenal)
    config.arsenal = [llm for llm in config.arsenal if llm.alias != alias]
    save_config(config)
    return len(config.arsenal) < before


def set_direcionador(direcionador: DireciondorConfig) -> None:
    config = load_config()
    config.direcionador = direcionador
    save_config(config)
