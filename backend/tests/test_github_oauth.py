"""
GitHub OAuth flow and callback unit tests.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.services.github_oauth_service import GitHubOAuthService


@pytest.mark.asyncio
async def test_github_login_redirect(client: AsyncClient):
    """GET /auth/github/login returns 302 redirect or 503 if client ID unconfigured."""
    with patch.object(settings, "GITHUB_CLIENT_ID", "mock_client_id"):
        resp = await client.get("/api/v1/auth/github/login", follow_redirects=False)
        assert resp.status_code == 302
        redirect_url = resp.headers["location"]
        assert "github.com/login/oauth/authorize" in redirect_url
        assert "client_id=mock_client_id" in redirect_url
        assert "state=" in redirect_url


@pytest.mark.asyncio
async def test_github_state_token_validation():
    """State tokens must verify signature and type."""
    token = GitHubOAuthService.generate_state_token()
    assert token is not None
    # Should not raise exception
    GitHubOAuthService.verify_state_token(token)


@pytest.mark.asyncio
async def test_github_oauth_callback_creates_new_user(client: AsyncClient):
    """Callback creates new user when GitHub account does not exist."""
    state = GitHubOAuthService.generate_state_token()

    mock_profile = {
        "id": 998877,
        "login": "octocat",
        "primary_email": "octocat@github.com",
        "name": "Mona Lisa Octocat",
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
    }

    with (
        patch.object(settings, "GITHUB_CLIENT_ID", "mock_id"),
        patch.object(settings, "GITHUB_CLIENT_SECRET", "mock_secret"),
        patch.object(
            GitHubOAuthService, "exchange_code_for_token", new_callable=AsyncMock
        ) as mock_exchange,
        patch.object(
            GitHubOAuthService, "fetch_github_user_info", new_callable=AsyncMock
        ) as mock_info,
    ):

        mock_exchange.return_value = "gho_mockaccesstoken123"
        mock_info.return_value = mock_profile

        resp = await client.get(
            "/api/v1/auth/github/callback",
            params={"code": "valid_code", "state": state},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

        # Verify user profile was created
        me_resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {body['access_token']}"},
        )
        assert me_resp.status_code == 200
        me_body = me_resp.json()
        assert me_body["email"] == "octocat@github.com"
        assert me_body["github_username"] == "octocat"
        assert me_body["is_verified"] is True
