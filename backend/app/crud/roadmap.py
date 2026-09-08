"""CRUD operations for Roadmaps, Stages, and User Roadmap Selections."""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.problem import (
    Submission,
    SubmissionStatus,
    UserProblemProgress,
)
from app.models.roadmap import Roadmap, UserRoadmapSelection


class CRUDRoadmap:
    """CRUD operations for Roadmaps and user progress tracking."""

    async def get_default_roadmap(self, db: AsyncSession) -> Roadmap | None:
        stmt = (
            select(Roadmap)
            .where(
                Roadmap.is_default.is_(True),
                Roadmap.is_published.is_(True),
            )
            .order_by(Roadmap.order.asc())
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_by_id(self, db: AsyncSession, roadmap_id: uuid.UUID) -> Roadmap | None:
        stmt = select(Roadmap).where(Roadmap.id == roadmap_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Roadmap | None:
        stmt = select(Roadmap).where(Roadmap.slug == slug)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_roadmaps(
        self, db: AsyncSession, published_only: bool = True
    ) -> Sequence[Roadmap]:
        stmt = select(Roadmap)
        if published_only:
            stmt = stmt.where(Roadmap.is_published.is_(True))
        stmt = stmt.order_by(Roadmap.order.asc(), Roadmap.title.asc())
        res = await db.execute(stmt)
        return res.scalars().all()

    async def get_user_active_selection(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> UserRoadmapSelection | None:
        stmt = select(UserRoadmapSelection).where(
            UserRoadmapSelection.user_id == user_id,
            UserRoadmapSelection.is_active.is_(True),
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def set_user_selection(
        self, db: AsyncSession, user_id: uuid.UUID, roadmap_id: uuid.UUID
    ) -> UserRoadmapSelection:
        stmt_prev = select(UserRoadmapSelection).where(
            UserRoadmapSelection.user_id == user_id,
            UserRoadmapSelection.is_active.is_(True),
        )
        prev_res = await db.execute(stmt_prev)
        prev = prev_res.scalars().all()
        for p in prev:
            p.is_active = False

        stmt_existing = select(UserRoadmapSelection).where(
            UserRoadmapSelection.user_id == user_id,
            UserRoadmapSelection.roadmap_id == roadmap_id,
        )
        existing_res = await db.execute(stmt_existing)
        existing = existing_res.scalar_one_or_none()

        if existing:
            existing.is_active = True
            selection = existing
        else:
            selection = UserRoadmapSelection(
                user_id=user_id,
                roadmap_id=roadmap_id,
                is_active=True,
            )
            db.add(selection)

        await db.commit()
        await db.refresh(selection)
        return selection

    async def get_user_solved_problem_ids(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> set[uuid.UUID]:
        """Fetch set of problem IDs solved by user."""
        stmt_prog = select(UserProblemProgress.problem_id).where(
            UserProblemProgress.user_id == user_id,
            UserProblemProgress.accepted_submissions > 0,
        )
        res_prog = await db.execute(stmt_prog)
        solved_ids = set(res_prog.scalars().all())

        stmt_sub = select(Submission.problem_id).where(
            Submission.user_id == user_id,
            Submission.status == SubmissionStatus.ACCEPTED,
        )
        res_sub = await db.execute(stmt_sub)
        solved_ids.update(res_sub.scalars().all())

        return solved_ids


roadmap_crud = CRUDRoadmap()
