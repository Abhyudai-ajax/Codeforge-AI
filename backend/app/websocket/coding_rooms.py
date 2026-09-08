"""Redis-backed WebSocket fan-out for coding room collaboration."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from redis import asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RoomConnectionManager:
    """Fan out collaboration events locally and through Redis pub/sub across API replicas."""

    def __init__(self) -> None:
        self.instance_id = str(uuid.uuid4())
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._redis: redis.Redis | None = None
        self._listeners: dict[str, asyncio.Task[None]] = {}

    async def _client(self) -> redis.Redis | None:
        if self._redis is None:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        try:
            await self._redis.ping()
        except Exception:
            logger.warning("Redis unavailable; room events are limited to this API instance.")
            return None
        return self._redis

    async def connect(self, room_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[room_id].add(websocket)
        if room_id not in self._listeners:
            self._listeners[room_id] = asyncio.create_task(self._listen(room_id))

    async def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        self.connections[room_id].discard(websocket)
        if not self.connections[room_id]:
            self.connections.pop(room_id, None)
            task = self._listeners.pop(room_id, None)
            if task:
                task.cancel()

    async def publish(
        self, room_id: str, payload: dict[str, Any], sender: WebSocket | None = None
    ) -> None:
        envelope = {"source": self.instance_id, "payload": payload}
        await self._broadcast(room_id, payload, exclude=sender)
        client = await self._client()
        if client:
            await client.publish(f"codeforge:room:{room_id}", json.dumps(envelope))

    async def _broadcast(
        self, room_id: str, payload: dict[str, Any], exclude: WebSocket | None = None
    ) -> None:
        for socket in tuple(self.connections.get(room_id, set())):
            if socket is exclude:
                continue
            try:
                await socket.send_json(payload)
            except Exception:
                await self.disconnect(room_id, socket)

    async def _listen(self, room_id: str) -> None:
        client = await self._client()
        if client is None:
            return
        pubsub = client.pubsub()
        try:
            await pubsub.subscribe(f"codeforge:room:{room_id}")
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                envelope = json.loads(message["data"])
                if envelope.get("source") != self.instance_id:
                    await self._broadcast(room_id, envelope["payload"])
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Redis room listener failed for room %s", room_id)
        finally:
            await pubsub.aclose()


room_connections = RoomConnectionManager()
