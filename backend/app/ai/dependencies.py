"""Dependencies for AI service injection."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.ai.services.ai_service import AIService
from app.dependencies.auth import get_current_active_user
from app.models.user import User


def get_ai_service(
    current_user: User = Depends(get_current_active_user),
) -> AIService:
    """Provide the configured AI service instance."""
    try:
        return AIService()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
