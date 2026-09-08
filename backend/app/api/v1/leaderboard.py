"""Platform-wide leaderboard routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.leaderboard import LeaderboardEntry, LeaderboardPage, MyLeaderboardStanding
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get(
    "",
    response_model=LeaderboardPage,
    summary="Global leaderboard",
    description=(
        "Ranks every user with at least one accepted submission by a difficulty-weighted "
        "point total (easy=10, medium=30, hard=50), tied-broken by solved count then username."
    ),
)
async def get_leaderboard(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardPage:
    items, total = await LeaderboardService(db).page(offset, limit)
    return LeaderboardPage(
        items=[LeaderboardEntry(**vars(entry)) for entry in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/me",
    response_model=MyLeaderboardStanding,
    summary="My leaderboard standing",
    description="The authenticated user's own rank, solved count and points.",
)
async def get_my_standing(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MyLeaderboardStanding:
    entry = await LeaderboardService(db).standing_for(current_user.id)
    if entry is None:
        return MyLeaderboardStanding(rank=None, solved_count=0, points=0)
    return MyLeaderboardStanding(
        rank=entry.rank, solved_count=entry.solved_count, points=entry.points
    )
