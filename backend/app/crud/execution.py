from typing import cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution import ExecutionJob, ExecutionStatus

TRANSITIONS = {
    ExecutionStatus.QUEUED: {
        ExecutionStatus.RUNNING,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.FAILED,
    },
    ExecutionStatus.RUNNING: {
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.TIMEOUT,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.COMPILATION_ERROR,
        ExecutionStatus.RUNTIME_ERROR,
        ExecutionStatus.MEMORY_LIMIT,
    },
}


class ExecutionCRUD:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, job: ExecutionJob) -> ExecutionJob:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get(self, job_id: UUID) -> ExecutionJob | None:
        return (
            await self.session.execute(select(ExecutionJob).where(ExecutionJob.id == job_id))
        ).scalar_one_or_none()

    async def claim(self, job_id: UUID) -> bool:
        return await self.transition_by_id(job_id, ExecutionStatus.QUEUED, ExecutionStatus.RUNNING)

    async def transition_by_id(
        self, job_id: UUID, source: ExecutionStatus, target: ExecutionStatus
    ) -> bool:
        if target not in TRANSITIONS.get(source, set()):
            return False
        result = await self.session.execute(
            update(ExecutionJob)
            .where(ExecutionJob.id == job_id, ExecutionJob.status == source)
            .values(status=target)
        )
        await self.session.commit()
        return cast(CursorResult, result).rowcount == 1
