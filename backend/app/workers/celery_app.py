"""The single Celery application shared by every background task.

Both the generic execution worker and the DSA judge publish to the default
queue, so they must live on one app. Two separate ``Celery()`` instances would
mean whichever one the worker was started with silently rejected the other's
tasks as unregistered.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Coroutine, TypeVar

from celery import Celery

from app.core.config import settings

app = Celery(
    "codeforge",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.execution", "app.workers.submission"],
)

app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
)

_T = TypeVar("_T")


def run_task_coroutine(coro: "Coroutine[object, object, _T]") -> _T:
    """Run a task body's coroutine, safe whether or not a loop is already running.

    A real Celery worker process has no event loop, so ``asyncio.run`` works
    directly. In eager mode (``CELERY_TASK_ALWAYS_EAGER``, used for local dev
    without a broker) the task body executes synchronously inside the caller —
    which, for a submission created from a FastAPI request, is already inside
    a running event loop, and ``asyncio.run`` refuses to nest. Fall back to a
    dedicated thread with its own loop in that case.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()
