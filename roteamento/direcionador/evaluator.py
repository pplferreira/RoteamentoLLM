from __future__ import annotations

import json
import re

from roteamento.adapters import call_direcionador
from roteamento.config import DireciondorConfig, ComplexityLevel

SYSTEM_PROMPT = """\
Você é um avaliador de complexidade de prompts. Sua única função é classificar o prompt do usuário em um dos três níveis:

- **low**: Perguntas factuais simples, traduções, formatação, resumos curtos, conversão de unidades, \
piadas, saudações, perguntas com resposta direta.
- **medium**: Análise de texto, explicações de conceitos, debugging simples, consultas com algum \
raciocínio, escrita criativa moderada, código simples.
- **high**: Raciocínio complexo em múltiplas etapas, geração de código avançado, arquitetura de \
sistemas, pesquisa aprofundada, tarefas que exigem planejamento e criatividade elevada.

Responda APENAS com um JSON no formato:
{"level": "low|medium|high", "reason": "<justificativa curta em uma frase>"}

Não adicione nenhum texto fora do JSON.\
"""


def evaluate_complexity(prompt: str, config: DireciondorConfig) -> tuple[ComplexityLevel, str]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    raw = call_direcionador(config, messages)

    # Extract JSON even if there's extra whitespace or markdown fences
    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    if not match:
        return ComplexityLevel.MEDIUM, "Não foi possível avaliar; usando nível médio como padrão."

    try:
        data = json.loads(match.group())
        level = ComplexityLevel(data.get("level", "medium"))
        reason = data.get("reason", "")
        return level, reason
    except (json.JSONDecodeError, ValueError):
        return ComplexityLevel.MEDIUM, "Resposta inválida do direcionador; usando nível médio."
