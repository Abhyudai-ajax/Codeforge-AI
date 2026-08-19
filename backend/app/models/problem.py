"""Problem and Submission models definition using SQLAlchemy 2.0 declarative style."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON as GenericJSON

from app.core.database import Base



class ProblemDifficulty(str, Enum):
    """Problem difficulty levels."""

    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class SubmissionStatus(str, Enum):
    """Status of a code submission."""

    ACCEPTED = "Accepted"
    WRONG_ANSWER = "Wrong Answer"
    TIME_LIMIT_EXCEEDED = "Time Limit Exceeded"
    RUNTIME_ERROR = "Runtime Error"
    COMPILE_ERROR = "Compile Error"
    PENDING = "Pending"


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

    difficulty: Mapped[str] = mapped_column(
        String(20),
        default=ProblemDifficulty.EASY.value,
        nullable=False,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        default="Arrays",
        nullable=False,
        index=True,
    )

    description_md: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    starter_code: Mapped[Dict[str, str]] = mapped_column(
        GenericJSON,
        default=dict,
        nullable=False,
    )

    test_cases: Mapped[List[Dict[str, Any]]] = mapped_column(
        GenericJSON,
        default=list,
        nullable=False,
    )

    constraints: Mapped[List[str]] = mapped_column(
        GenericJSON,
        default=list,
        nullable=False,
    )

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

    acceptance_rate: Mapped[float] = mapped_column(
        Float,
        default=65.0,
        nullable=False,
    )

    submissions: Mapped[List["Submission"]] = relationship(
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

    language: Mapped[str] = mapped_column(
        String(30),
        default="python",
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default=SubmissionStatus.PENDING.value,
        nullable=False,
    )

    passed_test_cases: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    total_test_cases: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    runtime_ms: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    memory_mb: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
