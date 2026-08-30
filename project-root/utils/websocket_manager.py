from typing import Dict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        connections = self.active_connections.get(user_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections and user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_to_user(self, user_id: int, event: str, data: dict) -> None:
        for connection in self.active_connections.get(user_id, []):
            await connection.send_json({"event": event, "data": data})


manager = ConnectionManager()
