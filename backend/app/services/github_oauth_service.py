"""
GitHub OAuth 2.0 Service
Handles state token generation/validation, token exchange with GitHub APIs,
profile fetching, and user account creation/linking logic.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, cast

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt  # type: ignore[import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.crud.user import UserCRUD
from app.schemas.auth import TokenResponse

logger = logging.getLogger(__name__)


class GitHubOAuthService:
    """Service handling GitHub OAuth 2.0 flow and user account resolution."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._crud = UserCRUD(session)

    # ------------------------------------------------------------------
    # State token management (anti-CSRF)
    # ------------------------------------------------------------------

    @staticmethod
    def generate_state_token() -> str:
        """Generate a signed JWT state token containing a random nonce."""
        nonce = secrets.token_hex(16)
        expire = datetime.now(tz=timezone.utc) + timedelta(minutes=10)
        payload = {
            "type": "oauth_state",
            "nonce": nonce,
            "exp": int(expire.timestamp()),
        }
        state_str: str = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return state_str

    @staticmethod
    def verify_state_token(state: str) -> None:
        """Verify the signature and expiration of an OAuth state token."""
        try:
            payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "oauth_state":
                raise ValueError("Invalid token type")
        except (JWTError, ValueError) as exc:
            logger.warning("OAuth state verification failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth state parameter.",
            ) from exc

    def get_authorization_url(self) -> str:
        """Construct the GitHub OAuth authorization URL."""
        if not settings.GITHUB_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub OAuth is not configured on this server.",
            )

        state = self.generate_state_token()
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            "scope": "read:user user:email",
            "state": state,
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://github.com/login/oauth/authorize?{query_string}"

    # ------------------------------------------------------------------
    # GitHub API Communication & Authentication
    # ------------------------------------------------------------------

    async def exchange_code_for_token(self, code: str) -> str:
        """Exchange authorization code for a GitHub access token."""
        url = "https://github.com/login/oauth/access_token"
        headers = {"Accept": "application/json"}
        data = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, data=data)

        if resp.status_code != 200:
            logger.error("GitHub token exchange failed: HTTP %s", resp.status_code)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code with GitHub.",
            )

        body = resp.json()
        access_token = body.get("access_token")
        if not access_token:
            error_desc = body.get("error_description", "Unknown error")
            logger.error("GitHub token exchange error: %s", error_desc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub OAuth error: {error_desc}",
            )

        return str(access_token)

    async def fetch_github_user_info(self, access_token: str) -> dict[str, Any]:
        """Fetch profile and primary verified email from GitHub API."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeForge-AI-Backend",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            user_resp = await client.get("https://api.github.com/user", headers=headers)
            if user_resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch GitHub user profile.",
                )
            user_data = cast(dict[str, Any], user_resp.json())

            email = user_data.get("email")
            if not email:
                email_resp = await client.get("https://api.github.com/user/emails", headers=headers)
                if email_resp.status_code == 200:
                    emails = email_resp.json()
                    for item in emails:
                        if item.get("primary") and item.get("verified"):
                            email = item.get("email")
                            break

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub account must have a verified primary email address.",
            )

        user_data["primary_email"] = email
        return user_data

    async def handle_callback(self, code: str, state: str) -> TokenResponse:
        """Full callback flow: verify state, exchange code, link/create user, issue JWTs."""
        self.verify_state_token(state)
        github_token = await self.exchange_code_for_token(code)
        gh_user = await self.fetch_github_user_info(github_token)

        github_id = str(gh_user["id"])
        github_username = str(gh_user.get("login", ""))
        email = str(gh_user["primary_email"])
        name = gh_user.get("name")
        avatar_url = gh_user.get("avatar_url")

        # 1. Check if user already exists by GitHub ID
        user = await self._crud.get_by_github_id(github_id)

        # 2. If not, check if user exists by verified email (account linking)
        if user is None:
            user = await self._crud.get_by_email(email)
            if user is not None:
                user = await self._crud.update(
                    user,
                    github_id=github_id,
                    github_username=github_username,
                    is_verified=True,
                )
                logger.info("Linked GitHub account to existing user: id=%s", user.id)

        # 3. If still not found, create new OAuth user
        if user is None:
            base_username = github_username if github_username else email.split("@")[0]
            candidate_username = base_username
            counter = 1
            while await self._crud.get_by_username(candidate_username) is not None:
                candidate_username = f"{base_username}_{counter}"
                counter += 1

            user = await self._crud.create_oauth_user(
                username=candidate_username,
                email=email,
                github_id=github_id,
                github_username=github_username,
                full_name=name,
                avatar_url=avatar_url,
            )
            logger.info("Created new user via GitHub OAuth: id=%s", user.id)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive.",
            )

        token_payload = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
