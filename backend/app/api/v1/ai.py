"""AI API Routes."""

import logging

from fastapi import APIRouter, Depends

from app.ai.dependencies import get_ai_service
from app.ai.schemas import AITextRequest, AITextResponse
from app.ai.services.ai_service import AIService
from app.dependencies.auth import get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post(
    "/review",
    response_model=AITextResponse,
    summary="Review code using AI",
    description="Analyze the supplied code and return a code review summary.",
)
async def review_code(
    payload: AITextRequest,
    current_user: User = Depends(get_current_active_user),
    ai_service: AIService = Depends(get_ai_service),
) -> AITextResponse:
    return await ai_service.review_code(payload)


@router.post(
    "/debug",
    response_model=AITextResponse,
    summary="Debug code using AI",
    description="Analyze the supplied code and return debugging guidance.",
)
async def debug_code(
    payload: AITextRequest,
    current_user: User = Depends(get_current_active_user),
    ai_service: AIService = Depends(get_ai_service),
) -> AITextResponse:
    return await ai_service.debug_code(payload)


@router.post(
    "/explain",
    response_model=AITextResponse,
    summary="Explain code using AI",
    description="Explain the supplied code in plain language.",
)
async def explain_code(
    payload: AITextRequest,
    current_user: User = Depends(get_current_active_user),
    ai_service: AIService = Depends(get_ai_service),
) -> AITextResponse:
    return await ai_service.explain_code(payload)


@router.post(
    "/tests",
    response_model=AITextResponse,
    summary="Generate tests using AI",
    description="Generate unit tests for the supplied code.",
)
async def generate_tests(
    payload: AITextRequest,
    current_user: User = Depends(get_current_active_user),
    ai_service: AIService = Depends(get_ai_service),
) -> AITextResponse:
    return await ai_service.generate_tests(payload)


@router.post(
    "/documentation",
    response_model=AITextResponse,
    summary="Generate documentation using AI",
    description="Generate documentation for the supplied code.",
)
async def generate_documentation(
    payload: AITextRequest,
    current_user: User = Depends(get_current_active_user),
    ai_service: AIService = Depends(get_ai_service),
) -> AITextResponse:
    return await ai_service.generate_documentation(payload)


@router.post(
    "/dsa-hint",
    response_model=AITextResponse,
    summary="Generate a DSA hint using AI",
    description="Provide a focused algorithmic hint for the supplied problem or code.",
)
async def generate_dsa_hint(
    payload: AITextRequest,
    current_user: User = Depends(get_current_active_user),
    ai_service: AIService = Depends(get_ai_service),
) -> AITextResponse:
    return await ai_service.generate_dsa_hint(payload)
