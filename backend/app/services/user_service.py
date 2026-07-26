"""
User Service Layer
Business logic for profile updates, password changes, and admin user management.
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.crud.user import UserCRUD
from app.models.user import User, UserRole
from app.schemas.user import (
    PasswordChangeRequest,
    UserProfileUpdate,
    UserRoleUpdate,
)

logger = logging.getLogger(__name__)


class UserService:
    """Service layer for User management and profile operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialise with an injected async session."""
        self._session = session
        self._crud = UserCRUD(session)

    async def update_profile(self, user: User, data: UserProfileUpdate) -> User:
        """Update current user profile fields."""
        updated = await self._crud.update(
            user,
            full_name=data.full_name,
            avatar_url=data.avatar_url,
            bio=data.bio,
        )
        logger.info("Profile updated for user: id=%s", user.id)
        return updated

    async def change_password(self, user: User, data: PasswordChangeRequest) -> None:
        """Change user password after verifying current password."""
        if user.hashed_password is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth accounts without a password cannot change password directly. Set up password reset.",
            )

        if not verify_password(data.current_password, user.hashed_password):
            logger.warning("Password change failed — invalid current password: id=%s", user.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        new_hashed = hash_password(data.new_password)
        await self._crud.update(user, hashed_password=new_hashed)
        logger.info("Password changed successfully for user: id=%s", user.id)

    async def list_users_admin(self, skip: int = 0, limit: int = 50) -> tuple[list[User], int]:
        """List users for admin dashboard with offset pagination."""
        return await self._crud.list_users(skip=skip, limit=limit)

    async def update_user_role_admin(self, target_user_id: str, data: UserRoleUpdate) -> User:
        """Update user role or active status (admin only)."""
        import uuid

        try:
            target_uuid = uuid.UUID(target_user_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid target user UUID format.",
            ) from exc

        target_user = await self._crud.get_by_id(target_uuid)
        if target_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        role_enum: UserRole | None = None
        if data.role is not None:
            try:
                role_enum = UserRole(data.role.lower())
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role '{data.role}'. Must be 'user' or 'admin'.",
                ) from exc

        updated = await self._crud.update(
            target_user,
            role=role_enum if role_enum is not None else target_user.role,
            is_active=data.is_active if data.is_active is not None else target_user.is_active,
        )
        logger.info(
            "Admin updated user role/status: id=%s role=%s", target_user.id, target_user.role
        )
        return updated
