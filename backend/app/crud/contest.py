"""Database access for contests, registrations, submissions, and leaderboards."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contest import (
    Contest,
    ContestParticipant,
    ContestProblem,
    ContestRegistration,
    ContestSubmission,
)
from app.models.user import User


class ContestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, contest_id: UUID, *, include_problems: bool = False) -> Contest | None:
        stmt = select(Contest).where(Contest.id == contest_id)
        if include_problems:
            stmt = stmt.options(selectinload(Contest.problems).selectinload(ContestProblem.problem))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def by_slug(self, slug: str) -> Contest | None:
        stmt = select(Contest).where(Contest.slug == slug)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_contests(
        self,
        *,
        status_filter: str | None = None,
        include_unpublished: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Contest], int]:
        now = datetime.now(UTC)
        stmt = select(Contest)
        if not include_unpublished:
            stmt = stmt.where(Contest.is_published.is_(True))

        if status_filter == "upcoming":
            stmt = stmt.where(Contest.start_time > now)
        elif status_filter == "running":
            stmt = stmt.where(Contest.start_time <= now, Contest.end_time >= now)
        elif status_filter == "ended":
            stmt = stmt.where(Contest.end_time < now)

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(total_stmt)).scalar_one()

        items = list(
            (
                await self.session.execute(
                    stmt.order_by(Contest.start_time.desc()).offset(offset).limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return items, total

    async def get_registration(self, contest_id: UUID, user_id: UUID) -> ContestRegistration | None:
        stmt = select(ContestRegistration).where(
            ContestRegistration.contest_id == contest_id,
            ContestRegistration.user_id == user_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def register_user(self, contest_id: UUID, user_id: UUID) -> ContestRegistration:
        reg = await self.get_registration(contest_id, user_id)
        if not reg:
            reg = ContestRegistration(contest_id=contest_id, user_id=user_id)
            self.session.add(reg)
            # Also create initial participant record
            participant = await self.get_participant(contest_id, user_id)
            if not participant:
                self.session.add(ContestParticipant(contest_id=contest_id, user_id=user_id))
            await self.session.commit()
            await self.session.refresh(reg)
        return reg

    async def unregister_user(self, contest_id: UUID, user_id: UUID) -> bool:
        reg = await self.get_registration(contest_id, user_id)
        if reg:
            await self.session.delete(reg)
            participant = await self.get_participant(contest_id, user_id)
            if participant:
                await self.session.delete(participant)
            await self.session.commit()
            return True
        return False

    async def count_participants(self, contest_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(ContestRegistration)
            .where(ContestRegistration.contest_id == contest_id)
        )
        return (await self.session.execute(stmt)).scalar_one()

    async def participant_counts(self, contest_ids: list[UUID]) -> dict[UUID, int]:
        """Fetch participant counts for a page of contests in one query."""
        if not contest_ids:
            return {}
        stmt = (
            select(ContestRegistration.contest_id, func.count())
            .where(ContestRegistration.contest_id.in_(contest_ids))
            .group_by(ContestRegistration.contest_id)
        )
        return dict((await self.session.execute(stmt)).all())

    async def registered_contest_ids(self, contest_ids: list[UUID], user_id: UUID) -> set[UUID]:
        """Fetch a user's registrations for a page of contests in one query."""
        if not contest_ids:
            return set()
        stmt = select(ContestRegistration.contest_id).where(
            ContestRegistration.contest_id.in_(contest_ids),
            ContestRegistration.user_id == user_id,
        )
        return set((await self.session.execute(stmt)).scalars().all())

    async def get_participant(self, contest_id: UUID, user_id: UUID) -> ContestParticipant | None:
        stmt = select(ContestParticipant).where(
            ContestParticipant.contest_id == contest_id,
            ContestParticipant.user_id == user_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def record_contest_submission(
        self,
        contest_id: UUID,
        problem_id: UUID,
        submission_id: UUID,
        user_id: UUID,
    ) -> ContestSubmission:
        c_sub = ContestSubmission(
            contest_id=contest_id,
            problem_id=problem_id,
            submission_id=submission_id,
            user_id=user_id,
        )
        self.session.add(c_sub)
        await self.session.commit()
        await self.session.refresh(c_sub)
        return c_sub

    async def get_leaderboard(
        self, contest_id: UUID, offset: int = 0, limit: int = 50
    ) -> tuple[list[tuple[ContestParticipant, User]], int]:
        stmt = (
            select(ContestParticipant, User)
            .join(User, User.id == ContestParticipant.user_id)
            .where(ContestParticipant.contest_id == contest_id)
            .order_by(
                ContestParticipant.total_score.desc(),
                ContestParticipant.total_penalty.asc(),
            )
        )
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(total_stmt)).scalar_one()

        rows = (await self.session.execute(stmt.offset(offset).limit(limit))).all()
        return [(row[0], row[1]) for row in rows], total

    async def get_user_contests(self, user_id: UUID) -> list[dict]:
        ranked_participants = (
            select(
                ContestParticipant.contest_id.label("contest_id"),
                ContestParticipant.user_id.label("user_id"),
                ContestParticipant.total_score.label("total_score"),
                ContestParticipant.total_penalty.label("total_penalty"),
                ContestParticipant.problems_solved.label("problems_solved"),
                func.rank()
                .over(
                    partition_by=ContestParticipant.contest_id,
                    order_by=(
                        ContestParticipant.total_score.desc(),
                        ContestParticipant.total_penalty.asc(),
                    ),
                )
                .label("rank"),
            )
            .subquery()
        )
        stmt = (
            select(
                ContestRegistration,
                Contest,
                ranked_participants.c.rank,
                ranked_participants.c.total_score,
                ranked_participants.c.total_penalty,
                ranked_participants.c.problems_solved,
            )
            .join(Contest, Contest.id == ContestRegistration.contest_id)
            .outerjoin(
                ranked_participants,
                (ranked_participants.c.contest_id == Contest.id)
                & (ranked_participants.c.user_id == user_id),
            )
            .where(ContestRegistration.user_id == user_id)
            .order_by(Contest.start_time.desc())
        )
        rows = (await self.session.execute(stmt)).all()
        results = []
        for reg, contest, rank, total_score, total_penalty, problems_solved in rows:
            results.append(
                {
                    "contest": contest,
                    "registered_at": reg.registered_at,
                    "rank": rank if rank is not None else None,
                    "total_score": total_score if total_score is not None else 0,
                    "total_penalty": total_penalty if total_penalty is not None else 0,
                    "problems_solved": problems_solved if problems_solved is not None else 0,
                }
            )
        return results
