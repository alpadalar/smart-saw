# src/api/websocket.py
from fastapi import WebSocket
from typing import List, Dict, Any
import json
import asyncio

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.last_data: Dict[str, Any] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, data: Dict[str, Any]):
        """Tüm bağlı clientlara veri gönderir"""
        self.last_data = data
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except:
                await self.disconnect(connection)
    
    async def send_updates(self):
        """Periyodik olarak güncellemeleri gönderir"""
        while True:
            if self.active_connections:
                await self.broadcast(self.last_data)
            await asyncio.sleep(0.1)  # 100ms güncelleme aralığı