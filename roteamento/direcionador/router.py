from __future__ import annotations

from roteamento.config import AppConfig, ComplexityLevel, LLMEntry


def pick_llm(config: AppConfig, level: ComplexityLevel) -> LLMEntry:
    """
    Picks the best LLM for the given complexity level.

    Strategy: exact match first → fallback up (higher complexity) → fallback down.
    Raises ValueError when the arsenal is empty or no LLM can handle the request.
    """
    if not config.arsenal:
        raise ValueError(
            "Acervo de modelos vazio. Adicione pelo menos um modelo de LLM com `rllm add`."
        )

    candidates = [llm for llm in config.arsenal if level in llm.complexity_levels]
    if candidates:
        return candidates[0]

    # Fallback: try adjacent levels
    order = [ComplexityLevel.LOW, ComplexityLevel.MEDIUM, ComplexityLevel.HIGH]
    idx = order.index(level)

    for fallback_idx in sorted(range(len(order)), key=lambda i: abs(i - idx)):
        if fallback_idx == idx:
            continue
        fallback_level = order[fallback_idx]
        candidates = [llm for llm in config.arsenal if fallback_level in llm.complexity_levels]
        if candidates:
            return candidates[0]

    # Last resort: return the first entry
    return config.arsenal[0]
