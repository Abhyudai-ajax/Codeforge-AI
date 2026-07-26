"""
User CRUD Repository
Implements the repository pattern for async database access.

All database operations are encapsulated here.  Service-layer code must
never construct raw SQL or call the session directly — use this class.
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class UserCRUD:
    """
    Async CRUD operations for the :class:`~app.models.user.User` model.

    Each method is stateless with respect to the session — the session is
    injected at instantiation so the class is easily unit-testable with a
    mock session.

    Args:
        session: An open :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialise the repository with an injected async session."""
        self._session = session

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_by_email(self, email: str) -> User | None:
        """
        Return the user whose email matches ``email``, or ``None``.

        Args:
            email: Email address to look up (case-sensitive).

        Returns:
            :class:`~app.models.user.User` or ``None``.
        """
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        logger.debug("get_by_email(%r) -> %s", email, user)
        return user

    async def get_by_username(self, username: str) -> User | None:
        """
        Return the user whose username matches ``username``, or ``None``.

        Args:
            username: Username to look up (case-sensitive).

        Returns:
            :class:`~app.models.user.User` or ``None``.
        """
        stmt = select(User).where(User.username == username)
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        logger.debug("get_by_username(%r) -> %s", username, user)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """
        Return the user with primary key ``user_id``, or ``None``.

        Args:
            user_id: UUID primary key.

        Returns:
            :class:`~app.models.user.User` or ``None``.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        logger.debug("get_by_id(%s) -> %s", user_id, user)
        return user

    async def get_by_github_id(self, github_id: str) -> User | None:
        """Return the user whose GitHub ID matches ``github_id``, or ``None``."""
        stmt = select(User).where(User.github_id == github_id)
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        logger.debug("get_by_github_id(%r) -> %s", github_id, user)
        return user

    async def list_users(self, skip: int = 0, limit: int = 50) -> tuple[list[User], int]:
        """
        List users with offset pagination and return (items, total_count).

        Args:
            skip: Number of records to skip.
            limit: Maximum records to return.

        Returns:
            Tuple of (list of users, total count).
        """
        from sqlalchemy import func

        count_stmt = select(func.count()).select_from(User)
        total_res = await self._session.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        users = list(result.scalars().all())
        return users, total

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def create(
        self,
        *,
        username: str,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
    ) -> User:
        """Persist a new user to the database."""
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
        try:
            await self._session.commit()
            await self._session.refresh(user)
        except IntegrityError:
            await self._session.rollback()
            raise
        logger.info("User created: id=%s email=%s", user.id, user.email)
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
        """Persist a new GitHub OAuth user (passwordless, verified)."""
        user = User(
            username=username,
            email=email,
            hashed_password=None,
            full_name=full_name,
            avatar_url=avatar_url,
            github_id=github_id,
            github_username=github_username,
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
        )
        self._session.add(user)
        try:
            await self._session.commit()
            await self._session.refresh(user)
        except IntegrityError:
            await self._session.rollback()
            raise
        logger.info("OAuth user created: id=%s github_id=%s", user.id, github_id)
        return user

    async def update(self, user: User, **kwargs: object) -> User:
        """
        Update fields on an existing User instance and commit.

        Args:
            user: The User ORM object to mutate.
            **kwargs: Field-value pairs to set.

        Returns:
            The refreshed User ORM instance.
        """
        for key, value in kwargs.items():
            if value is not None or key in (
                "full_name",
                "avatar_url",
                "bio",
                "github_id",
                "github_username",
            ):
                setattr(user, key, value)
        self._session.add(user)
        try:
            await self._session.commit()
            await self._session.refresh(user)
        except IntegrityError:
            await self._session.rollback()
            raise
        logger.info("User updated: id=%s", user.id)
        return user
