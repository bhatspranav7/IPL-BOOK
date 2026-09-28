import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        # Remember the server loop so sync endpoints (threadpool) can publish
        self.loop = asyncio.get_running_loop()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

    def publish(self, message: dict):
        """Fire-and-forget broadcast that is safe to call from sync code."""
        if self.loop is None or not self.active_connections:
            return
        try:
            asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)
        except Exception as e:
            logger.warning("WebSocket broadcast failed: %s", e)


# 🔥 GLOBAL INSTANCE
manager = ConnectionManager()
