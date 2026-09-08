"""Pydantic contracts for coding rooms and collaboration events."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.coding_room import RoomMemberRole


class CodingRoomCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    is_public: bool = False
    document: dict[str, Any] = Field(default_factory=dict)


class CodingRoomUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    is_public: bool | None = None


class RoomMemberCreate(BaseModel):
    user_id: UUID
    role: RoomMemberRole = RoomMemberRole.EDITOR


class RoomMemberResponse(BaseModel):
    user_id: UUID
    role: RoomMemberRole
    joined_at: datetime
    last_seen_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CodingRoomResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    description: str | None
    is_public: bool
    document: dict[str, Any]
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CodingRoomListResponse(BaseModel):
    items: list[CodingRoomResponse]
    total: int
    skip: int
    limit: int


class RoomDocumentUpdate(BaseModel):
    document: dict[str, Any]
    version: int = Field(ge=0)
