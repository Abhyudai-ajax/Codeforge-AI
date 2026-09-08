"""Problem-scoped AI assistance and the language filter it relies on."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.models.problem import Problem, ProblemDifficulty


async def _auth_headers(client: AsyncClient, username: str, email: str) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "StrongPassword123!"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _seed_problem(db_session) -> Problem:
    problem = Problem(
        id=uuid.uuid4(),
        slug="ai-two-sum",
        title="AI Two Sum",
        difficulty=ProblemDifficulty.EASY,
        description_md="Find the two indices that sum to the target.",
        input_description="Line 1: n and target.",
        output_description="Two indices.",
        constraints=["2 <= n <= 10000"],
        supported_languages=["python", "c", "cpp"],
    )
    db_session.add(problem)
    await db_session.commit()
    return problem


@pytest.mark.asyncio
async def test_hint_requires_authentication(client, db_session):
    problem = await _seed_problem(db_session)
    response = await client.post(f"/api/v1/problems/{problem.id}/ai/hint", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_hint_works_with_an_empty_editor(client, db_session):
    problem = await _seed_problem(db_session)
    headers = await _auth_headers(client, "hinter", "hinter@example.com")

    response = await client.post(f"/api/v1/problems/{problem.id}/ai/hint", json={}, headers=headers)
    assert response.status_code == 200
    assert response.json()["result"].strip()


@pytest.mark.asyncio
async def test_hint_accepts_c_source_from_the_editor(client, db_session):
    problem = await _seed_problem(db_session)
    headers = await _auth_headers(client, "c_dev", "c_dev@example.com")

    response = await client.post(
        f"/api/v1/problems/{problem.id}/ai/hint",
        json={"code": "#include <stdio.h>\nint main(void){return 0;}", "language": "C"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["result"].strip()


@pytest.mark.asyncio
async def test_review_rejects_an_empty_submission(client, db_session):
    problem = await _seed_problem(db_session)
    headers = await _auth_headers(client, "reviewer", "reviewer@example.com")

    response = await client.post(
        f"/api/v1/problems/{problem.id}/ai/review", json={}, headers=headers
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ai_routes_404_for_unknown_problem(client, db_session):
    headers = await _auth_headers(client, "ghost", "ghost@example.com")
    response = await client.post(
        f"/api/v1/problems/{uuid.uuid4()}/ai/explain", json={}, headers=headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_language_filter_matches_exact_ids(client, db_session):
    await _seed_problem(db_session)

    # 'c' must not be matched by the substring of 'cpp'.
    assert (await client.get("/api/v1/problems?language=c")).json()["total"] == 1
    assert (await client.get("/api/v1/problems?language=cpp")).json()["total"] == 1
    assert (await client.get("/api/v1/problems?language=C%2B%2B")).json()["total"] == 1
    # This problem does not offer Java, and 'java' must not match 'javascript'.
    assert (await client.get("/api/v1/problems?language=java")).json()["total"] == 0
    assert (await client.get("/api/v1/problems?language=javascript")).json()["total"] == 0


@pytest.mark.asyncio
async def test_unknown_language_filter_returns_nothing(client, db_session):
    await _seed_problem(db_session)
    response = await client.get("/api/v1/problems?language=cobol")
    assert response.status_code == 200
    assert response.json()["total"] == 0
