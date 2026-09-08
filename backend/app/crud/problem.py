"""Database access for DSA problems and submissions."""

from uuid import UUID

from sqlalchemy import String, cast, false, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import languages
from app.models.problem import Problem, ProblemTag, Submission, SubmissionStatus


def _supports_language(language: str):
    """Filter problems offering ``language``.

    ``supported_languages`` is a generic JSON column, so ``.contains()`` is a
    string operator here rather than JSON containment and never matches. Match
    the serialized array text instead, which works on both PostgreSQL and the
    SQLite used by the tests. The quotes in the pattern keep ``c`` from matching
    ``cpp`` and ``java`` from matching ``javascript``.
    """
    canonical = languages.normalize(language)
    if not languages.is_supported(canonical):
        return false()
    return cast(Problem.supported_languages, String).like(f'%"{canonical}"%')


class ProblemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, problem_id: UUID, *, include_cases: bool = False) -> Problem | None:
        stmt = select(Problem).where(Problem.id == problem_id).options(selectinload(Problem.tags))
        if include_cases:
            stmt = stmt.options(selectinload(Problem.test_cases))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def by_slug(self, slug: str) -> Problem | None:
        return (
            await self.session.execute(select(Problem).where(Problem.slug == slug))
        ).scalar_one_or_none()

    async def list(
        self,
        *,
        difficulty: str | None,
        language: str | None,
        tag: str | None,
        search: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Problem], int]:
        stmt = (
            select(Problem).where(Problem.is_active.is_(True)).options(selectinload(Problem.tags))
        )
        if difficulty:
            stmt = stmt.where(Problem.difficulty == difficulty)
        if language:
            stmt = stmt.where(_supports_language(language))
        if tag:
            stmt = stmt.join(Problem.tags).where(ProblemTag.name.ilike(tag))
        if search:
            stmt = stmt.where(
                Problem.title.ilike(f"%{search}%") | Problem.slug.ilike(f"%{search}%")
            )
        total = (
            await self.session.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()
        problems = list(
            (await self.session.execute(stmt.order_by(Problem.title).offset(offset).limit(limit)))
            .scalars()
            .unique()
        )
        return problems, total

    async def submission(self, submission_id: UUID) -> Submission | None:
        return (
            await self.session.execute(select(Submission).where(Submission.id == submission_id))
        ).scalar_one_or_none()

    async def claim_submission(self, submission_id: UUID) -> bool:
        result = await self.session.execute(
            update(Submission)
            .where(Submission.id == submission_id, Submission.status == SubmissionStatus.QUEUED)
            .values(status=SubmissionStatus.RUNNING)
        )
        await self.session.commit()
        rowcount = getattr(result, "rowcount", 0)
        return bool(rowcount == 1)
