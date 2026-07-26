"""
User profile and RBAC endpoint tests.
"""

import pytest
from httpx import AsyncClient

from app.models.user import UserRole

REGISTER_PAYLOAD = {
    "username": "profileuser",
    "email": "profile@example.com",
    "password": "Password123!",
    "full_name": "Profile User",
}


async def _get_auth_headers(client: AsyncClient, payload: dict = REGISTER_PAYLOAD) -> dict:
    """Register a user, login, and return Bearer auth headers."""
    await client.post("/api/v1/auth/register", json=payload)
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_my_profile(client: AsyncClient):
    """GET /users/me returns authenticated profile."""
    headers = await _get_auth_headers(client)
    resp = await client.get("/api/v1/users/me", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == REGISTER_PAYLOAD["email"]
    assert body["role"] == "user"


@pytest.mark.asyncio
async def test_update_my_profile(client: AsyncClient):
    """PATCH /users/me updates full_name and bio."""
    headers = await _get_auth_headers(client)
    patch_data = {"full_name": "Updated Name", "bio": "Software Architect"}
    resp = await client.patch("/api/v1/users/me", json=patch_data, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Updated Name"
    assert body["bio"] == "Software Architect"


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient):
    """PUT /users/me/password updates password when current password is correct."""
    headers = await _get_auth_headers(client)
    change_payload = {
        "current_password": REGISTER_PAYLOAD["password"],
        "new_password": "NewStrongPassword1!",
    }
    resp = await client.put("/api/v1/users/me/password", json=change_payload, headers=headers)
    assert resp.status_code == 200

    # Verify login with new password
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "NewStrongPassword1!"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient):
    """PUT /users/me/password returns 400 when current password is wrong."""
    headers = await _get_auth_headers(client)
    change_payload = {
        "current_password": "WrongPassword1!",
        "new_password": "NewStrongPassword1!",
    }
    resp = await client.put("/api/v1/users/me/password", json=change_payload, headers=headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_admin_endpoints_access_control(client: AsyncClient, db_session):
    """Regular users must get 403 on admin routes; Admin users get 200."""
    user_headers = await _get_auth_headers(client)

    # 1. Regular user gets 403
    resp = await client.get("/api/v1/admin/users", headers=user_headers)
    assert resp.status_code == 403

    # 2. Promote user to admin directly in DB for testing
    from app.crud.user import UserCRUD

    crud = UserCRUD(db_session)
    user = await crud.get_by_email(REGISTER_PAYLOAD["email"])
    assert user is not None
    await crud.update(user, role=UserRole.ADMIN)

    # Re-login to ensure active admin status is checked
    admin_headers = await _get_auth_headers(client)
    admin_resp = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert admin_resp.status_code == 200
    body = admin_resp.json()
    assert "items" in body
    assert body["total"] >= 1
