"""
User Profile API Routes.
GET   /users/me          — Get current user profile
PATCH /users/me          — Update current user profile details
PUT   /users/me/password — Change account password
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import (
    MessageResponse,
    PasswordChangeRequest,
    UserProfileUpdate,
    UserResponse,
)
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns public profile details of the authenticated user.",
)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Return profile of the authenticated user."""
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update full_name, avatar_url, or bio for the authenticated user.",
)
async def update_my_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update profile fields for current user."""
    service = UserService(db)
    updated = await service.update_profile(current_user, payload)
    return UserResponse.model_validate(updated)


@router.put(
    "/me/password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change account password",
    description="Change password after verifying the current password.",
)
async def change_my_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Change account password."""
    service = UserService(db)
    await service.change_password(current_user, payload)
    return MessageResponse(message="Password updated successfully.")
