"""Business rules for DSA problem management and asynchronous submissions."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import languages
from app.crud.problem import ProblemRepository
from app.models.problem import (
    Problem,
    ProblemTag,
    Submission,
    SubmissionStatus,
    TestCase,
    UserProblemProgress,
)
from app.models.user import User
from app.schemas.problem import ProblemCreate, ProblemUpdate, SubmissionCreate
from app.services.coding_room_service import CodingRoomService


class ProblemService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProblemRepository(session)

    async def create(self, payload: ProblemCreate) -> Problem:
        if await self.repo.by_slug(payload.slug):
            raise HTTPException(409, "Problem slug already exists.")
        problem = Problem(**payload.model_dump(exclude={"tags", "test_cases"}))
        problem.tags = await self._tags(payload.tags)
        problem.test_cases = [TestCase(**case.model_dump()) for case in payload.test_cases]
        self.session.add(problem)
        await self.session.commit()
        await self.session.refresh(problem)
        return problem

    async def update(self, problem_id: UUID, payload: ProblemUpdate) -> Problem:
        problem = await self.repo.get(problem_id, include_cases=True)
        if not problem:
            raise HTTPException(404, "Problem not found.")
        values = payload.model_dump(exclude_unset=True, exclude={"tags", "test_cases"})
        for key, value in values.items():
            setattr(problem, key, value)
        if payload.tags is not None:
            problem.tags = await self._tags(payload.tags)
        if payload.test_cases is not None:
            problem.test_cases = [TestCase(**case.model_dump()) for case in payload.test_cases]
        await self.session.commit()
        await self.session.refresh(problem)
        return problem

    async def delete(self, problem_id: UUID) -> None:
        problem = await self.repo.get(problem_id)
        if not problem:
            raise HTTPException(404, "Problem not found.")
        await self.session.delete(problem)
        await self.session.commit()

    async def _tags(self, names: list[str]) -> list[ProblemTag]:
        tags = []
        for name in sorted({name.strip().lower() for name in names if name.strip()}):
            tag = (
                await self.session.execute(select(ProblemTag).where(ProblemTag.name == name))
            ).scalar_one_or_none()
            if tag is None:
                tag = ProblemTag(name=name)
                self.session.add(tag)
            tags.append(tag)
        return tags


class SubmissionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProblemRepository(session)

    async def create(self, user: User, payload: SubmissionCreate) -> Submission:
        problem = await self.repo.get(payload.problem_id, include_cases=True)
        if not problem or not problem.is_active:
            raise HTTPException(404, "Problem not found.")
        language = languages.normalize(payload.language)
        if language not in problem.supported_languages:
            raise HTTPException(422, "Language is not supported by this problem.")
        if payload.room_id:
            await CodingRoomService(self.session).require_member(payload.room_id, user, write=True)
        submission = Submission(
            user_id=user.id,
            problem_id=problem.id,
            room_id=payload.room_id,
            language=language,
            source_code=payload.source_code,
            total_test_count=len(problem.test_cases),
        )
        self.session.add(submission)
        await self.session.commit()
        await self.session.refresh(submission)
        try:
            from app.workers.submission import judge_submission

            judge_submission.delay(str(submission.id))
        except Exception:
            submission.status = SubmissionStatus.FAILED
            submission.error_output = "Judge queue unavailable."
            submission.completed_at = datetime.now(UTC)
            await self.session.commit()
            raise HTTPException(503, "Submission queue is unavailable.")
        return submission

    async def get_for_user(self, submission_id: UUID, user: User) -> Submission:
        submission = await self.repo.submission(submission_id)
        if not submission:
            raise HTTPException(404, "Submission not found.")
        is_owner = submission.user_id == user.id
        is_admin = getattr(user.role, "value", user.role) == "admin"
        if not is_owner and not is_admin:
            raise HTTPException(403, "Submission access denied.")
        return submission

    async def record_result(
        self,
        submission: Submission,
        status: SubmissionStatus,
        passed: int,
        output: str = "",
        error: str = "",
    ) -> None:
        submission.status = status
        submission.passed_test_count = passed
        submission.score = passed
        submission.output = output[:65536]
        submission.error_output = error[:65536]
        submission.completed_at = datetime.now(UTC)
        progress = (
            await self.session.execute(
                select(UserProblemProgress).where(
                    UserProblemProgress.user_id == submission.user_id,
                    UserProblemProgress.problem_id == submission.problem_id,
                )
            )
        ).scalar_one_or_none()
        if not progress:
            progress = UserProblemProgress(
                user_id=submission.user_id, problem_id=submission.problem_id
            )
            self.session.add(progress)
        progress.attempts = (progress.attempts or 0) + 1
        progress.last_attempt_at = submission.completed_at
        if status == SubmissionStatus.ACCEPTED:
            progress.accepted_submissions = (progress.accepted_submissions or 0) + 1
            progress.first_solved_at = progress.first_solved_at or submission.completed_at
        else:
            progress.failed_submissions = (progress.failed_submissions or 0) + 1
        await self.session.commit()
