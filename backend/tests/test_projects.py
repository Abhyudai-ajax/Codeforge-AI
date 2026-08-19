"""
Project management endpoint tests.
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from httpx import AsyncClient

PROJECT_CREATE_PAYLOAD = {
    "title": "CodeForge Backend",
    "description": "A backend project for CodeForge AI.",
    "language": "python",
    "visibility": "private",
    "github_repo": "https://github.com/codeforge-ai/backend",
    "github_branch": "main",
}

PUBLIC_PROJECT_PAYLOAD = {
    "title": "Open Source Library",
    "description": "A public library for everyone.",
    "language": "python",
    "visibility": "public",
    "github_repo": "https://github.com/codeforge-ai/library",
    "github_branch": "main",
}

REGISTER_PAYLOAD = {
    "username": "projectuser",
    "email": "projectuser@example.com",
    "password": "StrongPass123!",
    "full_name": "Project User",
}

SECOND_USER_PAYLOAD = {
    "username": "seconduser",
    "email": "seconduser@example.com",
    "password": "StrongPass456!",
    "full_name": "Second User",
}


async def _get_auth_headers(client: AsyncClient, payload: dict[str, str]) -> dict[str, str]:
    await client.post("/api/v1/auth/register", json=payload)
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_project(
    client: AsyncClient, headers: dict[str, str], payload: dict[str, str]
) -> dict[str, Any]:
    resp = await client.post("/api/v1/projects/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return cast(dict[str, Any], resp.json())


@pytest.mark.asyncio
async def test_create_project_success(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, REGISTER_PAYLOAD)
    body = await _create_project(client, headers, PROJECT_CREATE_PAYLOAD)

    assert body["title"] == PROJECT_CREATE_PAYLOAD["title"]
    assert body["visibility"] == PROJECT_CREATE_PAYLOAD["visibility"]
    assert body["github_repo"] == PROJECT_CREATE_PAYLOAD["github_repo"]
    assert body["stars"] == 0
    assert body["forks"] == 0
    assert body["views"] == 0
    assert body["owner_id"] is not None


@pytest.mark.asyncio
async def test_list_my_projects_pagination(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, REGISTER_PAYLOAD)

    for index in range(3):
        payload = {**PROJECT_CREATE_PAYLOAD, "title": f"Project {index+1}"}
        await _create_project(client, headers, payload)

    response = await client.get("/api/v1/projects/?skip=1&limit=1", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["skip"] == 1
    assert body["limit"] == 1
    assert len(body["items"]) == 1


@pytest.mark.asyncio
async def test_public_project_listing_and_search(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, REGISTER_PAYLOAD)
    await _create_project(client, headers, PROJECT_CREATE_PAYLOAD)
    public_project = await _create_project(client, headers, PUBLIC_PROJECT_PAYLOAD)

    public_resp = await client.get("/api/v1/projects/public?skip=0&limit=20")
    assert public_resp.status_code == 200
    public_body = public_resp.json()
    assert public_body["total"] >= 1
    assert any(item["id"] == public_project["id"] for item in public_body["items"])
    assert all(item["visibility"] == "public" for item in public_body["items"])

    search_resp = await client.get("/api/v1/projects/search?query=Open&skip=0&limit=20")
    assert search_resp.status_code == 200
    search_body = search_resp.json()
    assert search_body["total"] >= 1
    assert any(item["id"] == public_project["id"] for item in search_body["items"])


@pytest.mark.asyncio
async def test_get_project_access_control(client: AsyncClient) -> None:
    owner_headers = await _get_auth_headers(client, REGISTER_PAYLOAD)
    project = await _create_project(client, owner_headers, PUBLIC_PROJECT_PAYLOAD)

    # Public project accessible without auth
    public_resp = await client.get(f"/api/v1/projects/{project['id']}")
    assert public_resp.status_code == 200

    # Private project accessible only to owner
    private_project = await _create_project(client, owner_headers, PROJECT_CREATE_PAYLOAD)
    unauth_resp = await client.get(f"/api/v1/projects/{private_project['id']}")
    assert unauth_resp.status_code == 403

    second_headers = await _get_auth_headers(client, SECOND_USER_PAYLOAD)
    other_resp = await client.get(
        f"/api/v1/projects/{private_project['id']}", headers=second_headers
    )
    assert other_resp.status_code == 403

    owner_resp = await client.get(
        f"/api/v1/projects/{private_project['id']}", headers=owner_headers
    )
    assert owner_resp.status_code == 200


@pytest.mark.asyncio
async def test_update_delete_restore_project(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, REGISTER_PAYLOAD)
    project = await _create_project(client, headers, PROJECT_CREATE_PAYLOAD)
    project_id = project["id"]

    update_payload = {"title": "Updated Backend Project", "visibility": "public"}
    update_resp = await client.patch(
        f"/api/v1/projects/{project_id}", json=update_payload, headers=headers
    )
    assert update_resp.status_code == 200
    updated_body = update_resp.json()
    assert updated_body["title"] == "Updated Backend Project"
    assert updated_body["visibility"] == "public"

    delete_resp = await client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["message"] == "Project deleted successfully."

    # Deleted project no longer accessible
    get_deleted_resp = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_deleted_resp.status_code == 404

    restore_resp = await client.post(f"/api/v1/projects/{project_id}/restore", headers=headers)
    assert restore_resp.status_code == 200
    restored_body = restore_resp.json()
    assert restored_body["id"] == project_id
    assert restored_body["visibility"] == "public"


@pytest.mark.asyncio
async def test_project_ownership_denied_on_update_delete_restore(client: AsyncClient) -> None:
    owner_headers = await _get_auth_headers(client, REGISTER_PAYLOAD)
    project = await _create_project(client, owner_headers, PROJECT_CREATE_PAYLOAD)
    project_id = project["id"]

    other_headers = await _get_auth_headers(client, SECOND_USER_PAYLOAD)

    update_resp = await client.patch(
        f"/api/v1/projects/{project_id}", json={"title": "Hacked"}, headers=other_headers
    )
    assert update_resp.status_code == 404

    delete_resp = await client.delete(f"/api/v1/projects/{project_id}", headers=other_headers)
    assert delete_resp.status_code == 404

    restore_resp = await client.post(
        f"/api/v1/projects/{project_id}/restore", headers=other_headers
    )
    assert restore_resp.status_code == 404
