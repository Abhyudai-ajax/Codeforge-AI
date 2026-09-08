"""The Celery worker must consume every task the API publishes.

A missing registration is invisible at publish time — `.delay()` succeeds and the
message is simply rejected by the worker — so submissions would sit QUEUED
forever. These tests pin the contract between the API and the worker entrypoint.
"""

from __future__ import annotations

import pytest

from app.workers import app as worker_app
from app.workers.execution import execute_job
from app.workers.submission import judge_submission

# The name docker-compose starts the worker with: `celery -A app.workers:app`.
PUBLISHED_TASKS = {"codeforge.execute_job", "codeforge.judge_submission"}


def test_worker_entrypoint_registers_every_published_task():
    assert PUBLISHED_TASKS <= set(worker_app.tasks)


def test_all_tasks_share_one_celery_app():
    """Separate Celery apps on the same queue reject each other's messages."""
    assert execute_job.app is worker_app
    assert judge_submission.app is worker_app


@pytest.mark.parametrize(
    ("task", "expected_name"),
    [(execute_job, "codeforge.execute_job"), (judge_submission, "codeforge.judge_submission")],
)
def test_task_names_are_stable(task, expected_name):
    """Renaming a task orphans messages already queued under the old name."""
    assert task.name == expected_name


def test_broker_and_backend_are_configured():
    assert worker_app.conf.broker_url
    assert worker_app.conf.result_backend
