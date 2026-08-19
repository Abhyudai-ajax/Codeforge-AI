"""Pydantic schemas for Project Files (VSCode Workspace)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProjectFileBase(BaseModel):
    """Base schema for Project File."""

    path: str
    name: str
    content: str = ""
    is_directory: bool = False
    language: str = "python"


class ProjectFileCreate(ProjectFileBase):
    """Schema for creating a project file or folder."""

    pass


class ProjectFileUpdate(BaseModel):
    """Schema for updating a project file content or name/path."""

    content: Optional[str] = None
    path: Optional[str] = None
    name: Optional[str] = None


class ProjectFileResponse(ProjectFileBase):
    """Schema for returning a project file item."""

    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
