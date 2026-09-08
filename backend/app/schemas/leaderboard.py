"""Platform-wide leaderboard, ranked by solved problems and difficulty-weighted points."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    username: str
    full_name: str | None
    avatar_url: str | None
    solved_count: int
    points: int
    model_config = ConfigDict(from_attributes=True)


class LeaderboardPage(BaseModel):
    items: list[LeaderboardEntry]
    total: int
    offset: int
    limit: int


class MyLeaderboardStanding(BaseModel):
    rank: int | None
    solved_count: int
    points: int
