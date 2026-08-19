"""Base provider abstraction for AI text generation."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    """Abstract interface for AI provider implementations."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
    ) -> str:
        """Generate a text completion for the supplied prompt."""
        raise NotImplementedError
