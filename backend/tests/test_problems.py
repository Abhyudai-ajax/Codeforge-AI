"""DSA catalog security tests: public consumers never receive hidden cases."""

import uuid

import pytest

from app.models.problem import Problem, ProblemDifficulty, TestCase


@pytest.mark.asyncio
async def test_public_problem_hides_cases_and_admin_case_route_requires_role(
    client, db_session
) -> None:
    problem = Problem(
        id=uuid.uuid4(),
        slug="sum-input",
        title="Sum Input",
        difficulty=ProblemDifficulty.EASY,
        description_md="Read two integers and print their sum.",
        supported_languages=["python"],
    )
    problem.test_cases = [
        TestCase(input_data="1 2\n", expected_output="3\n", is_public=True, order=1),
        TestCase(input_data="99 1\n", expected_output="100\n", is_public=False, order=2),
    ]
    db_session.add(problem)
    await db_session.commit()

    response = await client.get(f"/api/v1/problems/{problem.id}")
    assert response.status_code == 200
    body = response.json()
    assert "test_cases" not in body
    assert "99 1" not in response.text

    response = await client.get(f"/api/v1/problems/{problem.id}/test-cases")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_problem_list_filters_by_difficulty(client, db_session) -> None:
    db_session.add_all(
        [
            Problem(
                id=uuid.uuid4(),
                slug="easy-problem",
                title="Easy",
                difficulty=ProblemDifficulty.EASY,
                description_md="x",
            ),
            Problem(
                id=uuid.uuid4(),
                slug="hard-problem",
                title="Hard",
                difficulty=ProblemDifficulty.HARD,
                description_md="x",
            ),
        ]
    )
    await db_session.commit()
    response = await client.get("/api/v1/problems?difficulty=easy")
    assert response.status_code == 200
    assert [item["slug"] for item in response.json()["items"]] == ["easy-problem"]
