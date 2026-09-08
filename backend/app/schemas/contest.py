"""Pydantic schemas for Contests, Submissions, Leaderboards, and User History."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.problem import ProblemResponse


class ContestProblemCreate(BaseModel):
    problem_id: UUID
    order: int = Field(default=0, ge=0)
    points: int = Field(default=100, ge=1)
    label: str = Field(min_length=1, max_length=10)


class ContestProblemResponse(BaseModel):
    id: UUID
    contest_id: UUID
    problem_id: UUID
    order: int
    points: int
    label: str
    problem: ProblemResponse | None = None
    model_config = ConfigDict(from_attributes=True)


class ContestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=100)
    description_md: str = Field(default="")
    start_time: datetime
    end_time: datetime
    is_published: bool = True
    problems: list[ContestProblemCreate] = Field(default_factory=list)


class ContestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description_md: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_published: bool | None = None
    problems: list[ContestProblemCreate] | None = None


class ContestListItem(BaseModel):
    id: UUID
    title: str
    slug: str
    start_time: datetime
    end_time: datetime
    is_published: bool
    status: str  # "upcoming" | "running" | "ended"
    participant_count: int = 0
    is_registered: bool = False
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ContestDetailResponse(ContestListItem):
    description_md: str
    problems: list[ContestProblemResponse] = Field(default_factory=list)


class ContestSubmissionCreate(BaseModel):
    problem_id: UUID
    language: str
    source_code: str = Field(min_length=1, max_length=200_000)


class ContestLeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    username: str
    full_name: str | None
    total_score: int
    total_penalty: int
    problems_solved: int
    model_config = ConfigDict(from_attributes=True)


class ContestLeaderboardPage(BaseModel):
    items: list[ContestLeaderboardEntry]
    total: int
    offset: int
    limit: int


class UserContestHistoryItem(BaseModel):
    contest_id: UUID
    title: str
    slug: str
    start_time: datetime
    end_time: datetime
    registered_at: datetime
    rank: int | None = None
    total_score: int = 0
    total_penalty: int = 0
    problems_solved: int = 0
