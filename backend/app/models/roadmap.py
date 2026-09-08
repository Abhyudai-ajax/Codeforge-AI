"""Database models for Learning Roadmaps, Stages, Problems, and User Selections."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Roadmap(Base):
    """Represents a curriculum or learning roadmap (e.g. DSA Master Class)."""

    __tablename__ = "roadmaps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description_md: Mapped[str] = mapped_column(Text, default="")
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    stages: Mapped[list[RoadmapStage]] = relationship(
        "RoadmapStage",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapStage.order",
        lazy="selectin",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class RoadmapStage(Base):
    """Represents a stage/topic inside a roadmap (e.g. Arrays & Hashing)."""

    __tablename__ = "roadmap_stages"
    __table_args__ = (Index("ix_roadmap_stages_roadmap_id_order", "roadmap_id", "order"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    category_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description_md: Mapped[str] = mapped_column(Text, default="")
    order: Mapped[int] = mapped_column(Integer, default=0)

    roadmap: Mapped[Roadmap] = relationship("Roadmap", back_populates="stages")
    problems: Mapped[list[RoadmapStageProblem]] = relationship(
        "RoadmapStageProblem",
        back_populates="stage",
        cascade="all, delete-orphan",
        order_by="RoadmapStageProblem.order",
        lazy="selectin",
    )


class RoadmapStageProblem(Base):
    """Linkage between a roadmap stage and a DSA problem."""

    __tablename__ = "roadmap_stage_problems"
    __table_args__ = (
        Index("ix_roadmap_stage_problems_stage_id_order", "stage_id", "order"),
        UniqueConstraint("stage_id", "problem_id", name="uq_stage_problem"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roadmap_stages.id", ondelete="CASCADE"),
        nullable=False,
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
    )
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)

    stage: Mapped[RoadmapStage] = relationship("RoadmapStage", back_populates="problems")
    problem = relationship("Problem", lazy="selectin")


class UserRoadmapSelection(Base):
    """Tracks which roadmap a user has currently selected/enrolled in."""

    __tablename__ = "user_roadmap_selections"
    __table_args__ = (UniqueConstraint("user_id", "roadmap_id", name="uq_user_roadmap_selection"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    selected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="roadmap_selections")
    roadmap: Mapped[Roadmap] = relationship("Roadmap")
