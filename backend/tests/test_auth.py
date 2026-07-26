"""
Authentication endpoint tests.

All tests use the in-memory SQLite fixture from conftest.py so no live
database is required.  The ``client`` fixture provides an AsyncClient
with the test DB injected via dependency override.
"""

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------
REGISTER_PAYLOAD = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "Str0ng!Pass",
    "full_name": "Test User",
}

LOGIN_PAYLOAD = {
    "email": "testuser@example.com",
    "password": "Str0ng!Pass",
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


async def _register_user(client: AsyncClient, payload: dict = REGISTER_PAYLOAD) -> dict:
    """Register a user and assert success, returning the JSON body."""
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """
    A valid registration request should return 201 with the user profile.
    The response must never include the hashed password.
    """
    body = await _register_user(client)

    assert body["username"] == REGISTER_PAYLOAD["username"]
    assert body["email"] == REGISTER_PAYLOAD["email"]
    assert body["full_name"] == REGISTER_PAYLOAD["full_name"]
    assert body["is_active"] is True
    # Ensure hashed_password is NOT leaked in any form
    assert "password" not in body
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """
    Attempting to register a second account with the same email must return 409.
    """
    await _register_user(client)

    duplicate = {**REGISTER_PAYLOAD, "username": "different_user"}
    response = await client.post("/api/v1/auth/register", json=duplicate)

    assert response.status_code == 409
    assert "email" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """
    Attempting to register a second account with the same username must return 409.
    """
    await _register_user(client)

    duplicate = {**REGISTER_PAYLOAD, "email": "other@example.com"}
    response = await client.post("/api/v1/auth/register", json=duplicate)

    assert response.status_code == 409
    assert "username" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_password_too_short(client: AsyncClient):
    """Passwords shorter than 8 characters must be rejected with 422."""
    payload = {
        **REGISTER_PAYLOAD,
        "username": "shortpw",
        "email": "short@example.com",
        "password": "abc",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """
    Valid credentials should return 200 with access_token, refresh_token,
    token_type, and expires_in.
    """
    await _register_user(client)

    response = await client.post("/api/v1/auth/login", json=LOGIN_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert isinstance(body["expires_in"], int)
    assert body["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Wrong password must return 401 with a generic error (no user enumeration)."""
    await _register_user(client)

    bad_payload = {**LOGIN_PAYLOAD, "password": "WrongPass1"}
    response = await client.post("/api/v1/auth/login", json=bad_payload)

    assert response.status_code == 401
    body = response.json()
    # Error message must NOT reveal whether the email exists
    assert "email or password" in body["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    """Login with an email that has never been registered must return 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "Str0ng!Pass"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# /me — protected endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient):
    """
    A valid Bearer token must allow access to GET /me and return the
    user profile without the hashed password.
    """
    await _register_user(client)
    login_resp = await client.post("/api/v1/auth/login", json=LOGIN_PAYLOAD)
    access_token = login_resp.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == LOGIN_PAYLOAD["email"]
    assert "hashed_password" not in body
    assert "password" not in body


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    """Accessing /me without a token must return 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(client: AsyncClient):
    """Accessing /me with a tampered / invalid token must return 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
    )
    assert response.status_code == 401
