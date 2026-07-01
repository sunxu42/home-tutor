"""WebSocket handlers."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from home_tutor.core.logging import get_logger, log_trace

logger = get_logger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manage active WebSocket connections."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.remove(websocket)

    async def broadcast(self, message: dict[str, object]) -> None:
        for connection in self._connections:
            await connection.send_text(json.dumps(message))


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time messaging."""
    await manager.connect(websocket)
    log_trace(logger, "WS_CONNECT", path="/ws")
    try:
        while True:
            data = await websocket.receive_text()
            log_trace(logger, "WS_MESSAGE", payload=data)
            await manager.broadcast({"type": "echo", "payload": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
