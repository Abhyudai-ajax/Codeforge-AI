"""Pydantic schemas for Mock Interview System."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.interview import InterviewStatus, InterviewType


class StartInterviewRequest(BaseModel):
    type: InterviewType = InterviewType.DSA
    title: str = "Mock Interview Session"
    time_limit_minutes: int = Field(default=45, ge=10, le=180)


class InterviewAnswerRequest(BaseModel):
    question_id: UUID
    answer_text: str = ""


class InterviewCodeSubmissionRequest(BaseModel):
    question_id: UUID
    submission_id: UUID


class InterviewQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    problem_id: UUID | None = None
    question_text: str
    question_type: str
    order: int
    points: int
    problem_title: str | None = None


class InterviewAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_id: UUID
    session_id: UUID
    user_id: UUID
    answer_text: str
    submission_id: UUID | None = None
    score: float
    feedback_text: str
    submitted_at: datetime


class InterviewFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    overall_score: float
    strengths: list[str] = []
    improvements: list[str] = []
    summary_md: str
    evaluated_at: datetime


class InterviewSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    type: InterviewType
    title: str
    status: InterviewStatus
    score: float | None = None
    time_limit_minutes: int
    start_time: datetime | None = None
    end_time: datetime | None = None
    created_at: datetime
    questions: list[InterviewQuestionResponse] = []
    answers: list[InterviewAnswerResponse] = []
    feedback: InterviewFeedbackResponse | None = None
