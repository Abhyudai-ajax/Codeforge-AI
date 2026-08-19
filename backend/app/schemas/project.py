"""
Project request / response schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.project import ProjectVisibility


class ProjectBase(BaseModel):
    """Shared project fields."""

    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Project title",
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    language: str = Field(
        default="python",
        max_length=50,
    )

    visibility: ProjectVisibility = ProjectVisibility.PRIVATE

    github_repo: str | None = None
    github_branch: str | None = "main"


class ProjectCreate(ProjectBase):
    """Request body for creating a project."""

    pass


class ProjectUpdate(BaseModel):
    """Partial update schema."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    language: str | None = None
    visibility: ProjectVisibility | None = None
    github_repo: str | None = None
    github_branch: str | None = None


class ProjectResponse(ProjectBase):
    """Project returned by the API."""

    id: uuid.UUID
    owner_id: uuid.UUID

    stars: int
    forks: int
    views: int

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """Paginated project list."""

    items: list[ProjectResponse]
    total: int
    skip: int
    limit: int


class MessageResponse(BaseModel):
    """Generic success message."""

    message: str
