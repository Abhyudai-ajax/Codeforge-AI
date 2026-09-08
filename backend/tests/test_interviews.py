"""Tests for Mock Interview System."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def get_auth_headers(client: AsyncClient, username: str = "interviewuser") -> dict[str, str]:
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
async def test_start_and_complete_interview_session(client: AsyncClient):
    headers = await get_auth_headers(client, "interview_user1")

    # 1. Start Session
    res_start = await client.post(
        "/api/v1/interviews/sessions",
        headers=headers,
        json={"type": "dsa", "title": "System Design & DSA Mock", "time_limit_minutes": 60},
    )
    assert res_start.status_code == 201
    session_data = res_start.json()
    session_id = session_data["id"]
    assert session_data["status"] == "in_progress"

    # 2. List sessions
    res_list = await client.get("/api/v1/interviews/sessions/me", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 3. Answer question if any questions generated
    if session_data["questions"]:
        q_id = session_data["questions"][0]["id"]
        res_ans = await client.post(
            f"/api/v1/interviews/sessions/{session_id}/answer",
            headers=headers,
            json={"question_id": q_id, "answer_text": "I would use a HashMap with linear probing."},
        )
        assert res_ans.status_code == 200

    # 4. Finish Session
    res_finish = await client.post(
        f"/api/v1/interviews/sessions/{session_id}/finish",
        headers=headers,
    )
    assert res_finish.status_code == 200
    finish_data = res_finish.json()
    assert finish_data["status"] == "completed"
    assert finish_data["feedback"] is not None
    assert finish_data["feedback"]["summary_md"] != ""

    # 5. Get Feedback
    res_fb = await client.get(
        f"/api/v1/interviews/sessions/{session_id}/feedback",
        headers=headers,
    )
    assert res_fb.status_code == 200
    assert "overall_score" in res_fb.json()
