"""HTTP API for coding rooms; collaboration messages use the room WebSocket."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.core.security import decode_token
from app.dependencies.auth import get_current_active_user, get_current_user_optional
from app.models.user import User
from app.schemas.coding_room import (
    CodingRoomCreate,
    CodingRoomListResponse,
    CodingRoomResponse,
    CodingRoomUpdate,
    RoomMemberCreate,
    RoomMemberResponse,
)
from app.services.auth_service import AuthService
from app.services.coding_room_service import CodingRoomService
from app.websocket.coding_rooms import room_connections

router = APIRouter(prefix="/rooms", tags=["Coding Rooms"])


@router.post("/", response_model=CodingRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: CodingRoomCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CodingRoomResponse:
    return CodingRoomResponse.model_validate(await CodingRoomService(db).create(user, payload))


@router.get("/", response_model=CodingRoomListResponse)
async def list_rooms(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CodingRoomListResponse:
    items, total = await CodingRoomService(db).crud.list_accessible(user.id, skip, limit)
    return CodingRoomListResponse(
        items=[CodingRoomResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{room_id}", response_model=CodingRoomResponse)
async def get_room(
    room_id: UUID,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> CodingRoomResponse:
    return CodingRoomResponse.model_validate(
        await CodingRoomService(db).get_accessible(room_id, user)
    )


@router.patch("/{room_id}", response_model=CodingRoomResponse)
async def update_room(
    room_id: UUID,
    payload: CodingRoomUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CodingRoomResponse:
    return CodingRoomResponse.model_validate(
        await CodingRoomService(db).update(room_id, user, payload)
    )


@router.post("/{room_id}/join", response_model=RoomMemberResponse)
async def join_room(
    room_id: UUID, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
) -> RoomMemberResponse:
    return RoomMemberResponse.model_validate(await CodingRoomService(db).join(room_id, user))


@router.post(
    "/{room_id}/members", response_model=RoomMemberResponse, status_code=status.HTTP_201_CREATED
)
async def add_member(
    room_id: UUID,
    payload: RoomMemberCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RoomMemberResponse:
    return RoomMemberResponse.model_validate(
        await CodingRoomService(db).add_member(room_id, user, payload)
    )


@router.delete("/{room_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
async def leave_room(
    room_id: UUID, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
) -> None:
    await CodingRoomService(db).leave(room_id, user)


@router.websocket("/{room_id}/ws")
async def room_websocket(websocket: WebSocket, room_id: UUID) -> None:
    """Authenticated collaboration protocol: document_update, cursor_update, and ping."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return
    try:
        subject = decode_token(token).get("sub")
        if not isinstance(subject, str):
            raise ValueError("Missing token subject")
        async with AsyncSessionLocal() as db:
            user = await AuthService(db).get_user_by_id(subject)
            service = CodingRoomService(db)
            membership = await service.require_member(room_id, user)
            await service.crud.touch_member(membership)
            room = await service.get_accessible(room_id, user)
            await room_connections.connect(str(room_id), websocket)
            await websocket.send_json(
                {
                    "type": "room_state",
                    "document": room.document,
                    "version": room.version,
                    "role": membership.role.value,
                }
            )
            await room_connections.publish(
                str(room_id),
                {"type": "presence", "user_id": str(user.id), "state": "joined"},
                websocket,
            )
            while True:
                message = await websocket.receive_json()
                kind = message.get("type")
                if kind == "document_update":
                    document, version = message.get("document"), message.get("version")
                    if not isinstance(document, dict) or not isinstance(version, int):
                        await websocket.send_json(
                            {"type": "error", "detail": "Invalid document update."}
                        )
                        continue
                    updated = await service.update_document(room_id, user, document, version)
                    await room_connections.publish(
                        str(room_id),
                        {
                            "type": "document_update",
                            "document": updated.document,
                            "version": updated.version,
                            "user_id": str(user.id),
                        },
                        websocket,
                    )
                elif kind == "cursor_update":
                    cursor = message.get("cursor")
                    if not isinstance(cursor, dict):
                        await websocket.send_json(
                            {"type": "error", "detail": "Invalid cursor update."}
                        )
                        continue
                    await room_connections.publish(
                        str(room_id),
                        {"type": "cursor_update", "cursor": cursor, "user_id": str(user.id)},
                        websocket,
                    )
                elif kind == "ping":
                    await websocket.send_json({"type": "pong"})
                else:
                    await websocket.send_json(
                        {"type": "error", "detail": "Unsupported room event."}
                    )
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close(code=4403)
    finally:
        await room_connections.disconnect(str(room_id), websocket)
