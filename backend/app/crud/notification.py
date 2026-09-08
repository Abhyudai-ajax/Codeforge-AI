"""CRUD operations for Notification system."""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


class CRUDNotification:
    """CRUD operations for User Notifications."""

    async def create(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        type: NotificationType,
        title: str,
        message: str,
        data: dict | None = None,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            data=data or {},
        )
        db.add(notif)
        await db.commit()
        await db.refresh(notif)
        return notif

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return res.scalars().all()

    async def count_unread(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        res = await db.execute(stmt)
        return res.scalar() or 0

    async def get_by_id(
        self, db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def mark_as_read(
        self, db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notification | None:
        notif = await self.get_by_id(db, notification_id, user_id)
        if notif:
            notif.is_read = True
            notif.read_at = func.now()
            await db.commit()
            await db.refresh(notif)
        return notif

    async def mark_all_as_read(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=func.now())
        )
        res = await db.execute(stmt)
        await db.commit()
        rowcount = getattr(res, "rowcount", 0)
        return int(rowcount) if rowcount is not None else 0

    async def delete(
        self, db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        notif = await self.get_by_id(db, notification_id, user_id)
        if notif:
            await db.delete(notif)
            await db.commit()
            return True
        return False


notification_crud = CRUDNotification()
