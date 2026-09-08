"""Comprehensive submission flow and progress tracking unit and integration tests."""

import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models.problem import Problem, ProblemDifficulty, SubmissionStatus, TestCase
from app.workers.sandbox import SandboxResult
from app.workers.submission import _judge


async def _get_auth_headers(client: AsyncClient, username: str, email: str) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "StrongPassword123!"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_submission_creation_and_authorization(client: AsyncClient, db_session) -> None:
    problem = Problem(
        id=uuid.uuid4(),
        slug="submission-test-prob",
        title="Submission Test Problem",
        difficulty=ProblemDifficulty.EASY,
        description_md="Print sum",
        supported_languages=["python", "javascript"],
    )
    problem.test_cases = [
        TestCase(input_data="1 2\n", expected_output="3\n", is_public=True, order=1),
        TestCase(input_data="10 20\n", expected_output="30\n", is_public=False, order=2),
    ]
    db_session.add(problem)
    await db_session.commit()

    user_headers = await _get_auth_headers(client, "sub_user", "sub@example.com")
    other_headers = await _get_auth_headers(client, "other_sub_user", "othersub@example.com")

    with patch("app.workers.submission.judge_submission.delay") as mock_delay:
        response = await client.post(
            "/api/v1/submissions",
            json={
                "problem_id": str(problem.id),
                "language": "python",
                "source_code": "import sys\nprint(sum(map(int, sys.stdin.read().split())))",
            },
            headers=user_headers,
        )
        assert response.status_code == 202
        body = response.json()
        submission_id = body["id"]
        assert body["status"] == "queued"
        mock_delay.assert_called_once_with(submission_id)

    # Fetch submission details as owner
    resp_owner = await client.get(f"/api/v1/submissions/{submission_id}", headers=user_headers)
    assert resp_owner.status_code == 200
    assert resp_owner.json()["id"] == submission_id

    # Fetch submission details as unauthorized user
    resp_other = await client.get(f"/api/v1/submissions/{submission_id}", headers=other_headers)
    assert resp_other.status_code == 403


@pytest.mark.asyncio
async def test_submission_unsupported_language(client: AsyncClient, db_session) -> None:
    problem = Problem(
        id=uuid.uuid4(),
        slug="lang-test-prob",
        title="Lang Test Problem",
        difficulty=ProblemDifficulty.EASY,
        description_md="Lang test",
        supported_languages=["python"],
    )
    db_session.add(problem)
    await db_session.commit()

    headers = await _get_auth_headers(client, "lang_user", "lang@example.com")
    response = await client.post(
        "/api/v1/submissions",
        json={
            "problem_id": str(problem.id),
            "language": "cpp",
            "source_code": "#include <iostream>",
        },
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_judge_worker_and_progress_tracking(client: AsyncClient, db_session) -> None:
    problem = Problem(
        id=uuid.uuid4(),
        slug="judge-progress-prob",
        title="Judge Progress Problem",
        difficulty=ProblemDifficulty.EASY,
        description_md="Judge test",
        supported_languages=["python"],
    )
    problem.test_cases = [
        TestCase(input_data="1\n", expected_output="1\n", is_public=True, order=1),
        TestCase(input_data="2\n", expected_output="2\n", is_public=False, order=2),
    ]
    db_session.add(problem)
    await db_session.commit()

    user_headers = await _get_auth_headers(client, "judge_user", "judge@example.com")

    with patch("app.workers.submission.judge_submission.delay"):
        create_resp = await client.post(
            "/api/v1/submissions",
            json={
                "problem_id": str(problem.id),
                "language": "python",
                "source_code": "import sys\nprint(sys.stdin.read().strip())",
            },
            headers=user_headers,
        )
        assert create_resp.status_code == 202
        sub_id = create_resp.json()["id"]

    # Mock sandbox execution and DB session local for background worker call
    from tests.conftest import _TestSessionLocal

    with (
        patch("app.workers.submission.AsyncSessionLocal", _TestSessionLocal),
        patch("app.workers.submission.run_source") as mock_run,
    ):
        mock_run.side_effect = [
            SandboxResult(stdout="1\n", stderr="", exit_code=0),
            SandboxResult(stdout="2\n", stderr="", exit_code=0),
        ]
        await _judge(sub_id)

    # Check updated submission status
    res = await client.get(f"/api/v1/submissions/{sub_id}", headers=user_headers)
    assert res.status_code == 200
    assert res.json()["status"] == SubmissionStatus.ACCEPTED.value
    assert res.json()["passed_test_count"] == 2

    # Check user progress endpoint
    prog_resp = await client.get("/api/v1/users/me/progress", headers=user_headers)
    assert prog_resp.status_code == 200
    prog_data = prog_resp.json()
    assert prog_data["solved"] >= 1
    assert prog_data["by_difficulty"]["easy"] >= 1

    # Check problem progress endpoint
    prob_prog = await client.get("/api/v1/users/me/progress/problems", headers=user_headers)
    assert prob_prog.status_code == 200
    matched = [p for p in prob_prog.json() if p["problem_id"] == str(problem.id)]
    assert len(matched) == 1
    assert matched[0]["accepted_submissions"] == 1


@pytest.mark.asyncio
async def test_problem_run_and_submit_adapters(client: AsyncClient, db_session) -> None:
    problem = Problem(
        id=uuid.uuid4(),
        slug="editor-adapter-prob",
        title="Editor Adapter Problem",
        difficulty=ProblemDifficulty.EASY,
        description_md="Adapter test",
        supported_languages=["python"],
    )
    problem.test_cases = [
        TestCase(input_data="1 2\n", expected_output="3\n", is_public=True, order=1),
    ]
    db_session.add(problem)
    await db_session.commit()
    headers = await _get_auth_headers(client, "adapter_user", "adapter@example.com")

    with patch(
        "app.services.problem_execution_service.run_source",
        return_value=SandboxResult(stdout="3\n", stderr="", exit_code=0),
    ):
        run_response = await client.post(
            f"/api/v1/problems/{problem.id}/run",
            json={
                "code": "print(3)",
                "language": "python",
                "custom_test_cases": [{"input": "1 2\n", "expected_output": "3\n"}],
            },
            headers=headers,
        )
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "accepted"
    assert run_response.json()["passed_test_cases"] == 1

    with patch("app.workers.submission.judge_submission.delay") as mock_delay:
        submit_response = await client.post(
            f"/api/v1/problems/{problem.id}/submit",
            json={"code": "print(3)", "language": "python"},
            headers=headers,
        )
    assert submit_response.status_code == 202
    mock_delay.assert_called_once()
