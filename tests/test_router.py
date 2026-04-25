import pytest

from roteamento.config.models import AppConfig, LLMEntry, ComplexityLevel
from roteamento.direcionador.router import pick_llm


def _make_llm(alias: str, levels: list[ComplexityLevel]) -> LLMEntry:
    return LLMEntry(
        alias=alias,
        provider="openai",
        model="gpt-4o-mini",
        api_key="test-key",
        complexity_levels=levels,
    )


def _make_config(llms: list[LLMEntry]) -> AppConfig:
    config = AppConfig()
    config.arsenal = llms
    return config


def test_pick_exact_low():
    config = _make_config([
        _make_llm("fast", [ComplexityLevel.LOW]),
        _make_llm("smart", [ComplexityLevel.HIGH]),
    ])
    assert pick_llm(config, ComplexityLevel.LOW).alias == "fast"


def test_pick_exact_high():
    config = _make_config([
        _make_llm("fast", [ComplexityLevel.LOW]),
        _make_llm("smart", [ComplexityLevel.HIGH]),
    ])
    assert pick_llm(config, ComplexityLevel.HIGH).alias == "smart"


def test_pick_fallback_when_no_exact_match():
    config = _make_config([
        _make_llm("only-high", [ComplexityLevel.HIGH]),
    ])
    # No LOW model; should fall back to HIGH
    result = pick_llm(config, ComplexityLevel.LOW)
    assert result.alias == "only-high"


def test_pick_multi_level():
    config = _make_config([
        _make_llm("versatile", [ComplexityLevel.LOW, ComplexityLevel.MEDIUM, ComplexityLevel.HIGH]),
    ])
    assert pick_llm(config, ComplexityLevel.MEDIUM).alias == "versatile"


def test_empty_arsenal_raises():
    config = _make_config([])
    with pytest.raises(ValueError, match="Arsenal vazio"):
        pick_llm(config, ComplexityLevel.MEDIUM)


def test_first_candidate_wins():
    config = _make_config([
        _make_llm("alpha", [ComplexityLevel.MEDIUM]),
        _make_llm("beta", [ComplexityLevel.MEDIUM]),
    ])
    assert pick_llm(config, ComplexityLevel.MEDIUM).alias == "alpha"
