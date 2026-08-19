"""
Project CRUD Repository
Implements repository pattern for Project model.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectVisibility

logger = logging.getLogger(__name__)


class ProjectCRUD:
    """Repository providing async CRUD operations for Project."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ==========================================================
    # Read Operations
    # ==========================================================

    async def get_by_id(
        self, project_id: uuid.UUID, include_deleted: bool = False
    ) -> Project | None:
        query = select(Project).where(Project.id == project_id)
        if not include_deleted:
            query = query.where(Project.deleted_at.is_(None))

        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_owner(
        self,
        owner_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Project], int]:

        total_result = await self._session.execute(
            select(func.count())
            .select_from(Project)
            .where(
                Project.owner_id == owner_id,
                Project.deleted_at.is_(None),
            )
        )

        total = total_result.scalar_one()

        result = await self._session.execute(
            select(Project)
            .where(
                Project.owner_id == owner_id,
                Project.deleted_at.is_(None),
            )
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all()), total

    async def list_public(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Project], int]:

        total_result = await self._session.execute(
            select(func.count())
            .select_from(Project)
            .where(
                Project.visibility == ProjectVisibility.PUBLIC,
                Project.deleted_at.is_(None),
            )
        )

        total = total_result.scalar_one()

        result = await self._session.execute(
            select(Project)
            .where(
                Project.visibility == ProjectVisibility.PUBLIC,
                Project.deleted_at.is_(None),
            )
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all()), total

    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 20,
        public_only: bool = True,
    ) -> tuple[list[Project], int]:

        filters = or_(
            Project.title.ilike(f"%{query}%"),
            Project.description.ilike(f"%{query}%"),
        )

        where_clauses = [filters, Project.deleted_at.is_(None)]
        if public_only:
            where_clauses.append(Project.visibility == ProjectVisibility.PUBLIC)

        total_result = await self._session.execute(
            select(func.count()).select_from(Project).where(*where_clauses)
        )

        total = total_result.scalar_one()

        result = await self._session.execute(
            select(Project)
            .where(*where_clauses)
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all()), total

    # ==========================================================
    # Create
    # ==========================================================

    async def create(self, project: Project) -> Project:

        self._session.add(project)

        await self._session.commit()
        await self._session.refresh(project)

        logger.info("Created project %s", project.id)

        return project

    # ==========================================================
    # Update
    # ==========================================================

    async def update(
        self,
        project: Project,
        **kwargs,
    ) -> Project:

        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)

        self._session.add(project)

        await self._session.commit()
        await self._session.refresh(project)

        logger.info("Updated project %s", project.id)

        return project

    # ==========================================================
    # Soft Delete
    # ==========================================================

    async def soft_delete(self, project: Project) -> Project:

        from datetime import UTC, datetime

        project.deleted_at = datetime.now(UTC)

        self._session.add(project)

        await self._session.commit()
        await self._session.refresh(project)

        return project

    async def restore(self, project: Project) -> Project:

        project.deleted_at = None

        self._session.add(project)

        await self._session.commit()
        await self._session.refresh(project)

        return project

    # ==========================================================
    # Hard Delete
    # ==========================================================

    async def delete(self, project: Project) -> None:

        await self._session.delete(project)
        await self._session.commit()
