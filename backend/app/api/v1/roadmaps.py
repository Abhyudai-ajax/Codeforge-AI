"""API router for Learning Roadmaps and Personalized Recommendations."""

from __future__ import annotations

import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.roadmap import (
    CategoryProgress,
    ProblemRecommendation,
    RoadmapResponse,
    UserRoadmapProgressOverview,
    UserRoadmapSelectionResponse,
)
from app.services.roadmap_service import roadmap_service

router = APIRouter(prefix="/roadmaps", tags=["Roadmaps"])


@router.get("/", response_model=list[RoadmapResponse])
async def list_roadmaps(
    db: AsyncSession = Depends(get_db),
) -> Sequence[RoadmapResponse]:
    """List all published learning roadmaps."""
    roadmaps = await roadmap_service.list_roadmaps(db)
    results: list[RoadmapResponse] = []
    for rm in roadmaps:
        detail = await roadmap_service.get_roadmap(db, rm.id)
        if detail:
            results.append(detail)
    return results


@router.get("/me", response_model=RoadmapResponse)
async def get_my_roadmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoadmapResponse:
    """Get authenticated user's active roadmap with personalized progress."""
    rm = await roadmap_service.get_user_active_roadmap(db, current_user.id)
    if not rm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default or active roadmap available",
        )
    return rm


@router.get("/progress", response_model=UserRoadmapProgressOverview)
async def get_roadmap_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRoadmapProgressOverview:
    """Get authenticated user's overall roadmap, category, and difficulty progress."""
    return await roadmap_service.get_user_progress_overview(db, current_user.id)


@router.get("/categories", response_model=list[CategoryProgress])
async def get_category_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CategoryProgress]:
    """Get authenticated user's DSA category progress breakdown."""
    overview = await roadmap_service.get_user_progress_overview(db, current_user.id)
    return overview.categories


@router.get("/recommendations", response_model=list[ProblemRecommendation])
async def get_recommended_problems(
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProblemRecommendation]:
    """Get personalized problem recommendations for authenticated user."""
    return await roadmap_service.get_recommendations(db, current_user.id, limit=limit)


@router.post("/refresh", response_model=UserRoadmapProgressOverview)
async def refresh_roadmap_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRoadmapProgressOverview:
    """Force recalculation of authenticated user's roadmap progress and recommendations."""
    return await roadmap_service.get_user_progress_overview(db, current_user.id)


@router.get("/{identifier}", response_model=RoadmapResponse)
async def get_roadmap(
    identifier: str,
    db: AsyncSession = Depends(get_db),
) -> RoadmapResponse:
    """Get detailed roadmap structure by ID or slug."""
    rm = await roadmap_service.get_roadmap(db, identifier)
    if not rm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Roadmap '{identifier}' not found",
        )
    return rm


@router.post("/select/{roadmap_id}", response_model=UserRoadmapSelectionResponse)
async def select_roadmap(
    roadmap_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRoadmapSelectionResponse:
    """Select / enroll in a learning roadmap for authenticated user."""
    try:
        selection = await roadmap_service.select_roadmap(db, current_user.id, roadmap_id)
        rm_detail = await roadmap_service.get_roadmap(db, roadmap_id, user_id=current_user.id)
        return UserRoadmapSelectionResponse(
            id=selection.id,
            user_id=selection.user_id,
            roadmap_id=selection.roadmap_id,
            is_active=selection.is_active,
            selected_at=selection.selected_at,
            last_activity_at=selection.last_activity_at,
            roadmap=rm_detail,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
