"""The seeder must load the whole catalog and stay idempotent across re-runs."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.db.problem_catalog import CATALOG, CATALOG_BY_SLUG
from app.db.seed_data import seed_problems
from app.models.problem import Problem, TestCase


@pytest.mark.asyncio
async def test_seeding_loads_every_catalog_problem(db_session):
    created, updated = await seed_problems(db_session)
    assert (created, updated) == (len(CATALOG), 0)

    total = await db_session.scalar(select(func.count()).select_from(Problem))
    assert total == len(CATALOG)


@pytest.mark.asyncio
async def test_seeding_twice_refreshes_instead_of_duplicating(db_session):
    await seed_problems(db_session)
    created, updated = await seed_problems(db_session)

    assert created == 0, "re-seeding must not insert duplicates"
    assert updated == len(CATALOG)
    total = await db_session.scalar(select(func.count()).select_from(Problem))
    assert total == len(CATALOG)

    # Test cases are replaced, not appended, on every refresh.
    case_total = await db_session.scalar(select(func.count()).select_from(TestCase))
    assert case_total == sum(len(problem.cases) for problem in CATALOG)


@pytest.mark.asyncio
async def test_seeded_problem_is_editor_ready(db_session):
    await seed_problems(db_session)
    problem = (
        await db_session.execute(select(Problem).where(Problem.slug == "two-sum"))
    ).scalar_one()
    spec = CATALOG_BY_SLUG["two-sum"]

    assert problem.title == spec.title
    assert problem.input_description and problem.output_description
    assert problem.editorial_md
    assert problem.constraints
    assert {"c", "cpp", "python", "javascript", "java"} <= set(problem.supported_languages)
    assert set(problem.starter_code) == set(problem.supported_languages)
    assert problem.is_active


@pytest.mark.asyncio
async def test_only_sample_cases_are_public(db_session):
    await seed_problems(db_session)
    problem = (
        await db_session.execute(select(Problem).where(Problem.slug == "two-sum"))
    ).scalar_one()
    spec = CATALOG_BY_SLUG["two-sum"]

    cases = sorted(problem.test_cases, key=lambda case: case.order)
    assert len(cases) == len(spec.cases)
    assert [case.is_public for case in cases] == [
        index < spec.sample_count for index in range(len(spec.cases))
    ]
    assert any(not case.is_public for case in cases), "hidden cases must exist"


@pytest.mark.asyncio
async def test_seeded_catalog_is_listable_over_the_api(client, db_session):
    await seed_problems(db_session)
    response = await client.get("/api/v1/problems?limit=100")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == len(CATALOG)

    response = await client.get("/api/v1/problems?difficulty=hard&limit=100")
    assert response.status_code == 200
    hard = sum(1 for problem in CATALOG if problem.difficulty == "hard")
    assert response.json()["total"] == hard


@pytest.mark.asyncio
async def test_seeded_problems_are_filterable_by_c_support(client, db_session):
    await seed_problems(db_session)
    response = await client.get("/api/v1/problems?language=c&limit=100")
    assert response.status_code == 200
    assert response.json()["total"] == len(CATALOG)
