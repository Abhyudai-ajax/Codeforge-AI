"""
Project API Routes
CRUD and discovery endpoints for code projects.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import (
    get_current_active_user,
    get_current_user_optional,
)
from app.models.project_file import ProjectFile
from app.models.user import User
from app.schemas.execution import ExecutionCreate, ExecutionResponse
from app.schemas.project import (
    MessageResponse,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.schemas.project_file import ProjectFileCreate, ProjectFileResponse, ProjectFileUpdate
from app.services.execution_service import ExecutionService
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new project owned by the authenticated user.",
)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Create a new project."""
    service = ProjectService(db)
    project = await service.create_project(current_user, payload)
    return ProjectResponse.model_validate(project)


@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="List my projects",
    description="List projects owned by the authenticated user.",
)
async def list_my_projects(
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    """Return paginated projects for the authenticated user."""
    service = ProjectService(db)
    items, total = await service.list_my_projects(current_user, skip=skip, limit=limit)
    return ProjectListResponse(
        items=[ProjectResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/public",
    response_model=ProjectListResponse,
    summary="List public projects",
    description="Return publicly visible projects.",
)
async def list_public_projects(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    """Return a paginated list of public projects."""
    service = ProjectService(db)
    items, total = await service.list_public_projects(skip=skip, limit=limit)
    return ProjectListResponse(
        items=[ProjectResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/search",
    response_model=ProjectListResponse,
    summary="Search public projects",
    description="Search public projects by title or description.",
)
async def search_public_projects(
    query: str = Query(..., min_length=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    """Search public projects."""
    service = ProjectService(db)
    items, total = await service.search_public_projects(query=query, skip=skip, limit=limit)
    return ProjectListResponse(
        items=[ProjectResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
    description="Return project details if it is public or owned by the authenticated user.",
)
async def get_project(
    project_id: uuid.UUID,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Return a project by its UUID."""
    service = ProjectService(db)
    project = await service.get_project(project_id, current_user=current_user)
    return ProjectResponse.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project",
    description="Update project metadata for projects owned by the authenticated user.",
)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Update a project."""
    service = ProjectService(db)
    project = await service.update_project(current_user, project_id, payload)
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    response_model=MessageResponse,
    summary="Delete a project",
    description="Soft delete a project owned by the authenticated user.",
)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Soft delete a project."""
    service = ProjectService(db)
    await service.delete_project(current_user, project_id)
    return MessageResponse(message="Project deleted successfully.")


@router.post(
    "/{project_id}/restore",
    response_model=ProjectResponse,
    summary="Restore a deleted project",
    description="Restore a previously soft-deleted project owned by the authenticated user.",
)
async def restore_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Restore a soft-deleted project."""
    service = ProjectService(db)
    project = await service.restore_project(current_user, project_id)
    return ProjectResponse.model_validate(project)


# ============================================================================
# Project Workspace & Files (VSCode IDE Integration)
# ============================================================================


@router.get(
    "/{project_id}/files",
    response_model=list[ProjectFileResponse],
    summary="List project files tree",
)
async def list_project_files(
    project_id: uuid.UUID,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectFileResponse]:
    await ProjectService(db).get_project(project_id, current_user)
    stmt = (
        select(ProjectFile)
        .where(ProjectFile.project_id == project_id)
        .order_by(ProjectFile.path.asc())
    )
    res = await db.execute(stmt)
    files = res.scalars().all()
    return [ProjectFileResponse.model_validate(f) for f in files]


@router.post(
    "/{project_id}/files",
    response_model=ProjectFileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project file or folder",
)
async def create_project_file(
    project_id: uuid.UUID,
    payload: ProjectFileCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectFileResponse:
    project = await ProjectService(db).get_project(project_id, current_user)
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Project owner access is required."
        )
    file_obj = ProjectFile(
        project_id=project_id,
        path=payload.path,
        name=payload.name,
        content=payload.content,
        is_directory=payload.is_directory,
        language=payload.language,
    )
    db.add(file_obj)
    await db.commit()
    await db.refresh(file_obj)
    return ProjectFileResponse.model_validate(file_obj)


@router.put(
    "/{project_id}/files/{file_id}",
    response_model=ProjectFileResponse,
    summary="Update a project file",
)
async def update_project_file(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    payload: ProjectFileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectFileResponse:
    project = await ProjectService(db).get_project(project_id, current_user)
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Project owner access is required."
        )
    stmt = select(ProjectFile).where(
        ProjectFile.id == file_id, ProjectFile.project_id == project_id
    )
    res = await db.execute(stmt)
    file_obj = res.scalar_one_or_none()
    if not file_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if payload.content is not None:
        file_obj.content = payload.content
    if payload.path is not None:
        file_obj.path = payload.path
    if payload.name is not None:
        file_obj.name = payload.name

    await db.commit()
    await db.refresh(file_obj)
    return ProjectFileResponse.model_validate(file_obj)


@router.delete(
    "/{project_id}/files/{file_id}",
    summary="Delete a project file",
)
async def delete_project_file(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    project = await ProjectService(db).get_project(project_id, current_user)
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Project owner access is required."
        )
    stmt = select(ProjectFile).where(
        ProjectFile.id == file_id, ProjectFile.project_id == project_id
    )
    res = await db.execute(stmt)
    file_obj = res.scalar_one_or_none()
    if file_obj:
        await db.delete(file_obj)
        await db.commit()
    return {"message": "File deleted successfully"}


@router.post(
    "/{project_id}/run",
    response_model=ExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute project code file",
)
async def run_project_file(
    project_id: uuid.UUID,
    payload: ExecutionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    project = await ProjectService(db).get_project(project_id, current_user)
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Project owner access is required."
        )
    if payload.project_id and payload.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project IDs differ."
        )
    return await ExecutionService(db).enqueue(
        current_user, payload.model_copy(update={"project_id": project_id})
    )
