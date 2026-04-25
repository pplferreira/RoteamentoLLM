from __future__ import annotations

from typing import Iterator

import litellm

from roteamento.config import LLMEntry, DireciondorConfig, resolve_api_key

litellm.suppress_debug_info = True


def _build_model_string(provider: str, model: str) -> str:
    """Build a litellm-compatible model string."""
    provider_prefixes = {
        "openai": "",
        "anthropic": "anthropic/",
        "google": "gemini/",
        "groq": "groq/",
        "ollama": "ollama/",
        "openrouter": "openrouter/",
        "mistral": "mistral/",
        "cohere": "cohere/",
        "together": "together_ai/",
        "perplexity": "perplexity/",
        "deepseek": "deepseek/",
        "xai": "xai/",
    }
    prefix = provider_prefixes.get(provider.lower(), f"{provider}/")
    if model.startswith(prefix) or "/" in model:
        return model
    return f"{prefix}{model}"


def call_llm(entry: LLMEntry, messages: list[dict], stream: bool = True) -> Iterator[str]:
    api_key = resolve_api_key(entry.api_key)
    model_str = _build_model_string(entry.provider, entry.model)

    params = {
        "model": model_str,
        "messages": messages,
        "api_key": api_key,
        "stream": stream,
        **entry.extra_params,
    }

    if stream:
        response = litellm.completion(**params)
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    else:
        response = litellm.completion(**params)
        yield response.choices[0].message.content


def call_direcionador(config: DireciondorConfig, messages: list[dict]) -> str:
    api_key = resolve_api_key(config.api_key)
    model_str = _build_model_string(config.provider, config.model)

    response = litellm.completion(
        model=model_str,
        messages=messages,
        api_key=api_key,
        stream=False,
    )
    return response.choices[0].message.content
