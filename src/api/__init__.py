# src/api/__init__.py
from fastapi import FastAPI
from .routes import router
from .websocket import WebSocketManager
from .log_reader import get_log_reader, LogReader
from core.logger import logger

def create_app() -> FastAPI:
    """FastAPI uygulamasını oluşturur ve yapılandırır"""
    app = FastAPI(
        title="Smart Saw API",
        description="Akıllı Testere Kontrol Sistemi API",
        version="1.0.0",
        root_path=""  # Ana sunucu ile birlikte çalıştığında boş olmalı
    )
    
    # API router'ını ekle
    app.include_router(router)
    
    # WebSocket yöneticisini başlat
    ws_manager = WebSocketManager()
    
    @app.on_event("startup")
    async def startup_event():
        """Uygulama başlangıcında çalışacak kodlar"""
        logger.info("API servisi başlatıldı")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Uygulama kapanışında çalışacak kodlar"""
        logger.info("API servisi kapatıldı")
    
    return app

__all__ = [
    'router',
    'WebSocketManager',
    'LogReader',
    'get_log_reader'
]