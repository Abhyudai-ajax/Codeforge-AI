"""Contest and Leaderboard SQLAlchemy models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Contest(Base):
    __tablename__ = "contests"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    created_by = relationship("User", foreign_keys=[created_by_id])
    problems = relationship(
        "ContestProblem",
        back_populates="contest",
        cascade="all, delete-orphan",
        order_by="ContestProblem.order",
    )
    registrations = relationship(
        "ContestRegistration", back_populates="contest", cascade="all, delete-orphan"
    )
    participants = relationship(
        "ContestParticipant", back_populates="contest", cascade="all, delete-orphan"
    )


class ContestProblem(Base):
    __tablename__ = "contest_problems"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    contest_id: Mapped[UUID] = mapped_column(
        ForeignKey("contests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    problem_id: Mapped[UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    label: Mapped[str] = mapped_column(String(10), nullable=False, default="A")

    __table_args__ = (
        UniqueConstraint("contest_id", "problem_id", name="uq_contest_problem"),
        UniqueConstraint("contest_id", "label", name="uq_contest_label"),
    )

    contest = relationship("Contest", back_populates="problems")
    problem = relationship("Problem")


class ContestRegistration(Base):
    __tablename__ = "contest_registrations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    contest_id: Mapped[UUID] = mapped_column(
        ForeignKey("contests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("contest_id", "user_id", name="uq_contest_user_registration"),
    )

    contest = relationship("Contest", back_populates="registrations")
    user = relationship("User")


class ContestSubmission(Base):
    __tablename__ = "contest_submissions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    contest_id: Mapped[UUID] = mapped_column(
        ForeignKey("contests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    problem_id: Mapped[UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    submission_id: Mapped[UUID] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    contest = relationship("Contest")
    problem = relationship("Problem")
    submission = relationship("Submission")
    user = relationship("User")


class ContestParticipant(Base):
    __tablename__ = "contest_participants"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    contest_id: Mapped[UUID] = mapped_column(
        ForeignKey("contests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_penalty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    problems_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("contest_id", "user_id", name="uq_contest_participant"),
        Index("idx_contest_leaderboard", "contest_id", total_score.desc(), total_penalty.asc()),
    )

    contest = relationship("Contest", back_populates="participants")
    user = relationship("User")
