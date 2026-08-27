"""ConnectionManager — WebSocket connection tracking and broadcasting."""

from typing import Any, Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self._connections:
            self._connections[session_id] = []
        self._connections[session_id].append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self._connections:
            self._connections[session_id] = [ws for ws in self._connections[session_id] if ws is not websocket]

    async def broadcast(self, session_id: str, message: Dict[str, Any]):
        for ws in self._connections.get(session_id, []):
            await ws.send_json(message)
