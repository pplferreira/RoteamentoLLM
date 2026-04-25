import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from roteamento.config.models import AppConfig, LLMEntry, ComplexityLevel
from roteamento.config.manager import resolve_api_key


def test_resolve_api_key_direct():
    assert resolve_api_key("sk-test-123") == "sk-test-123"


def test_resolve_api_key_env_var():
    with patch.dict(os.environ, {"MY_API_KEY": "secret-value"}):
        assert resolve_api_key("env:MY_API_KEY") == "secret-value"


def test_resolve_api_key_missing_env_var():
    key = "env:DEFINITELY_NOT_SET_12345"
    os.environ.pop("DEFINITELY_NOT_SET_12345", None)
    with pytest.raises(EnvironmentError, match="DEFINITELY_NOT_SET_12345"):
        resolve_api_key(key)


def test_get_llm_by_alias():
    config = AppConfig()
    config.arsenal = [
        LLMEntry(alias="fast", provider="groq", model="llama", api_key="k"),
        LLMEntry(alias="smart", provider="openai", model="gpt-4o", api_key="k"),
    ]
    assert config.get_llm_by_alias("smart").model == "gpt-4o"
    assert config.get_llm_by_alias("nonexistent") is None


def test_save_and_load_config(tmp_path):
    with patch("roteamento.config.manager.CONFIG_DIR", tmp_path), \
         patch("roteamento.config.manager.CONFIG_FILE", tmp_path / "config.yaml"):
        from roteamento.config.manager import save_config, load_config

        config = AppConfig()
        config.arsenal = [
            LLMEntry(
                alias="test-llm",
                provider="openai",
                model="gpt-4o-mini",
                api_key="env:OPENAI_API_KEY",
                complexity_levels=[ComplexityLevel.MEDIUM],
                description="Test model",
            )
        ]
        save_config(config)
        loaded = load_config()

        assert len(loaded.arsenal) == 1
        assert loaded.arsenal[0].alias == "test-llm"
        assert loaded.arsenal[0].model == "gpt-4o-mini"
