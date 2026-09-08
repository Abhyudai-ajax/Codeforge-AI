"""Project model definition using SQLAlchemy 2.0 declarative style."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project_file import ProjectFile
    from app.models.user import User


class ProjectVisibility(str, Enum):
    """Visibility options for a project."""

    PRIVATE = "private"
    PUBLIC = "public"


class Project(Base):
    """Represents a coding project."""

    __tablename__ = "projects"

    __table_args__ = (Index("ix_projects_owner_visibility", "owner_id", "visibility"),)

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Owner
    # ==========================================================

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    owner: Mapped[User] = relationship(
        "User",
        back_populates="projects",
        lazy="selectin",
    )

    files: Mapped[list["ProjectFile"]] = relationship(
        "ProjectFile",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # ==========================================================
    # Basic Information
    # ==========================================================

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    language: Mapped[str] = mapped_column(
        String(50),
        default="python",
        nullable=False,
    )

    visibility: Mapped[ProjectVisibility] = mapped_column(
        SQLEnum(ProjectVisibility),
        default=ProjectVisibility.PRIVATE,
        nullable=False,
    )

    # ==========================================================
    # Git Repository
    # ==========================================================

    github_repo: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    github_branch: Mapped[str | None] = mapped_column(
        String(100),
        default="main",
        nullable=True,
    )

    # ==========================================================
    # Statistics
    # ==========================================================

    stars: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    forks: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    views: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    # ==========================================================
    # Soft Delete
    # ==========================================================

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ==========================================================
    # Timestamps
    # ==========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ==========================================================
    # Helper Methods
    # ==========================================================

    @property
    def is_public(self) -> bool:
        return self.visibility == ProjectVisibility.PUBLIC

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def __repr__(self) -> str:
        return (
            f"<Project("
            f"id={self.id}, "
            f"title='{self.title}', "
            f"owner_id={self.owner_id}"
            f")>"
        )
