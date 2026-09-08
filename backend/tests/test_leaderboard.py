"""Global leaderboard: ranking, points, and the caller's own standing."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.models.problem import Problem, ProblemDifficulty, UserProblemProgress
from app.models.user import User, UserRole


async def _register(client: AsyncClient, username: str, email: str) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "StrongPassword123!"},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "StrongPassword123!"}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _make_problem(db_session, difficulty: ProblemDifficulty, slug: str) -> Problem:
    problem = Problem(
        id=uuid.uuid4(),
        slug=slug,
        title=slug,
        difficulty=difficulty,
        description_md="x",
    )
    db_session.add(problem)
    await db_session.commit()
    await db_session.refresh(problem)
    return problem


async def _solve(db_session, user: User, problem: Problem) -> None:
    db_session.add(
        UserProblemProgress(
            id=uuid.uuid4(),
            user_id=user.id,
            problem_id=problem.id,
            attempts=1,
            accepted_submissions=1,
            first_solved_at=datetime.now(UTC),
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_users_with_no_solves_are_excluded(client, db_session):
    await _register(client, "newbie", "newbie@example.com")
    response = await client.get("/api/v1/leaderboard")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["items"] == []


@pytest.mark.asyncio
async def test_ranking_orders_by_points_then_solved_count(client, db_session):
    headers_hard = await _register(client, "hard_solver", "hard@example.com")
    headers_easy = await _register(client, "easy_solver", "easy@example.com")

    hard_user = (
        (await db_session.execute(User.__table__.select().where(User.username == "hard_solver")))
        .mappings()
        .first()
    )
    easy_user = (
        (await db_session.execute(User.__table__.select().where(User.username == "easy_solver")))
        .mappings()
        .first()
    )

    hard_problem = await _make_problem(db_session, ProblemDifficulty.HARD, "hard-one")
    easy_problems = [
        await _make_problem(db_session, ProblemDifficulty.EASY, f"easy-{i}") for i in range(3)
    ]

    hard_user_obj = await db_session.get(User, hard_user["id"])
    easy_user_obj = await db_session.get(User, easy_user["id"])

    await _solve(db_session, hard_user_obj, hard_problem)  # 50 points, 1 solved
    for problem in easy_problems:
        await _solve(db_session, easy_user_obj, problem)  # 30 points, 3 solved

    response = await client.get("/api/v1/leaderboard")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["username"] for item in body["items"]] == ["hard_solver", "easy_solver"]
    assert body["items"][0] == {
        "rank": 1,
        "user_id": str(hard_user["id"]),
        "username": "hard_solver",
        "full_name": None,
        "avatar_url": None,
        "solved_count": 1,
        "points": 50,
    }
    assert body["items"][1]["points"] == 30
    assert body["items"][1]["solved_count"] == 3
    assert body["items"][1]["rank"] == 2

    # 'my standing' matches the same ranking, for the caller specifically.
    mine = await client.get("/api/v1/leaderboard/me", headers=headers_easy)
    assert mine.status_code == 200
    assert mine.json() == {"rank": 2, "solved_count": 3, "points": 30}

    unranked = await client.get(
        "/api/v1/leaderboard/me", headers=await _register(client, "lurker", "lurker@example.com")
    )
    assert unranked.json() == {"rank": None, "solved_count": 0, "points": 0}

    del headers_hard  # only used to prove the account exists via registration


@pytest.mark.asyncio
async def test_pagination(client, db_session):
    headers = []
    for i in range(3):
        h = await _register(client, f"pager{i}", f"pager{i}@example.com")
        headers.append(h)

    user_rows = (
        (
            await db_session.execute(
                User.__table__.select().where(User.username.in_([f"pager{i}" for i in range(3)]))
            )
        )
        .mappings()
        .all()
    )
    problem = await _make_problem(db_session, ProblemDifficulty.EASY, "shared-easy")
    for row in user_rows:
        user_obj = await db_session.get(User, row["id"])
        await _solve(db_session, user_obj, problem)

    page1 = await client.get("/api/v1/leaderboard?offset=0&limit=2")
    page2 = await client.get("/api/v1/leaderboard?offset=2&limit=2")
    assert page1.json()["total"] == 3
    assert len(page1.json()["items"]) == 2
    assert len(page2.json()["items"]) == 1
    # Ranks are absolute, not reset per page.
    assert page2.json()["items"][0]["rank"] == 3


@pytest.mark.asyncio
async def test_admin_role_field_does_not_affect_ranking(db_session, client):
    """Sanity check the query joins on the right tables and ignores role."""
    headers = await _register(client, "admin_solver", "admin_solver@example.com")
    user_row = (
        (await db_session.execute(User.__table__.select().where(User.username == "admin_solver")))
        .mappings()
        .first()
    )
    user_obj = await db_session.get(User, user_row["id"])
    user_obj.role = UserRole.ADMIN
    await db_session.commit()

    problem = await _make_problem(db_session, ProblemDifficulty.MEDIUM, "admin-medium")
    await _solve(db_session, user_obj, problem)

    response = await client.get("/api/v1/leaderboard", headers=headers)
    body = response.json()
    assert body["items"][0]["points"] == 30
