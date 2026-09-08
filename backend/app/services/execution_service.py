from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import languages
from app.crud.execution import ExecutionCRUD
from app.models.execution import ExecutionJob, ExecutionStatus
from app.models.user import User
from app.schemas.execution import ExecutionCreate
from app.services.coding_room_service import CodingRoomService
from app.services.project_service import ProjectService


class ExecutionService:
    def __init__(self, session: AsyncSession) -> None:
        self.crud = ExecutionCRUD(session)
        self.session = session

    async def enqueue(self, user: User, payload: ExecutionCreate) -> ExecutionJob:
        language = languages.normalize(payload.language)
        if not languages.is_supported(language):
            raise HTTPException(status_code=422, detail="Unsupported execution language.")
        if payload.room_id:
            await CodingRoomService(self.session).require_member(payload.room_id, user, write=True)
        if payload.project_id:
            project = await ProjectService(self.session).get_project(payload.project_id, user)
            if project.owner_id != user.id:
                raise HTTPException(
                    status_code=403, detail="Project owner access is required for execution."
                )
        job = await self.crud.create(
            ExecutionJob(
                user_id=user.id, language=language, **payload.model_dump(exclude={"language"})
            )
        )
        from app.workers.execution import execute_job

        try:
            execute_job.delay(str(job.id))
        except Exception:
            job.status = ExecutionStatus.FAILED
            job.stderr = "Execution queue unavailable."
            from datetime import UTC, datetime

            job.completed_at = datetime.now(UTC)
            self.session.add(job)
            await self.session.commit()
            raise HTTPException(status_code=503, detail="Execution queue is unavailable.")
        return job

    async def cancel(self, job_id, user: User) -> ExecutionJob:
        from datetime import UTC, datetime

        job = await self.get_for_user(job_id, user)
        if not await self.crud.transition_by_id(
            job.id, ExecutionStatus.QUEUED, ExecutionStatus.CANCELLED
        ):
            raise HTTPException(status_code=409, detail="Only queued executions can be cancelled.")
        job.completed_at = datetime.now(UTC)
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_for_user(self, job_id, user: User) -> ExecutionJob:
        job = await self.crud.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Execution not found.")
        if job.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this execution.",
            )
        return job
