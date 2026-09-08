"""Business rules for persisted coding rooms."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.coding_room import CodingRoomCRUD
from app.models.coding_room import CodingRoom, RoomMemberRole, RoomMembership
from app.models.user import User
from app.schemas.coding_room import CodingRoomCreate, CodingRoomUpdate, RoomMemberCreate


class CodingRoomService:
    def __init__(self, session: AsyncSession) -> None:
        self.crud = CodingRoomCRUD(session)

    async def create(self, user: User, data: CodingRoomCreate) -> CodingRoom:
        return await self.crud.create(CodingRoom(owner_id=user.id, **data.model_dump()))

    async def get_accessible(self, room_id, user: User | None) -> CodingRoom:
        room = await self.crud.get(room_id)
        if room is None:
            raise HTTPException(status_code=404, detail="Coding room not found.")
        membership = await self.crud.get_membership(room.id, user.id) if user else None
        if not room.is_public and membership is None and (user is None or room.owner_id != user.id):
            raise HTTPException(
                status_code=403, detail="You do not have access to this coding room."
            )
        return room

    async def require_member(self, room_id, user: User, write: bool = False) -> RoomMembership:
        room = await self.get_accessible(room_id, user)
        membership = await self.crud.get_membership(room.id, user.id)
        if membership is None:
            raise HTTPException(
                status_code=403, detail="Join this coding room before collaborating."
            )
        if write and membership.role == RoomMemberRole.VIEWER:
            raise HTTPException(status_code=403, detail="Editor access is required.")
        return membership

    async def require_owner(self, room_id, user: User) -> CodingRoom:
        room = await self.get_accessible(room_id, user)
        if room.owner_id != user.id:
            raise HTTPException(status_code=403, detail="Coding room owner access is required.")
        return room

    async def update(self, room_id, user: User, data: CodingRoomUpdate) -> CodingRoom:
        room = await self.require_owner(room_id, user)
        for key, value in data.model_dump(exclude_none=True).items():
            setattr(room, key, value)
        return await self.crud.save(room)

    async def join(self, room_id, user: User) -> RoomMembership:
        room = await self.get_accessible(room_id, user)
        existing = await self.crud.get_membership(room.id, user.id)
        if existing:
            return existing
        if not room.is_public:
            raise HTTPException(
                status_code=403, detail="An owner must invite you to this private room."
            )
        return await self.crud.add_member(RoomMembership(room_id=room.id, user_id=user.id))

    async def add_member(self, room_id, owner: User, data: RoomMemberCreate) -> RoomMembership:
        room = await self.require_owner(room_id, owner)
        existing = await self.crud.get_membership(room.id, data.user_id)
        if existing:
            raise HTTPException(status_code=409, detail="User is already a room member.")
        if data.role == RoomMemberRole.OWNER:
            raise HTTPException(
                status_code=422,
                detail="Room ownership cannot be delegated through membership creation.",
            )
        return await self.crud.add_member(RoomMembership(room_id=room.id, **data.model_dump()))

    async def leave(self, room_id, user: User) -> None:
        room = await self.get_accessible(room_id, user)
        membership = await self.crud.get_membership(room.id, user.id)
        if membership is None:
            raise HTTPException(status_code=404, detail="Room membership not found.")
        if membership.role == RoomMemberRole.OWNER:
            raise HTTPException(
                status_code=400,
                detail="The room owner cannot leave; transfer ownership or delete the room.",
            )
        await self.crud.remove_member(membership)

    async def update_document(
        self, room_id, user: User, document: dict, version: int
    ) -> CodingRoom:
        await self.require_member(room_id, user, write=True)
        room = await self.crud.get(room_id)
        if room is None:
            raise HTTPException(status_code=404, detail="Coding room not found.")
        if version != room.version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Room document version conflict."
            )
        room.document = document
        room.version += 1
        return await self.crud.save(room)
