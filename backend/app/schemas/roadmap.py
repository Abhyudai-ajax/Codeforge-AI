"""Pydantic schemas for Learning Roadmaps and Progress Tracking."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoadmapStageProblemBase(BaseModel):
    order: int = 0
    is_required: bool = True


class RoadmapStageProblemResponse(RoadmapStageProblemBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stage_id: UUID
    problem_id: UUID
    problem_title: str | None = None
    problem_slug: str | None = None
    problem_difficulty: str | None = None
    is_solved: bool = False


class RoadmapStageBase(BaseModel):
    title: str
    slug: str
    category_name: str
    description_md: str = ""
    order: int = 0


class RoadmapStageResponse(RoadmapStageBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    roadmap_id: UUID
    total_problems: int = 0
    solved_problems: int = 0
    problems: list[RoadmapStageProblemResponse] = []


class RoadmapBase(BaseModel):
    slug: str
    title: str
    description_md: str = ""
    is_published: bool = True
    is_default: bool = False
    order: int = 0


class RoadmapCreate(RoadmapBase):
    pass


class RoadmapResponse(RoadmapBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    stages: list[RoadmapStageResponse] = []


class UserRoadmapSelectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    roadmap_id: UUID
    is_active: bool
    selected_at: datetime
    last_activity_at: datetime
    roadmap: RoadmapResponse | None = None


class CategoryProgress(BaseModel):
    category: str
    total_problems: int
    solved_problems: int
    completion_percentage: float


class DifficultyProgress(BaseModel):
    difficulty: str
    total_problems: int
    solved_problems: int
    completion_percentage: float


class UserRoadmapProgressOverview(BaseModel):
    active_roadmap: RoadmapResponse | None = None
    total_roadmap_problems: int = 0
    solved_roadmap_problems: int = 0
    overall_completion_percentage: float = 0.0
    categories: list[CategoryProgress] = []
    difficulties: list[DifficultyProgress] = []
    weak_categories: list[str] = []


class ProblemRecommendation(BaseModel):
    problem_id: UUID
    title: str
    slug: str
    category: str
    difficulty: str
    reason: str
