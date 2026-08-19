"""OpenAI provider implementation for the AI module."""

from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, status

from app.ai.providers.base import BaseAIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """AI provider implementation that calls the OpenAI REST API."""

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
    ) -> str:
        if not settings.OPENAI_API_KEY:
            logger.error("OpenAI API key is not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI is not configured on this server.",
            )

        url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            logger.error(
                "OpenAI request failed: status=%s body=%s",
                response.status_code,
                response.text,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to receive a valid response from OpenAI.",
            )

        body = response.json()
        choices = body.get("choices")
        if not choices or not isinstance(choices, list):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI response did not contain valid choices.",
            )

        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI response content is malformed.",
            )

        return content.strip()
