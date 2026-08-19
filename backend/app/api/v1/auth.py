"""
Authentication API Routes
POST /auth/register — create a new account
POST /auth/login    — authenticate and receive JWT tokens
GET  /auth/me       — fetch the currently authenticated user's profile

Routes are intentionally thin.  All business logic lives in AuthService.
"""

import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import RegisterRequest, RegisterResponse, UserResponse
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description=(
        "Create a new user account.\n\n"
        "- Validates that the email and username are not already taken.\n"
        "- Hashes the password with bcrypt before persisting.\n"
        "- Returns the public user profile — **never** exposes the hashed password."
    ),
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """Register a new user and return their public profile."""
    service = AuthService(db)
    user = await service.register(payload)
    logger.info("register endpoint: user created id=%s", user.id)
    return RegisterResponse.model_validate(user)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain JWT tokens",
    description=(
        "Authenticate with **email** + **password**.\n\n"
        "On success, returns:\n"
        "- `access_token` — short-lived JWT (include as `Authorization: Bearer <token>`).\n"
        "- `refresh_token` — long-lived JWT for obtaining new access tokens.\n"
        "- `expires_in` — access token TTL in **seconds**."
    ),
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email + password and return JWT tokens."""
    service = AuthService(db)
    tokens = await service.login(payload)
    logger.info("login endpoint: tokens issued")
    return tokens


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
    description="Return the authenticated user's profile details.",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Return the authenticated user's public profile."""
    return UserResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# GitHub OAuth
# ---------------------------------------------------------------------------


@router.get(
    "/github/login",
    summary="Initiate GitHub OAuth login flow",
    description="Redirects user to GitHub OAuth authorize page with a signed anti-CSRF state token.",
)
async def github_login(
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Redirect to GitHub OAuth authorization URL."""
    from fastapi.responses import RedirectResponse

    from app.services.github_oauth_service import GitHubOAuthService

    service = GitHubOAuthService(db)
    auth_url = service.get_authorization_url()
    return RedirectResponse(url=auth_url, status_code=302)


@router.get(
    "/github/callback",
    response_model=TokenResponse,
    summary="GitHub OAuth callback endpoint",
    description="Receives code & state, verifies state token, exchanges code for access token, and issues JWT tokens.",
)
async def github_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Handle GitHub OAuth callback and issue JWT tokens."""
    from app.services.github_oauth_service import GitHubOAuthService

    service = GitHubOAuthService(db)
    return await service.handle_callback(code=code, state=state)
