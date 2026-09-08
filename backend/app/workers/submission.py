"""Celery worker that judges every persisted test case in Docker."""

from __future__ import annotations

import logging
import time
import uuid

from sqlalchemy import select

from app.core import languages
from app.core.database import AsyncSessionLocal
from app.crud.problem import ProblemRepository
from app.models.problem import Problem, Submission, SubmissionStatus, TestCase
from app.services.problem_service import SubmissionService
from app.workers.celery_app import app as celery_app
from app.workers.celery_app import run_task_coroutine
from app.workers.sandbox import SPECS, run_source

logger = logging.getLogger(__name__)


def _same_output(actual: str, expected: str) -> bool:
    """Deterministic whitespace-normalized output comparison."""
    return "\n".join(line.rstrip() for line in actual.strip().splitlines()) == "\n".join(
        line.rstrip() for line in expected.strip().splitlines()
    )


def _failure_status(language: str, stderr: str) -> SubmissionStatus:
    message = stderr.lower()
    if "memory" in message or "out of memory" in message:
        return SubmissionStatus.MEMORY_LIMIT_EXCEEDED
    if languages.is_compiled(language):
        return SubmissionStatus.COMPILATION_ERROR
    return SubmissionStatus.RUNTIME_ERROR


@celery_app.task(name="codeforge.judge_submission")
def judge_submission(submission_id: str) -> None:
    run_task_coroutine(_judge(submission_id))


async def _judge(submission_id: str) -> None:
    async with AsyncSessionLocal() as session:
        submission_uuid = uuid.UUID(submission_id)
        if not await ProblemRepository(session).claim_submission(submission_uuid):
            return  # atomic queue claim prevents duplicate work
        submission = await session.get(Submission, submission_uuid)
        if submission is None:
            return
        if submission.language not in SPECS:
            await SubmissionService(session).record_result(
                submission, SubmissionStatus.FAILED, 0, error="Unsupported judge language."
            )
            return
        cases = list(
            (
                await session.execute(
                    select(TestCase)
                    .where(TestCase.problem_id == submission.problem_id)
                    .order_by(TestCase.order)
                )
            ).scalars()
        )
        problem = await session.get(Problem, submission.problem_id)
        if problem is None:
            await SubmissionService(session).record_result(
                submission, SubmissionStatus.FAILED, 0, error="Problem no longer exists."
            )
            return
        passed = 0
        elapsed_ms = 0
        final_status = SubmissionStatus.ACCEPTED
        safe_error = ""
        try:
            for case in cases:
                started = time.monotonic()
                result = run_source(
                    submission.language,
                    submission.source_code,
                    case.input_data,
                    problem.time_limit_ms / 1000,
                    problem.memory_limit_mb,
                )
                elapsed_ms += int((time.monotonic() - started) * 1000)
                if result.timed_out:
                    final_status = SubmissionStatus.TIME_LIMIT_EXCEEDED
                    safe_error = "Time limit exceeded."
                    break
                if result.exit_code != 0:
                    final_status = _failure_status(submission.language, result.stderr)
                    safe_error = "Program failed in the isolated runner."
                    break
                if not _same_output(result.stdout, case.expected_output):
                    final_status = SubmissionStatus.WRONG_ANSWER
                    safe_error = "One or more test cases failed."
                    break
                passed += 1
        except Exception:
            logger.exception("Judge worker failed for submission %s", submission.id)
            final_status = SubmissionStatus.FAILED
            safe_error = "Judge worker failed; inspect worker logs."
        submission.runtime_ms = elapsed_ms
        # Docker's cgroup limit is enforced, but reliable peak memory requires
        # a runner-side metric protocol; leave it null rather than invent one.
        await SubmissionService(session).record_result(
            submission,
            final_status,
            passed,
            output="" if final_status != SubmissionStatus.ACCEPTED else "Accepted.",
            error=safe_error,
        )
