"""WebSocket support for real-time audio streaming and matching."""

import logging
import time

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time audio streaming."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.user_streams: dict[str, list] = {}
        self.connection_times: dict[str, float] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.user_streams[client_id] = []
        self.connection_times[client_id] = time.time()
        logger.info(f"Client {client_id} connected via WebSocket")

    def disconnect(self, client_id: str):
        """Remove a client connection."""
        self.active_connections.pop(client_id, None)
        self.user_streams.pop(client_id, None)
        self.connection_times.pop(client_id, None)
        logger.info(f"Client {client_id} disconnected")

    async def send_match(self, client_id: str, match_data: dict):
        """Send match results to a connected client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json({
                    "type": "match",
                    "data": match_data
                })
                logger.debug(f"Sent match to client {client_id}")
            except Exception as e:
                logger.error(f"Error sending match to {client_id}: {e}")
                self.disconnect(client_id)

    async def send_status(self, client_id: str, status: str):
        """Send status update to a connected client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json({
                    "type": "status",
                    "message": status
                })
                logger.debug(f"Sent status to client {client_id}: {status}")
            except Exception as e:
                logger.error(f"Error sending status to {client_id}: {e}")
                self.disconnect(client_id)

    async def send_error(self, client_id: str, error_message: str):
        """Send error message to a connected client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json({
                    "type": "error",
                    "message": error_message
                })
                logger.debug(f"Sent error to client {client_id}: {error_message}")
            except Exception as e:
                logger.error(f"Error sending error to {client_id}: {e}")
                self.disconnect(client_id)

    def get_active_connections(self) -> list[dict]:
        """Get list of active connections with metadata."""
        return [
            {
                "client_id": client_id,
                "connected_at": self.connection_times.get(client_id, 0),
                "duration_seconds": time.time() - self.connection_times.get(client_id, time.time())
            }
            for client_id in self.active_connections.keys()
        ]


# Global connection manager instance
manager = ConnectionManager()
