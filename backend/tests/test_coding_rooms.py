"""Coding-room REST authorization and collaboration state tests."""

from typing import cast

import pytest
from fastapi import WebSocket
from httpx import AsyncClient

from app.websocket.coding_rooms import RoomConnectionManager


class _Socket:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        self.messages.append(payload)


async def _headers(client: AsyncClient, username: str, email: str) -> dict[str, str]:
    password = "StrongPassword123!"
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert response.status_code == 201
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_public_room_join_and_owner_membership_controls(client: AsyncClient) -> None:
    owner = await _headers(client, "roomowner", "roomowner@example.com")
    member = await _headers(client, "roommember", "roommember@example.com")
    created = await client.post(
        "/api/v1/rooms/",
        json={"title": "Public pair session", "is_public": True, "document": {"code": "x = 1"}},
        headers=owner,
    )
    assert created.status_code == 201
    room = created.json()
    assert room["version"] == 0

    joined = await client.post(f"/api/v1/rooms/{room['id']}/join", headers=member)
    assert joined.status_code == 200
    assert joined.json()["role"] == "editor"

    non_owner = await client.patch(
        f"/api/v1/rooms/{room['id']}", json={"title": "Not owner"}, headers=member
    )
    assert non_owner.status_code == 403


@pytest.mark.asyncio
async def test_private_room_requires_invitation_and_owner_can_add_member(
    client: AsyncClient,
) -> None:
    owner = await _headers(client, "privateowner", "privateowner@example.com")
    invitee = await _headers(client, "invitee", "invitee@example.com")
    room = (
        await client.post("/api/v1/rooms/", json={"title": "Private room"}, headers=owner)
    ).json()

    assert (await client.get(f"/api/v1/rooms/{room['id']}")).status_code == 403
    assert (
        await client.post(f"/api/v1/rooms/{room['id']}/join", headers=invitee)
    ).status_code == 403

    me = await client.get("/api/v1/users/me", headers=invitee)
    added = await client.post(
        f"/api/v1/rooms/{room['id']}/members",
        json={"user_id": me.json()["id"], "role": "viewer"},
        headers=owner,
    )
    assert added.status_code == 201
    assert (await client.get(f"/api/v1/rooms/{room['id']}", headers=invitee)).status_code == 200


@pytest.mark.asyncio
async def test_owner_cannot_leave_room(client: AsyncClient) -> None:
    owner = await _headers(client, "leaveowner", "leaveowner@example.com")
    room = (await client.post("/api/v1/rooms/", json={"title": "Owner room"}, headers=owner)).json()
    response = await client.delete(f"/api/v1/rooms/{room['id']}/members/me", headers=owner)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_websocket_manager_broadcast_excludes_event_sender() -> None:
    manager = RoomConnectionManager()
    sender, peer = _Socket(), _Socket()
    # _Socket duck-types WebSocket (it only needs send_json); cast for mypy.
    sender_ws, peer_ws = cast(WebSocket, sender), cast(WebSocket, peer)
    manager.connections["room"].update({sender_ws, peer_ws})
    await manager._broadcast("room", {"type": "cursor_update"}, exclude=sender_ws)  # noqa: SLF001
    assert sender.messages == []
    assert peer.messages == [{"type": "cursor_update"}]
