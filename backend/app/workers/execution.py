"""Celery worker: the only component allowed to invoke Docker sandboxes."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime

from app.core import languages
from app.core.database import AsyncSessionLocal
from app.crud.execution import ExecutionCRUD
from app.models.execution import ExecutionJob, ExecutionStatus
from app.workers.celery_app import app as celery_app
from app.workers.celery_app import run_task_coroutine
from app.workers.sandbox import run_source

logger = logging.getLogger(__name__)


def terminal_status(language: str, exit_code: int) -> ExecutionStatus:
    """Classify a sandbox process result without evaluating user source in Python."""
    if exit_code == 0:
        return ExecutionStatus.COMPLETED
    if languages.is_compiled(language):
        return ExecutionStatus.COMPILATION_ERROR
    return ExecutionStatus.RUNTIME_ERROR


async def _run(job_id: str) -> None:
    async with AsyncSessionLocal() as session:
        crud = ExecutionCRUD(session)
        execution_id = uuid.UUID(job_id)
        if not await crud.claim(execution_id):
            return
        job = await session.get(ExecutionJob, execution_id)
        if job is None:
            return
        started = time.monotonic()
        try:
            result = run_source(job.language, job.source_code, job.stdin, 5, 256)
            if result.timed_out:
                raise TimeoutError
            job.stdout = result.stdout[:65_536]
            job.stderr = result.stderr[:65_536]
            job.exit_code = result.exit_code
            exit_val = result.exit_code if result.exit_code is not None else 1
            final_status = terminal_status(job.language, exit_val)
            await crud.transition_by_id(execution_id, ExecutionStatus.RUNNING, final_status)
        except TimeoutError:
            await crud.transition_by_id(
                execution_id, ExecutionStatus.RUNNING, ExecutionStatus.TIMEOUT
            )
            job.stderr = "Execution timed out."
        except Exception:
            logger.exception("Execution worker failed for job id=%s", job_id)
            await crud.transition_by_id(
                execution_id, ExecutionStatus.RUNNING, ExecutionStatus.FAILED
            )
            job.stderr = "Execution worker failed; inspect worker logs."
        job.execution_time_ms = int((time.monotonic() - started) * 1000)
        job.completed_at = datetime.now(UTC)
        await session.commit()


@celery_app.task(name="codeforge.execute_job")
def execute_job(job_id: str) -> None:
    run_task_coroutine(_run(job_id))
