"""Comprehensive test suite for Contests & Leaderboards."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.problem import Problem, ProblemDifficulty, TestCase
from app.models.user import User, UserRole
from app.workers.sandbox import SandboxResult


async def _register_user(client: AsyncClient, username: str, role: str = "user") -> dict[str, str]:
    email = f"{username}@example.com"
    pwd = "StrongPassword123!"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": pwd},
    )
    user_id = reg_resp.json()["id"]

    if role == "admin":
        from sqlalchemy import update

        from app.models.user import User
        from tests.conftest import _TestSessionLocal

        async with _TestSessionLocal() as session:
            await session.execute(
                update(User).where(User.id == uuid.UUID(user_id)).values(role=UserRole.ADMIN)
            )
            await session.commit()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": pwd},
    )
    return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_contest_admin_crud_and_registration(client: AsyncClient, db_session) -> None:
    admin_headers = await _register_user(client, "admin_user", role="admin")
    user_headers = await _register_user(client, "normal_user")

    # 1. Admin creates contest
    now = datetime.now(UTC)
    start = now + timedelta(hours=1)
    end = now + timedelta(hours=3)

    create_resp = await client.post(
        "/api/v1/contests",
        json={
            "title": "CodeForge Weekly 101",
            "slug": "weekly-101",
            "description_md": "Weekly contest #101",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "is_published": True,
            "problems": [],
        },
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    contest = create_resp.json()
    contest_id = contest["id"]
    assert contest["status"] == "upcoming"

    # Non-admin cannot create contest
    fail_create = await client.post(
        "/api/v1/contests",
        json={
            "title": "Hacker Contest",
            "slug": "hacker-contest",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
        headers=user_headers,
    )
    assert fail_create.status_code == 403

    # 2. User registers for upcoming contest
    reg_resp = await client.post(f"/api/v1/contests/{contest_id}/register", headers=user_headers)
    assert reg_resp.status_code == 200
    assert reg_resp.json()["message"] == "Successfully registered for contest."

    # Verify registration state in contest detail
    detail = await client.get(f"/api/v1/contests/{contest_id}", headers=user_headers)
    assert detail.status_code == 200
    assert detail.json()["is_registered"] is True
    assert detail.json()["participant_count"] == 1

    # 3. User unregisters
    unreg_resp = await client.post(
        f"/api/v1/contests/{contest_id}/unregister", headers=user_headers
    )
    assert unreg_resp.status_code == 200

    detail_after = await client.get(f"/api/v1/contests/{contest_id}", headers=user_headers)
    assert detail_after.json()["is_registered"] is False
    assert detail_after.json()["participant_count"] == 0

    # Re-register
    await client.post(f"/api/v1/contests/{contest_id}/register", headers=user_headers)

    # 4. Admin updates contest
    patch_resp = await client.patch(
        f"/api/v1/contests/{contest_id}",
        json={"title": "CodeForge Weekly 101 (Updated)"},
        headers=admin_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "CodeForge Weekly 101 (Updated)"


@pytest.mark.asyncio
async def test_problem_gating_and_contest_submission(client: AsyncClient, db_session) -> None:
    admin_headers = await _register_user(client, "contest_admin", role="admin")
    user_headers = await _register_user(client, "contest_player")

    # Create problem
    problem = Problem(
        id=uuid.uuid4(),
        slug="contest-prob-1",
        title="Contest Problem 1",
        difficulty=ProblemDifficulty.EASY,
        description_md="Description for contest problem 1",
        supported_languages=["python"],
    )
    problem.test_cases = [
        TestCase(input_data="5\n", expected_output="5\n", is_public=True, order=1),
        TestCase(input_data="10\n", expected_output="10\n", is_public=False, order=2),
    ]
    db_session.add(problem)
    await db_session.commit()

    # Create running contest
    now = datetime.now(UTC)
    start = now - timedelta(minutes=10)
    end = now + timedelta(hours=2)

    c_resp = await client.post(
        "/api/v1/contests",
        json={
            "title": "Active Sprint",
            "slug": "active-sprint",
            "description_md": "Running contest",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "is_published": True,
            "problems": [
                {
                    "problem_id": str(problem.id),
                    "order": 0,
                    "points": 100,
                    "label": "A",
                }
            ],
        },
        headers=admin_headers,
    )
    contest_id = c_resp.json()["id"]

    # Register user
    await client.post(f"/api/v1/contests/{contest_id}/register", headers=user_headers)

    # Problem details ARE accessible to user since contest is running
    detail = await client.get(f"/api/v1/contests/{contest_id}", headers=user_headers)
    assert detail.status_code == 200
    prob_item = detail.json()["problems"][0]
    assert prob_item["label"] == "A"
    assert prob_item["problem"]["title"] == "Contest Problem 1"

    # User submits for contest problem
    with patch("app.workers.submission.judge_submission.delay"):
        sub_resp = await client.post(
            f"/api/v1/contests/{contest_id}/submissions",
            json={
                "problem_id": str(problem.id),
                "language": "python",
                "source_code": "import sys\nprint(sys.stdin.read().strip())",
            },
            headers=user_headers,
        )
        assert sub_resp.status_code == 202
        sub_id = sub_resp.json()["id"]

    # Execute judge worker and score update
    from app.services.contest_service import ContestService
    from app.workers.submission import _judge
    from tests.conftest import _TestSessionLocal

    with (
        patch("app.workers.submission.AsyncSessionLocal", _TestSessionLocal),
        patch("app.workers.submission.run_source") as mock_run,
    ):
        mock_run.side_effect = [
            SandboxResult(stdout="5\n", stderr="", exit_code=0),
            SandboxResult(stdout="10\n", stderr="", exit_code=0),
        ]
        await _judge(sub_id)

    # Trigger contest score processing
    async with _TestSessionLocal() as session:
        from app.crud.problem import ProblemRepository

        sub_obj = await ProblemRepository(session).submission(uuid.UUID(sub_id))
        user_obj = (
            await session.execute(select(User).where(User.email == "contest_player@example.com"))
        ).scalar_one()
        assert sub_obj is not None
        await ContestService(session).process_submission_score(
            uuid.UUID(contest_id), user_obj.id, problem.id, sub_obj
        )

    # Check Leaderboard
    lb_resp = await client.get(f"/api/v1/contests/{contest_id}/leaderboard")
    assert lb_resp.status_code == 200
    lb_data = lb_resp.json()
    assert lb_data["total"] == 1
    top_entry = lb_data["items"][0]
    assert top_entry["username"] == "contest_player"
    assert top_entry["total_score"] == 100
    assert top_entry["problems_solved"] == 1

    # Check User Contest History
    hist_resp = await client.get("/api/v1/contests/my-history", headers=user_headers)
    assert hist_resp.status_code == 200
    hist_items = hist_resp.json()
    assert len(hist_items) == 1
    assert hist_items[0]["title"] == "Active Sprint"
    assert hist_items[0]["rank"] == 1
    assert hist_items[0]["total_score"] == 100
