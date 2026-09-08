"""Contest and Leaderboard API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user, get_current_user_optional, require_role
from app.models.user import User
from app.schemas.contest import (
    ContestCreate,
    ContestDetailResponse,
    ContestLeaderboardPage,
    ContestListItem,
    ContestSubmissionCreate,
    ContestUpdate,
    UserContestHistoryItem,
)
from app.schemas.problem import SubmissionResponse
from app.services.contest_service import ContestService

router = APIRouter(prefix="/contests", tags=["Contests & Leaderboards"])


@router.get("", response_model=list[ContestListItem])
async def list_contests(
    status_filter: str | None = Query(
        default=None, alias="status", pattern=r"^(upcoming|running|ended)$"
    ),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> list[ContestListItem]:
    items, _ = await ContestService(db).list_contests(
        status_filter=status_filter,
        current_user=current_user,
        offset=offset,
        limit=limit,
    )
    return items


@router.post("", response_model=ContestDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_contest(
    payload: ContestCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    contest = await ContestService(db).create(payload, current_user)
    return await ContestService(db).get_contest_detail(contest.id, current_user)


@router.get("/my-history", response_model=list[UserContestHistoryItem])
@router.get("/users/me/contests", response_model=list[UserContestHistoryItem])
async def user_contest_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserContestHistoryItem]:
    return await ContestService(db).get_user_contest_history(current_user)


@router.get("/{contest_id}", response_model=ContestDetailResponse)
async def get_contest(
    contest_id: UUID,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ContestService(db).get_contest_detail(contest_id, current_user)


@router.patch("/{contest_id}", response_model=ContestDetailResponse)
async def update_contest(
    contest_id: UUID,
    payload: ContestUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    contest = await ContestService(db).update(contest_id, payload)
    return await ContestService(db).get_contest_detail(contest.id, current_user)


@router.delete("/{contest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contest(
    contest_id: UUID,
    _: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await ContestService(db).delete(contest_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{contest_id}/register", status_code=status.HTTP_200_OK)
async def register_contest(
    contest_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ContestService(db).register(contest_id, current_user)


@router.post("/{contest_id}/unregister", status_code=status.HTTP_200_OK)
async def unregister_contest(
    contest_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ContestService(db).unregister(contest_id, current_user)


@router.post(
    "/{contest_id}/submissions",
    response_model=SubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_contest_submission(
    contest_id: UUID,
    payload: ContestSubmissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    return await ContestService(db).submit_contest_solution(contest_id, payload, current_user)


@router.get("/{contest_id}/leaderboard", response_model=ContestLeaderboardPage)
async def contest_leaderboard(
    contest_id: UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ContestLeaderboardPage:
    return await ContestService(db).get_leaderboard(contest_id, offset=offset, limit=limit)
