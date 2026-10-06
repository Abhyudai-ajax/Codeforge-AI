"""AI service layer: delegates to the configured provider, else analyses the input offline."""

from __future__ import annotations

import asyncio
import logging

from fastapi import HTTPException

from app.ai import offline_analyzer
from app.ai.providers import get_ai_provider
from app.ai.providers.base import BaseAIProvider
from app.ai.schemas import AITextRequest, AITextResponse
from app.ai.utils.prompt_renderer import render_prompt
from app.ai.utils.prompt_templates import (
    CODE_REVIEW_PROMPT,
    DEBUG_PROMPT,
    DOCUMENTATION_PROMPT,
    DSA_HINT_PROMPT,
    EXPLAIN_PROMPT,
    GENERATE_TESTS_PROMPT,
)

logger = logging.getLogger(__name__)

_NOT_CONFIGURED = "OpenAI is not configured on this server."


class AIService:
    """Service layer for AI operations.

    When no model is configured (or the provider fails), answers come from
    ``offline_analyzer``, which inspects the submitted code itself, so the
    response always reflects what the user actually sent.
    """

    def __init__(self) -> None:
        self._provider: BaseAIProvider | None
        try:
            self._provider = get_ai_provider()
        except Exception:
            self._provider = None

    async def _generate(self, prompt: str, mode: str, request: AITextRequest) -> AITextResponse:
        failure: str | None = None
        if self._provider:
            try:
                return AITextResponse(result=await self._provider.generate_text(prompt))
            except HTTPException as e:
                failure = str(e.detail)
            except Exception as e:
                failure = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
        result = await asyncio.to_thread(
            offline_analyzer.analyze, mode, request.content, request.additional_context
        )
        # A missing key is the normal offline case; anything else is worth surfacing.
        if failure and failure != _NOT_CONFIGURED:
            logger.warning("AI provider failed (%s); using offline analysis.", failure)
            result = result.replace(
                offline_analyzer.OFFLINE_NOTE,
                f"\n\n---\n_⚠️ The AI model request failed ({failure}). "
                "Showing offline analysis of your code instead._",
            )
        return AITextResponse(result=result)

    def _prompt(self, template: str, request: AITextRequest) -> str:
        return render_prompt(
            template, content=request.content, context=request.additional_context
        )

    async def explain_code(self, request: AITextRequest) -> AITextResponse:
        return await self._generate(self._prompt(EXPLAIN_PROMPT, request), "explain", request)

    async def review_code(self, request: AITextRequest) -> AITextResponse:
        return await self._generate(self._prompt(CODE_REVIEW_PROMPT, request), "review", request)

    async def debug_code(self, request: AITextRequest) -> AITextResponse:
        return await self._generate(self._prompt(DEBUG_PROMPT, request), "debug", request)

    async def generate_tests(self, request: AITextRequest) -> AITextResponse:
        return await self._generate(self._prompt(GENERATE_TESTS_PROMPT, request), "tests", request)

    async def generate_documentation(self, request: AITextRequest) -> AITextResponse:
        return await self._generate(self._prompt(DOCUMENTATION_PROMPT, request), "docs", request)

    async def generate_dsa_hint(self, request: AITextRequest) -> AITextResponse:
        return await self._generate(self._prompt(DSA_HINT_PROMPT, request), "hint", request)

    async def generate_interview_feedback(self, request: AITextRequest) -> AITextResponse:
        prompt = (
            f"Analyze the following interview session performance:\n\n{request.content}\n"
            f"Context: {request.additional_context or ''}"
        )
        return await self._generate(prompt, "interview", request)

    async def generate_roadmap_recommendations(self, request: AITextRequest) -> AITextResponse:
        prompt = (
            f"Suggest next learning steps for user based on progress:\n\n{request.content}\n"
            f"Context: {request.additional_context or ''}"
        )
        return await self._generate(prompt, "roadmap", request)
