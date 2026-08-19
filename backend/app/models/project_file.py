"""ProjectFile model definition using SQLAlchemy 2.0 declarative style."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectFile(Base):
    """Represents a file or directory within a Project workspace."""

    __tablename__ = "project_files"

    __table_args__ = (
        Index("ix_project_files_proj_path", "project_id", "path", unique=True),
    )


    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    is_directory: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(30),
        default="python",
        nullable=False,
    )

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
