"""
Authentication Service
Business logic for user registration, authentication, and user lookup.

Routes must contain no business logic — they delegate everything here.
"""

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.crud.user import UserCRUD
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import RegisterRequest

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service layer for all authentication-related operations.

    Raises :exc:`fastapi.HTTPException` on every failure path so that
    the caller (route handler or dependency) never has to handle raw
    database or cryptography exceptions.

    Args:
        session: An open :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialise the service with a database session."""
        self._session = session
        self._crud = UserCRUD(session)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(self, data: RegisterRequest) -> User:
        """
        Register a new user account.

        Steps:
        1. Validate email uniqueness.
        2. Validate username uniqueness.
        3. Hash the plain-text password.
        4. Persist the new user via the CRUD repository.

        Args:
            data: Validated :class:`~app.schemas.user.RegisterRequest` payload.

        Returns:
            The newly created :class:`~app.models.user.User` ORM instance.

        Raises:
            HTTPException 409: Email is already registered.
            HTTPException 409: Username is already taken.
        """
        # --- Duplicate email check ---
        if await self._crud.get_by_email(data.email) is not None:
            logger.warning("Registration rejected — email already in use: %s", data.email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            )

        # --- Duplicate username check ---
        if await self._crud.get_by_username(data.username) is not None:
            logger.warning("Registration rejected — username taken: %s", data.username)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This username is already taken.",
            )

        hashed = hash_password(data.password)
        user = await self._crud.create(
            username=data.username,
            email=data.email,
            hashed_password=hashed,
            full_name=data.full_name,
        )
        logger.info("User registered: id=%s email=%s", user.id, user.email)
        return user

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def login(self, data: LoginRequest) -> TokenResponse:
        """
        Authenticate a user and issue JWT tokens.

        Constant-time behaviour: ``verify_password`` is called even when
        the user does not exist to prevent timing-based user enumeration.

        Args:
            data: Validated :class:`~app.schemas.auth.LoginRequest` payload.

        Returns:
            A :class:`~app.schemas.auth.TokenResponse` with access + refresh tokens.

        Raises:
            HTTPException 401: Invalid email or password.
            HTTPException 403: Account is inactive.
        """
        user = await self._crud.get_by_email(data.email)

        # Always call verify_password to ensure constant-time comparison
        # regardless of whether the user was found or is an OAuth-only user.
        sentinel_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeg6Lruj3vjPGga31lW"
        actual_hash = (
            user.hashed_password
            if (user is not None and user.hashed_password is not None)
            else sentinel_hash
        )
        password_ok = verify_password(data.password, actual_hash)

        if user is None or not password_ok:
            logger.warning("Login failed — invalid credentials for: %s", data.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            logger.warning("Login failed — inactive account: id=%s", user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated. Please contact support.",
            )

        token_payload = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(data=token_payload)
        refresh_token = create_refresh_token(data=token_payload)

        logger.info("User authenticated: id=%s", user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ------------------------------------------------------------------
    # Token → User resolution
    # ------------------------------------------------------------------

    async def get_user_by_id(self, user_id_str: str) -> User:
        """
        Resolve a JWT ``sub`` claim (string UUID) to a live User record.

        Used by the ``get_current_user`` FastAPI dependency after token
        decoding.

        Args:
            user_id_str: String representation of the user's UUID taken
                directly from the JWT ``"sub"`` claim.

        Returns:
            The corresponding :class:`~app.models.user.User` instance.

        Raises:
            HTTPException 401: The ``sub`` is not a valid UUID or the user
                does not exist in the database.
            HTTPException 403: The account is inactive.
        """
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError as exc:
            logger.warning("Invalid UUID in token sub claim: %r", user_id_str)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        user = await self._crud.get_by_id(user_id)
        if user is None:
            logger.warning("Token references non-existent user: sub=%s", user_id_str)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            logger.warning("Token user is inactive: id=%s", user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive.",
            )

        return user
