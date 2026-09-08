"""Database models for Mock Interview System."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.problem import Problem, Submission
    from app.models.user import User


class InterviewType(str, Enum):
    """Types of interview sessions."""

    DSA = "dsa"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"


class InterviewStatus(str, Enum):
    """Lifecycle status of an interview session."""

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InterviewSession(Base):
    """Represents a mock interview session for a user."""

    __tablename__ = "interview_sessions"
    __table_args__ = (Index("ix_interview_sessions_user_status", "user_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[InterviewType] = mapped_column(
        SQLEnum(InterviewType), default=InterviewType.DSA, nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, default="Mock Interview Session"
    )
    status: Mapped[InterviewStatus] = mapped_column(
        SQLEnum(InterviewStatus), default=InterviewStatus.CREATED, nullable=False, index=True
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=45, nullable=False)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship("User")
    questions: Mapped[list[InterviewQuestion]] = relationship(
        "InterviewQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.order",
        lazy="selectin",
    )
    answers: Mapped[list[InterviewAnswer]] = relationship(
        "InterviewAnswer",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    feedback: Mapped[InterviewFeedback | None] = relationship(
        "InterviewFeedback",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class InterviewQuestion(Base):
    """A question presented within an interview session."""

    __tablename__ = "interview_questions"
    __table_args__ = (Index("ix_interview_questions_session_order", "session_id", "order"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False
    )
    problem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("problems.id", ondelete="SET NULL"), nullable=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), default="coding", nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    session: Mapped[InterviewSession] = relationship("InterviewSession", back_populates="questions")
    problem: Mapped[Problem | None] = relationship("Problem", lazy="selectin")
    answers: Mapped[list[InterviewAnswer]] = relationship(
        "InterviewAnswer", back_populates="question", cascade="all, delete-orphan", lazy="selectin"
    )


class InterviewAnswer(Base):
    """User answer / code submission for an interview question."""

    __tablename__ = "interview_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    answer_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    submission_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="SET NULL"), nullable=True
    )
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    feedback_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    question: Mapped[InterviewQuestion] = relationship(
        "InterviewQuestion", back_populates="answers"
    )
    session: Mapped[InterviewSession] = relationship("InterviewSession", back_populates="answers")
    submission: Mapped[Submission | None] = relationship("Submission", lazy="selectin")


class InterviewFeedback(Base):
    """Evaluated feedback and summary report for an interview session."""

    __tablename__ = "interview_feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    strengths: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    improvements: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    summary_md: Mapped[str] = mapped_column(Text, default="", nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[InterviewSession] = relationship("InterviewSession", back_populates="feedback")
