"""Tests for Notification System."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationType
from app.services.notification_service import notification_service


async def get_auth_headers(client: AsyncClient, username: str = "notifuser") -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "Password123!"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": f"{username}@example.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_notification_lifecycle(client: AsyncClient, db_session: AsyncSession):
    headers = await get_auth_headers(client, "notif_user1")

    # Get user details from /me to obtain user_id
    me_res = await client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    user_id = me_res.json()["id"]

    # Emit notification
    import uuid

    notif = await notification_service.notify_user(
        db_session,
        user_id=uuid.UUID(user_id),
        type=NotificationType.CONTEST_REGISTERED,
        title="Registered for Weekly Contest #1",
        message="You are successfully registered for the contest.",
    )

    # 1. Unread count
    res_count = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert res_count.status_code == 200
    assert res_count.json()["unread_count"] >= 1

    # 2. List notifications
    res_list = await client.get("/api/v1/notifications/", headers=headers)
    assert res_list.status_code == 200
    data = res_list.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Registered for Weekly Contest #1"

    # 3. Mark single as read
    res_read = await client.patch(f"/api/v1/notifications/{notif.id}/read", headers=headers)
    assert res_read.status_code == 200
    assert res_read.json()["is_read"] is True

    # 4. Delete notification
    res_del = await client.delete(f"/api/v1/notifications/{notif.id}", headers=headers)
    assert res_del.status_code == 204
