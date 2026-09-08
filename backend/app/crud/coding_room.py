"""Database repository for coding rooms."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.coding_room import CodingRoom, RoomMemberRole, RoomMembership


class CodingRoomCRUD:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, room_id: UUID, include_deleted: bool = False) -> CodingRoom | None:
        statement = (
            select(CodingRoom)
            .where(CodingRoom.id == room_id)
            .options(selectinload(CodingRoom.members))
        )
        if not include_deleted:
            statement = statement.where(CodingRoom.deleted_at.is_(None))
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def list_accessible(
        self, user_id: UUID, skip: int, limit: int
    ) -> tuple[list[CodingRoom], int]:
        accessible = (
            (CodingRoom.is_public.is_(True))
            | (CodingRoom.owner_id == user_id)
            | (CodingRoom.members.any(RoomMembership.user_id == user_id))
        )
        statement = select(CodingRoom).where(CodingRoom.deleted_at.is_(None), accessible)
        total = (
            await self.session.execute(select(func.count()).select_from(statement.subquery()))
        ).scalar_one()
        rooms = (
            (
                await self.session.execute(
                    statement.order_by(CodingRoom.created_at.desc()).offset(skip).limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return list(rooms), total

    async def get_membership(self, room_id: UUID, user_id: UUID) -> RoomMembership | None:
        return (
            await self.session.execute(
                select(RoomMembership).where(
                    RoomMembership.room_id == room_id, RoomMembership.user_id == user_id
                )
            )
        ).scalar_one_or_none()

    async def create(self, room: CodingRoom) -> CodingRoom:
        self.session.add(room)
        await self.session.flush()
        self.session.add(
            RoomMembership(room_id=room.id, user_id=room.owner_id, role=RoomMemberRole.OWNER)
        )
        await self.session.commit()
        created = await self.get(room.id)
        if created is None:
            raise RuntimeError("Created coding room could not be loaded.")
        return created

    async def add_member(self, membership: RoomMembership) -> RoomMembership:
        self.session.add(membership)
        await self.session.commit()
        await self.session.refresh(membership)
        return membership

    async def remove_member(self, membership: RoomMembership) -> None:
        await self.session.delete(membership)
        await self.session.commit()

    async def save(self, room: CodingRoom) -> CodingRoom:
        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room)
        return room

    async def touch_member(self, membership: RoomMembership) -> None:
        membership.last_seen_at = datetime.now(UTC)
        await self.session.commit()
