from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ComplexityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LLMEntry(BaseModel):
    alias: str
    provider: str
    model: str
    api_key: str = Field(description="Valor direto ou 'env:VAR_NAME'")
    complexity_levels: list[ComplexityLevel] = Field(
        default_factory=lambda: [ComplexityLevel.MEDIUM]
    )
    description: Optional[str] = None
    extra_params: dict = Field(default_factory=dict)


class DireciondorConfig(BaseModel):
    provider: str = "groq"
    model: str = "llama-3.1-8b-instant"
    api_key: str = "env:GROQ_API_KEY"


class AppConfig(BaseModel):
    direcionador: DireciondorConfig = Field(default_factory=DireciondorConfig)
    arsenal: list[LLMEntry] = Field(default_factory=list)

    def get_llm_by_alias(self, alias: str) -> Optional[LLMEntry]:
        return next((llm for llm in self.arsenal if llm.alias == alias), None)

    def get_llms_for_complexity(self, level: ComplexityLevel) -> list[LLMEntry]:
        return [llm for llm in self.arsenal if level in llm.complexity_levels]
