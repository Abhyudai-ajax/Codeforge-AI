"""Background job workers and Celery tasks.

Importing the task modules here is what registers ``codeforge.execute_job`` and
``codeforge.judge_submission`` on the worker started with ``-A app.workers:app``.
"""

from app.workers.celery_app import app

__all__ = ["app"]


def _register_tasks() -> None:
    """Import task modules for their registration side effects."""
    from app.workers import execution, submission  # noqa: F401


_register_tasks()
