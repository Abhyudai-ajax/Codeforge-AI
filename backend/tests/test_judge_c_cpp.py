"""End-to-end judging for C and C++ submissions, with the sandbox stubbed out.

Docker is not available in CI, so the container itself is faked — but everything
either side of it is real: the submit route, language validation, the judge
worker's test-case loop, status classification and progress tracking.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models.problem import Problem, ProblemDifficulty, SubmissionStatus, TestCase
from app.workers.sandbox import SandboxResult
from app.workers.submission import _judge
from tests.conftest import _TestSessionLocal

C_SOURCE = """#include <stdio.h>
int main(void){int a,b;scanf("%d %d",&a,&b);printf("%d\\n",a+b);return 0;}
"""
CPP_SOURCE = """#include <iostream>
int main(){int a,b;std::cin>>a>>b;std::cout<<a+b<<std::endl;return 0;}
"""


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


async def _sum_problem(db_session) -> Problem:
    problem = Problem(
        id=uuid.uuid4(),
        slug="sum-two",
        title="Sum Two",
        difficulty=ProblemDifficulty.EASY,
        description_md="Read two integers and print their sum.",
        supported_languages=["python", "c", "cpp", "javascript", "java"],
    )
    problem.test_cases = [
        TestCase(input_data="1 2\n", expected_output="3\n", is_public=True, order=0),
        TestCase(input_data="10 5\n", expected_output="15\n", is_public=False, order=1),
    ]
    db_session.add(problem)
    await db_session.commit()
    return problem


@pytest.mark.parametrize(("language", "source"), [("c", C_SOURCE), ("cpp", CPP_SOURCE)])
@pytest.mark.asyncio
async def test_correct_c_and_cpp_submissions_are_accepted(client, db_session, language, source):
    problem = await _sum_problem(db_session)
    headers = await _auth_headers(client, f"dev_{language}", f"dev_{language}@example.com")

    with patch("app.workers.submission.judge_submission.delay", lambda _: None):
        response = await client.post(
            "/api/v1/submissions",
            json={
                "problem_id": str(problem.id),
                "language": language,
                "source_code": source,
            },
            headers=headers,
        )
    assert response.status_code == 202, response.text
    submission_id = response.json()["id"]

    answers = iter([SandboxResult("3\n", "", 0), SandboxResult("15\n", "", 0)])
    with (
        patch("app.workers.submission.AsyncSessionLocal", _TestSessionLocal),
        patch(
            "app.workers.submission.run_source",
            side_effect=lambda *a, **k: next(answers),
        ),
    ):
        await _judge(submission_id)

    result = await client.get(f"/api/v1/submissions/{submission_id}", headers=headers)
    body = result.json()
    assert body["status"] == SubmissionStatus.ACCEPTED.value
    assert body["passed_test_count"] == 2


@pytest.mark.asyncio
async def test_c_compilation_failure_is_reported_as_compilation_error(client, db_session):
    problem = await _sum_problem(db_session)
    headers = await _auth_headers(client, "broken_c", "broken_c@example.com")

    with patch("app.workers.submission.judge_submission.delay", lambda _: None):
        response = await client.post(
            "/api/v1/submissions",
            json={
                "problem_id": str(problem.id),
                "language": "c",
                "source_code": "int main(void){ this is not C }",
            },
            headers=headers,
        )
    submission_id = response.json()["id"]

    compile_failure = SandboxResult("", "main.c:1:16: error: expected ';'", 1)
    with (
        patch("app.workers.submission.AsyncSessionLocal", _TestSessionLocal),
        patch("app.workers.submission.run_source", return_value=compile_failure),
    ):
        await _judge(submission_id)

    body = (await client.get(f"/api/v1/submissions/{submission_id}", headers=headers)).json()
    assert body["status"] == SubmissionStatus.COMPILATION_ERROR.value
    assert body["passed_test_count"] == 0
    # Compiler output must not leak verbatim to the client.
    assert "main.c:1:16" not in body["error_output"]


@pytest.mark.asyncio
async def test_wrong_c_output_is_a_wrong_answer(client, db_session):
    problem = await _sum_problem(db_session)
    headers = await _auth_headers(client, "wrong_c", "wrong_c@example.com")

    with patch("app.workers.submission.judge_submission.delay", lambda _: None):
        response = await client.post(
            "/api/v1/submissions",
            json={
                "problem_id": str(problem.id),
                "language": "c",
                "source_code": C_SOURCE,
            },
            headers=headers,
        )
    submission_id = response.json()["id"]

    with (
        patch("app.workers.submission.AsyncSessionLocal", _TestSessionLocal),
        patch(
            "app.workers.submission.run_source",
            return_value=SandboxResult("999\n", "", 0),
        ),
    ):
        await _judge(submission_id)

    body = (await client.get(f"/api/v1/submissions/{submission_id}", headers=headers)).json()
    assert body["status"] == SubmissionStatus.WRONG_ANSWER.value


@pytest.mark.asyncio
async def test_language_alias_is_accepted_on_submit(client, db_session):
    """`C++` from a language dropdown must resolve to the canonical `cpp`."""
    problem = await _sum_problem(db_session)
    headers = await _auth_headers(client, "alias_dev", "alias_dev@example.com")

    with patch("app.workers.submission.judge_submission.delay", lambda _: None):
        response = await client.post(
            "/api/v1/submissions",
            json={
                "problem_id": str(problem.id),
                "language": "C++",
                "source_code": CPP_SOURCE,
            },
            headers=headers,
        )
    assert response.status_code == 202, response.text
    assert response.json()["language"] == "cpp"
