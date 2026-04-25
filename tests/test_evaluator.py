import json
from unittest.mock import patch

import pytest

from roteamento.config.models import DireciondorConfig, ComplexityLevel
from roteamento.direcionador.evaluator import evaluate_complexity


@pytest.fixture
def config():
    return DireciondorConfig(provider="groq", model="llama-3.1-8b-instant", api_key="test")


def _mock_call(response: str):
    return patch("roteamento.direcionador.evaluator.call_direcionador", return_value=response)


def test_evaluate_low(config):
    payload = json.dumps({"level": "low", "reason": "Pergunta simples"})
    with _mock_call(payload):
        level, reason = evaluate_complexity("Qual é a capital do Brasil?", config)
    assert level == ComplexityLevel.LOW
    assert reason == "Pergunta simples"


def test_evaluate_high(config):
    payload = json.dumps({"level": "high", "reason": "Raciocínio complexo"})
    with _mock_call(payload):
        level, reason = evaluate_complexity("Projete uma arquitetura de microsserviços", config)
    assert level == ComplexityLevel.HIGH


def test_evaluate_fallback_on_bad_json(config):
    with _mock_call("desculpe, não consigo classificar"):
        level, reason = evaluate_complexity("anything", config)
    assert level == ComplexityLevel.MEDIUM


def test_evaluate_json_in_markdown_fence(config):
    payload = f'```json\n{json.dumps({"level": "medium", "reason": "Análise moderada"})}\n```'
    with _mock_call(payload):
        level, reason = evaluate_complexity("Explique o que é machine learning", config)
    assert level == ComplexityLevel.MEDIUM
