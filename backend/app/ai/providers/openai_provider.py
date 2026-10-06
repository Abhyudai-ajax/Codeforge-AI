"""OpenAI provider implementation for the AI module."""

from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, status

from app.ai.providers.base import BaseAIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


_OPENAI_DEFAULTS = ("https://api.openai.com/v1", "gpt-4o-mini")

# OpenAI-compatible services recognised by their key prefix, so pasting a key is
# enough. An explicitly configured base URL or model always wins.
_COMPATIBLE_SERVICES = {
    "gsk_": ("https://api.groq.com/openai/v1", "openai/gpt-oss-120b"),  # Groq
    "xai-": ("https://api.x.ai/v1", "grok-3-mini"),  # xAI Grok
}


def resolve_endpoint(api_key: str, base_url: str, model: str) -> tuple[str, str]:
    """Pick the base URL and model for the service this key belongs to."""
    for prefix, (service_url, service_model) in _COMPATIBLE_SERVICES.items():
        if api_key.startswith(prefix):
            if base_url.rstrip("/") == _OPENAI_DEFAULTS[0]:
                base_url = service_url
            if model == _OPENAI_DEFAULTS[1]:
                model = service_model
            break
    return base_url, model


class OpenAIProvider(BaseAIProvider):
    """AI provider implementation that calls the OpenAI REST API."""

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ) -> str:
        if not settings.OPENAI_API_KEY:
            logger.error("OpenAI API key is not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI is not configured on this server.",
            )

        base_url, model = resolve_endpoint(
            settings.OPENAI_API_KEY, settings.OPENAI_BASE_URL, settings.OPENAI_MODEL
        )
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
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
            try:
                reason = response.json()["error"]["message"]
            except Exception:
                reason = response.reason_phrase
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI service ({base_url}) returned HTTP {response.status_code}: {reason}",
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
