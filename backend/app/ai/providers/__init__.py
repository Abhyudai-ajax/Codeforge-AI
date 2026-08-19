"""AI provider factory and registry."""

from __future__ import annotations

from typing import Type

from app.ai.providers.base import BaseAIProvider
from app.ai.providers.ollama_provider import OllamaProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import settings

PROVIDER_REGISTRY: dict[str, Type[BaseAIProvider]] = {
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def get_ai_provider() -> BaseAIProvider:
    provider_key = settings.AI_PROVIDER.lower().strip()
    provider_class = PROVIDER_REGISTRY.get(provider_key)
    if provider_class is None:
        available = ", ".join(sorted(PROVIDER_REGISTRY.keys()))
        raise ValueError(
            f"Unsupported AI provider '{settings.AI_PROVIDER}'. Available providers: {available}."
        )
    return provider_class()
