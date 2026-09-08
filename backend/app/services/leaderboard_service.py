"""Platform-wide leaderboard.

Ranks every user who has solved at least one problem by a difficulty-weighted
point total (easy=10, medium=30, hard=50), tie-broken by solved count then
username. The catalog is small (dozens of problems), so the whole ranked set is
computed in Python from one aggregate query rather than pushed through a SQL
window function — simpler, and fast enough at this scale.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.problem import Problem, ProblemDifficulty, UserProblemProgress
from app.models.user import User

POINTS_BY_DIFFICULTY = {
    ProblemDifficulty.EASY: 10,
    ProblemDifficulty.MEDIUM: 30,
    ProblemDifficulty.HARD: 50,
}


@dataclass(frozen=True)
class RankedUser:
    rank: int
    user_id: UUID
    username: str
    full_name: str | None
    avatar_url: str | None
    solved_count: int
    points: int


class LeaderboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _ranked(self) -> list[RankedUser]:
        points_expr = func.sum(
            case(
                *(
                    (Problem.difficulty == difficulty, weight)
                    for difficulty, weight in POINTS_BY_DIFFICULTY.items()
                ),
                else_=0,
            )
        )
        solved_count_expr = func.count(func.distinct(UserProblemProgress.problem_id))
        stmt = (
            select(
                User.id,
                User.username,
                User.full_name,
                User.avatar_url,
                solved_count_expr.label("solved_count"),
                points_expr.label("points"),
            )
            .join(UserProblemProgress, UserProblemProgress.user_id == User.id)
            .join(Problem, Problem.id == UserProblemProgress.problem_id)
            .where(UserProblemProgress.first_solved_at.isnot(None))
            .group_by(User.id, User.username, User.full_name, User.avatar_url)
            .order_by(points_expr.desc(), solved_count_expr.desc(), User.username.asc())
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            RankedUser(
                rank=index,
                user_id=row.id,
                username=row.username,
                full_name=row.full_name,
                avatar_url=row.avatar_url,
                solved_count=row.solved_count,
                points=row.points or 0,
            )
            for index, row in enumerate(rows, start=1)
        ]

    async def page(self, offset: int, limit: int) -> tuple[list[RankedUser], int]:
        ranked = await self._ranked()
        return ranked[offset : offset + limit], len(ranked)

    async def standing_for(self, user_id: UUID) -> RankedUser | None:
        ranked = await self._ranked()
        return next((entry for entry in ranked if entry.user_id == user_id), None)
