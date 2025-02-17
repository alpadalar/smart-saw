# src/api/websocket.py
from fastapi import WebSocket
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime
from .api_models import WebSocketMessage

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.last_data: Dict[str, Any] = {}
    
    async def connect(self, websocket: WebSocket):
        """Yeni WebSocket bağlantısı kabul eder"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Bağlantı sonrası son durumu gönder
        if self.last_data:
            await websocket.send_json(WebSocketMessage(
                type="initial_state",
                data=self.last_data
            ).dict())
    
    def disconnect(self, websocket: WebSocket):
        """WebSocket bağlantısını kapatır"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Tüm bağlı istemcilere mesaj gönderir"""
        if not isinstance(message, dict):
            message = {"type": "data", "data": message}
        
        self.last_data = message
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Kopan bağlantıları temizle
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_updates(self):
        """Periyodik güncellemeleri gönderir"""
        while True:
            if self.active_connections and self.last_data:
                await self.broadcast(WebSocketMessage(
                    type="update",
                    data=self.last_data
                ).dict())
            await asyncio.sleep(0.1)  # 100ms güncelleme aralığı