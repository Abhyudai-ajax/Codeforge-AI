"""
Authentication FastAPI Dependencies.

These callables are injected via ``Depends()`` in route handlers.
They decode the Bearer token, validate it, and surface a fully hydrated
``User`` ORM instance.  Separating them from the service layer makes
mocking trivial in tests.
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OAuth2 schemes
# ---------------------------------------------------------------------------
# Points to the login URL so Swagger UI's "Authorize" button works correctly.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: decode the Bearer token and return the User.

    Decodes the JWT, extracts the ``sub`` (user UUID), then fetches the
    live user record from the database.

    Args:
        token: JWT Bearer token automatically extracted by
               :class:`~fastapi.security.OAuth2PasswordBearer`.
        db:    Async database session from :func:`~app.core.database.get_db`.

    Returns:
        The :class:`~app.models.user.User` ORM instance for the token owner.

    Raises:
        HTTPException 401: Token is invalid/expired or ``sub`` is missing.
        HTTPException 403: User account is inactive.
    """
    payload = decode_token(token)

    sub: str | None = payload.get("sub")
    if sub is None:
        logger.warning("JWT payload missing required 'sub' claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    service = AuthService(db)
    return await service.get_user_by_id(sub)


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Optional authentication dependency for public endpoints."""
    if not token:
        return None

    try:
        payload = decode_token(token)
    except HTTPException:
        return None

    sub: str | None = payload.get("sub")
    if sub is None:
        return None

    service = AuthService(db)
    try:
        return await service.get_user_by_id(sub)
    except HTTPException:
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency: ``get_current_user`` plus an active-status guard.

    Prefer this dependency in endpoints that must reject deactivated accounts
    even if a valid token exists (tokens outlive account deactivation).

    Args:
        current_user: Injected by :func:`get_current_user`.

    Returns:
        The active :class:`~app.models.user.User` instance.

    Raises:
        HTTPException 403: Account has been deactivated.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )
    return current_user


def require_role(*allowed_roles: str):
    """
    FastAPI dependency factory enforcing Role-Based Access Control (RBAC).

    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_role("admin"))])

    Args:
        *allowed_roles: String role names allowed to access the endpoint.
    """

    async def _role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        user_role_val = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )
        if user_role_val not in allowed_roles:
            logger.warning(
                "Access denied for user id=%s role=%s — required roles=%s",
                current_user.id,
                user_role_val,
                allowed_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return _role_checker
