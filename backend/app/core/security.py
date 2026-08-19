"""
Security Utilities
JWT token creation/validation and bcrypt password hashing.

All cryptographic operations are centralised here so they can be
independently tested and swapped without touching business logic.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt  # type: ignore[import]

from app.core.config import settings

logger = logging.getLogger(__name__)


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        plain_password: The raw password string from the user.

    Returns:
        A bcrypt-hashed string safe for database storage.
    """
    pwd_bytes = plain_password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    Args:
        plain_password: The raw password to check.
        hashed_password: The bcrypt hash retrieved from the database.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bool(bcrypt.checkpw(pwd_bytes, hash_bytes))
    except Exception as exc:
        logger.warning("Password verification failed with exception: %s", exc)
        return False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload to embed — must include a ``"sub"`` (subject) key.
        expires_delta: Custom TTL.  Defaults to ``ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    ttl = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    expire = datetime.now(tz=timezone.utc) + ttl
    to_encode.update({"exp": expire, "type": "access"})
    token: str = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug("Access token created for sub=%s", data.get("sub"))
    return token


def create_refresh_token(data: dict[str, Any]) -> str:
    """
    Create a signed JWT refresh token with a longer TTL.

    Args:
        data: Payload to embed — must include a ``"sub"`` (subject) key.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    token: str = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug("Refresh token created for sub=%s", data.get("sub"))
    return token


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Raises an ``HTTPException(401)`` instead of letting raw ``JWTError``
    propagate into route handlers.

    Args:
        token: Raw JWT string (without the ``"Bearer "`` prefix).

    Returns:
        Decoded payload dictionary.

    Raises:
        HTTPException 401: Token is expired, tampered-with, or malformed.
    """
    # Import here to avoid a circular dependency when security.py is imported
    # before the FastAPI application object is created.
    from fastapi import HTTPException, status

    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as exc:
        logger.warning("JWT decode failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
