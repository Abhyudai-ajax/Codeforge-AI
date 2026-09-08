"""DSA problems, immutable test cases, submissions, and user progress."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
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
from sqlalchemy.types import JSON as GenericJSON

from app.core.database import Base


class ProblemDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SubmissionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    ACCEPTED = "accepted"
    WRONG_ANSWER = "wrong_answer"
    COMPILATION_ERROR = "compilation_error"
    RUNTIME_ERROR = "runtime_error"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    FAILED = "failed"


class Problem(Base):
    """Represents a LeetCode-style DSA problem."""

    __tablename__ = "problems"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    difficulty: Mapped[ProblemDifficulty] = mapped_column(SQLEnum(ProblemDifficulty), index=True)

    description_md: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    input_description: Mapped[str] = mapped_column(Text, default="", server_default="")
    output_description: Mapped[str] = mapped_column(Text, default="", server_default="")
    starter_code: Mapped[dict[str, str]] = mapped_column(GenericJSON, default=dict)
    constraints: Mapped[list[str]] = mapped_column(GenericJSON, default=list)
    examples: Mapped[list[dict]] = mapped_column(GenericJSON, default=list)
    supported_languages: Mapped[list[str]] = mapped_column(GenericJSON, default=lambda: ["python"])
    editorial_md: Mapped[str | None] = mapped_column(Text)

    time_limit_ms: Mapped[int] = mapped_column(
        Integer,
        default=2000,
        nullable=False,
    )

    memory_limit_mb: Mapped[int] = mapped_column(
        Integer,
        default=256,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    test_cases: Mapped[list["TestCase"]] = relationship(
        "TestCase", back_populates="problem", cascade="all, delete-orphan", lazy="selectin"
    )
    tags: Mapped[list["ProblemTag"]] = relationship(
        secondary="problem_tag_links", back_populates="problems", lazy="selectin"
    )
    submissions: Mapped[list["Submission"]] = relationship(
        "Submission",
        back_populates="problem",
        cascade="all, delete-orphan",
        lazy="selectin",
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


class TestCase(Base):
    __test__ = False
    __tablename__ = "test_cases"
    __table_args__ = (Index("ix_test_cases_problem_public", "problem_id", "is_public"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE")
    )
    input_data: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    problem: Mapped[Problem] = relationship(back_populates="test_cases")


class ProblemTag(Base):
    __tablename__ = "problem_tags"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    problems: Mapped[list[Problem]] = relationship(
        secondary="problem_tag_links", back_populates="tags"
    )


class ProblemTagLink(Base):
    __tablename__ = "problem_tag_links"
    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("problem_tags.id", ondelete="CASCADE"), primary_key=True
    )


class Submission(Base):
    """Represents a solution submission for a problem."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    problem: Mapped[Problem] = relationship(
        "Problem",
        back_populates="submissions",
    )

    user = relationship("User", back_populates="submissions")

    room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_rooms.id", ondelete="SET NULL")
    )
    language: Mapped[str] = mapped_column(String(30))
    source_code: Mapped[str] = mapped_column(Text)
    status: Mapped[SubmissionStatus] = mapped_column(
        SQLEnum(SubmissionStatus), default=SubmissionStatus.QUEUED, index=True
    )
    runtime_ms: Mapped[int | None] = mapped_column(Integer)
    memory_kb: Mapped[int | None] = mapped_column(Integer)
    passed_test_count: Mapped[int] = mapped_column(Integer, default=0)
    total_test_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=0)
    output: Mapped[str] = mapped_column(Text, default="", server_default="")
    error_output: Mapped[str] = mapped_column(Text, default="", server_default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserProblemProgress(Base):
    __tablename__ = "user_problem_progress"
    __table_args__ = (UniqueConstraint("user_id", "problem_id", name="uq_user_problem_progress"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    accepted_submissions: Mapped[int] = mapped_column(Integer, default=0)
    failed_submissions: Mapped[int] = mapped_column(Integer, default=0)
    first_solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
