"""Service layer for Notification management."""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.notification import notification_crud
from app.models.notification import Notification, NotificationType

logger = logging.getLogger(__name__)


class NotificationService:
    """Business logic for notifications across CodeForge AI."""

    async def list_notifications(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Notification]:
        return await notification_crud.list_for_user(
            db, user_id=user_id, unread_only=unread_only, limit=limit, offset=offset
        )

    async def get_unread_count(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        return await notification_crud.count_unread(db, user_id)

    async def mark_as_read(
        self, db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notification | None:
        return await notification_crud.mark_as_read(db, notification_id, user_id)

    async def mark_all_as_read(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        return await notification_crud.mark_all_as_read(db, user_id)

    async def delete_notification(
        self, db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        return await notification_crud.delete(db, notification_id, user_id)

    async def notify_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        type: NotificationType,
        title: str,
        message: str,
        data: dict | None = None,
    ) -> Notification:
        logger.info(f"Emitting notification '{title}' to user {user_id}")
        return await notification_crud.create(
            db,
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            data=data or {},
        )


notification_service = NotificationService()
