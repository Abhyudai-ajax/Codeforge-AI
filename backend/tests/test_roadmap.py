"""Tests for Roadmap and Recommendation System."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.problem import Problem, ProblemDifficulty
from app.models.roadmap import Roadmap, RoadmapStage, RoadmapStageProblem


async def get_auth_headers(client: AsyncClient, username: str = "rmuser") -> dict[str, str]:
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


@pytest.fixture
async def sample_roadmap_data(db_session: AsyncSession) -> Roadmap:
    p1 = Problem(
        slug="two-sum-roadmap",
        title="Two Sum",
        difficulty=ProblemDifficulty.EASY,
        description_md="Two sum description",
        input_description="Array",
        output_description="Indices",
        starter_code={"python": "def twoSum(): pass"},
        test_cases=[],
        constraints=[],
    )
    p2 = Problem(
        slug="three-sum-roadmap",
        title="Three Sum",
        difficulty=ProblemDifficulty.MEDIUM,
        description_md="Three sum description",
        input_description="Array",
        output_description="Triplets",
        starter_code={"python": "def threeSum(): pass"},
        test_cases=[],
        constraints=[],
    )
    db_session.add_all([p1, p2])
    await db_session.commit()

    rm = Roadmap(
        slug="dsa-mastery",
        title="DSA Mastery Roadmap",
        description_md="Complete DSA Guide",
        is_published=True,
        is_default=True,
    )
    db_session.add(rm)
    await db_session.commit()

    st = RoadmapStage(
        roadmap_id=rm.id,
        title="Arrays & Hashing",
        slug="arrays-hashing",
        category_name="Arrays",
        order=0,
    )
    db_session.add(st)
    await db_session.commit()

    sp1 = RoadmapStageProblem(stage_id=st.id, problem_id=p1.id, order=0)
    sp2 = RoadmapStageProblem(stage_id=st.id, problem_id=p2.id, order=1)
    db_session.add_all([sp1, sp2])
    await db_session.commit()
    await db_session.refresh(rm)
    return rm


@pytest.mark.asyncio
async def test_list_roadmaps(client: AsyncClient, sample_roadmap_data: Roadmap):
    res = await client.get("/api/v1/roadmaps/")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["slug"] == "dsa-mastery"


@pytest.mark.asyncio
async def test_get_my_roadmap(client: AsyncClient, sample_roadmap_data: Roadmap):
    headers = await get_auth_headers(client, "rm_user1")
    res = await client.get("/api/v1/roadmaps/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "DSA Mastery Roadmap"
    assert len(data["stages"]) == 1


@pytest.mark.asyncio
async def test_get_roadmap_progress_and_recommendations(
    client: AsyncClient, sample_roadmap_data: Roadmap
):
    headers = await get_auth_headers(client, "rm_user2")
    res_prog = await client.get("/api/v1/roadmaps/progress", headers=headers)
    assert res_prog.status_code == 200
    prog_data = res_prog.json()
    assert "categories" in prog_data
    assert "difficulties" in prog_data

    res_rec = await client.get("/api/v1/roadmaps/recommendations", headers=headers)
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert isinstance(rec_data, list)
    assert len(rec_data) >= 1
