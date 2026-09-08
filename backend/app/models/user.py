"""User model definition using SQLAlchemy 2.0 declarative style."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.coding_room import CodingRoom, RoomMembership
    from app.models.problem import Submission
    from app.models.project import Project
    from app.models.roadmap import UserRoadmapSelection


class UserRole(str, Enum):
    """User role enumeration."""

    USER = "user"
    ADMIN = "admin"


class User(Base):
    """Represents an application user."""

    __tablename__ = "users"

    # ==========================
    # Primary Key
    # ==========================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================
    # Basic Information
    # ==========================
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ==========================
    # Role & Status
    # ==========================
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.USER,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ==========================
    # OAuth (GitHub)
    # ==========================
    github_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True,
    )

    github_username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ==========================
    # Relationships
    # ==========================
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    submissions: Mapped[list["Submission"]] = relationship(
        "Submission",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    coding_rooms: Mapped[list["CodingRoom"]] = relationship("CodingRoom", back_populates="owner")
    room_memberships: Mapped[list["RoomMembership"]] = relationship(
        "RoomMembership", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    roadmap_selections: Mapped[list["UserRoadmapSelection"]] = relationship(
        "UserRoadmapSelection",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # ==========================
    # Timestamps
    # ==========================
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

    # ==========================
    # Utility Methods
    # ==========================
    def __repr__(self) -> str:
        return (
            f"<User("
            f"id={self.id}, "
            f"username='{self.username}', "
            f"email='{self.email}', "
            f"role='{self.role.value}'"
            f")>"
        )
