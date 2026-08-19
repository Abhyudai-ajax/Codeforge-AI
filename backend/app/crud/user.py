"""
User CRUD Repository

Implements the repository pattern for async database access.

All database operations for the User model are encapsulated here.
Service-layer code should never interact with AsyncSession directly.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class UserCRUD:
    """Repository providing async CRUD operations for User."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ==========================================================
    # Internal Helpers
    # ==========================================================

    async def _commit(self, user: User) -> User:
        """Commit transaction and refresh instance."""

        try:
            await self._session.commit()
            await self._session.refresh(user)
            return user

        except IntegrityError:
            await self._session.rollback()
            logger.exception("Database integrity error.")
            raise

    # ==========================================================
    # Read Operations
    # ==========================================================

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_github_id(self, github_id: str) -> User | None:
        result = await self._session.execute(select(User).where(User.github_id == github_id))
        return result.scalar_one_or_none()

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        """Return paginated users."""

        total_result = await self._session.execute(select(func.count()).select_from(User))

        total = total_result.scalar_one()

        result = await self._session.execute(
            select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        )

        return list(result.scalars().all()), total

    # ==========================================================
    # Create Operations
    # ==========================================================

    async def create(
        self,
        *,
        username: str,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
    ) -> User:

        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=UserRole.USER,
            is_active=True,
            is_verified=False,
        )

        self._session.add(user)

        user = await self._commit(user)

        logger.info("Created user %s", user.email)

        return user

    async def create_oauth_user(
        self,
        *,
        username: str,
        email: str,
        github_id: str,
        github_username: str | None = None,
        full_name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:

        user = User(
            username=username,
            email=email,
            hashed_password=None,
            github_id=github_id,
            github_username=github_username,
            full_name=full_name,
            avatar_url=avatar_url,
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
        )

        self._session.add(user)

        user = await self._commit(user)

        logger.info("Created GitHub user %s", user.email)

        return user

    # ==========================================================
    # Update Operations
    # ==========================================================

    async def update(
        self,
        user: User,
        **kwargs: object,
    ) -> User:

        allowed_fields = {
            "username",
            "email",
            "hashed_password",
            "full_name",
            "avatar_url",
            "bio",
            "github_username",
            "github_id",
            "role",
            "is_active",
            "is_verified",
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(user, key, value)

        self._session.add(user)

        user = await self._commit(user)

        logger.info("Updated user %s", user.id)

        return user

    async def activate(self, user: User) -> User:
        user.is_active = True

        self._session.add(user)

        user = await self._commit(user)

        logger.info("Activated user %s", user.id)

        return user

    async def deactivate(self, user: User) -> User:
        user.is_active = False

        self._session.add(user)

        user = await self._commit(user)

        logger.info("Deactivated user %s", user.id)

        return user

    async def verify(self, user: User) -> User:
        user.is_verified = True

        self._session.add(user)

        user = await self._commit(user)

        logger.info("Verified user %s", user.id)

        return user

    # ==========================================================
    # Delete Operations
    # ==========================================================

    async def delete(self, user: User) -> None:
        await self._session.delete(user)
        await self._session.commit()

        logger.info("Deleted user %s", user.id)

    # ==========================================================
    # Utility Operations
    # ==========================================================

    async def exists_email(self, email: str) -> bool:
        return await self.get_by_email(email) is not None

    async def exists_username(self, username: str) -> bool:
        return await self.get_by_username(username) is not None
