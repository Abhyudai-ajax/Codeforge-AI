"""Execution API tests; Docker integration is skipped when Docker is unavailable."""

import shutil

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.crud.execution import ExecutionCRUD
from app.models.execution import ExecutionJob, ExecutionStatus
from app.models.user import User
from app.workers.execution import terminal_status


async def _headers(client: AsyncClient) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "executor",
            "email": "executor@example.com",
            "password": "StrongPassword123!",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "executor@example.com", "password": "StrongPassword123!"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_execution_requires_authentication(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/executions", json={"language": "python", "source_code": "print(1)"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_language_is_rejected_before_queueing(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/executions",
        json={"language": "ruby", "source_code": "puts 1"},
        headers=await _headers(client),
    )
    assert response.status_code == 422


@pytest.mark.skipif(
    shutil.which("docker") is None,
    reason="Docker is required for isolated-runner integration tests",
)
def test_docker_available_for_integration() -> None:
    assert shutil.which("docker") is not None


def test_worker_terminal_status_classification() -> None:
    assert terminal_status("python", 0) == ExecutionStatus.COMPLETED
    assert terminal_status("cpp", 1) == ExecutionStatus.COMPILATION_ERROR
    assert terminal_status("java", 1) == ExecutionStatus.COMPILATION_ERROR
    assert terminal_status("javascript", 1) == ExecutionStatus.RUNTIME_ERROR


@pytest.mark.asyncio
async def test_execution_transition_contract(db_session) -> None:
    user = User(username="state_user", email="state@example.com", hashed_password="hash")
    db_session.add(user)
    await db_session.commit()
    job = await ExecutionCRUD(db_session).create(
        ExecutionJob(user_id=user.id, language="python", source_code="print(1)")
    )
    crud = ExecutionCRUD(db_session)
    assert await crud.claim(job.id)
    assert not await crud.claim(job.id)
    assert await crud.transition_by_id(job.id, ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED)
    assert not await crud.transition_by_id(
        job.id, ExecutionStatus.COMPLETED, ExecutionStatus.FAILED
    )


async def _other_headers(client: AsyncClient) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "otherexec",
            "email": "otherexec@example.com",
            "password": "StrongPassword123!",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "otherexec@example.com", "password": "StrongPassword123!"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_cancel_and_result_owner_authorization(client: AsyncClient, monkeypatch) -> None:
    from app.workers.execution import execute_job

    monkeypatch.setattr(execute_job, "delay", lambda _: None)
    owner, other = await _headers(client), await _other_headers(client)
    created = await client.post(
        "/api/v1/executions", json={"language": "python", "source_code": "print(1)"}, headers=owner
    )
    assert created.status_code == 202
    job_id = created.json()["id"]
    assert (
        await client.get(f"/api/v1/executions/{job_id}/result", headers=other)
    ).status_code == 403
    assert (
        await client.post(f"/api/v1/executions/{job_id}/cancel", headers=other)
    ).status_code == 403
    assert (await client.post(f"/api/v1/executions/{job_id}/cancel", headers=owner)).json()[
        "status"
    ] == "cancelled"


@pytest.mark.asyncio
async def test_dispatch_failure_marks_job_failed(
    client: AsyncClient, db_session, monkeypatch
) -> None:
    from app.workers.execution import execute_job

    monkeypatch.setattr(execute_job, "delay", lambda _: (_ for _ in ()).throw(ConnectionError()))
    response = await client.post(
        "/api/v1/executions",
        json={"language": "python", "source_code": "print(1)"},
        headers=await _headers(client),
    )
    assert response.status_code == 503
    job = (await db_session.execute(select(ExecutionJob))).scalar_one()
    assert job.status == ExecutionStatus.FAILED
    assert job.stderr == "Execution queue unavailable."
