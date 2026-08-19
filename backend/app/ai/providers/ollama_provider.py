"""Ollama provider implementation for the AI module."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.ai.providers.base import BaseAIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(BaseAIProvider):
    """AI provider implementation that calls a local Ollama API."""

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
    ) -> str:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/completions"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)

        if response.status_code != 200:
            logger.error(
                "Ollama request failed: status=%s body=%s",
                response.status_code,
                response.text,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to receive a valid response from Ollama.",
            )

        body = response.json()
        if not isinstance(body, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Ollama response content is malformed.",
            )

        output = body.get("output")
        if not output or not isinstance(output, list):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Ollama response did not contain valid output.",
            )

        first_output = output[0]
        if not isinstance(first_output, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Ollama response content is malformed.",
            )

        generated_text = first_output.get("generated_text")
        if not isinstance(generated_text, str):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Ollama response content is malformed.",
            )

        return generated_text.strip()
