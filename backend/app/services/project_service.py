"""
Project Service Layer
Business logic for managing project lifecycle and access control.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.project import ProjectCRUD
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


class ProjectService:
    """Service layer for project management operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._crud = ProjectCRUD(session)

    async def create_project(self, owner: User, data: ProjectCreate) -> Project:
        """Create a new project owned by the authenticated user."""
        project = Project(
            owner_id=owner.id,
            title=data.title,
            description=data.description,
            language=data.language,
            visibility=data.visibility,
            github_repo=data.github_repo,
            github_branch=data.github_branch,
        )
        created = await self._crud.create(project)
        logger.info("Project created: id=%s owner_id=%s", created.id, owner.id)
        return created

    async def list_my_projects(
        self,
        owner: User,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Project], int]:
        """List projects owned by the authenticated user."""
        return await self._crud.list_by_owner(owner.id, skip=skip, limit=limit)

    async def list_public_projects(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Project], int]:
        """List all public, non-deleted projects."""
        return await self._crud.list_public(skip=skip, limit=limit)

    async def search_public_projects(
        self,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Project], int]:
        """Search public projects by title or description."""
        if not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must not be empty.",
            )
        return await self._crud.search(
            query=query,
            skip=skip,
            limit=limit,
            public_only=True,
        )

    async def get_project(
        self,
        project_id: uuid.UUID,
        current_user: User | None = None,
    ) -> Project:
        """Return a project if it is public or owned by the current user."""
        project = await self._crud.get_by_id(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )

        if project.is_public:
            return project

        if current_user is None or project.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project.",
            )

        return project

    async def update_project(
        self,
        owner: User,
        project_id: uuid.UUID,
        data: ProjectUpdate,
    ) -> Project:
        """Update an existing project owned by the authenticated user."""
        project = await self._crud.get_by_id(project_id)
        if project is None or project.owner_id != owner.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )

        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return project

        updated = await self._crud.update(project, **update_data)
        logger.info("Project updated: id=%s owner_id=%s", project.id, owner.id)
        return updated

    async def delete_project(self, owner: User, project_id: uuid.UUID) -> Project:
        """Soft delete a project owned by the authenticated user."""
        project = await self._crud.get_by_id(project_id)
        if project is None or project.owner_id != owner.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )

        deleted = await self._crud.soft_delete(project)
        logger.info(
            "Project soft deleted: id=%s owner_id=%s",
            project.id,
            owner.id,
        )
        return deleted

    async def restore_project(self, owner: User, project_id: uuid.UUID) -> Project:
        """Restore a previously soft-deleted project owned by the authenticated user."""
        project = await self._crud.get_by_id(project_id, include_deleted=True)
        if project is None or project.owner_id != owner.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )

        if not project.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is not deleted.",
            )

        restored = await self._crud.restore(project)
        logger.info(
            "Project restored: id=%s owner_id=%s",
            project.id,
            owner.id,
        )
        return restored
