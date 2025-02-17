# src/api/routes.py
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
from datetime import datetime

from core.logger import logger
from core.constants import ControllerType, SPEED_LIMITS, TestereState
from control.factory import get_controller_factory
from utils.helpers import validate_speed_limits, reverse_calculate_value
from hardware.modbus.client import ModbusClient
from .api_models import (
    SystemStatus,
    SpeedUpdate,
    ControllerUpdate,
    MachineData,
    APIResponse,
    WebSocketMessage
)
from .websocket import WebSocketManager

router = APIRouter(prefix="/api/v1")
controller_factory = get_controller_factory()
ws_manager = WebSocketManager()

@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Sistem durumunu döndürür"""
    try:
        modbus = ModbusClient()
        current_data = modbus.read_all() if modbus.is_connected else None
        active_controller = controller_factory.active_controller

        return SystemStatus(
            status="running",
            active_controller=active_controller.value if active_controller else None,
            modbus_connected=modbus.is_connected,
            last_update=datetime.now(),
            error_count=sum(stats["errors"] for stats in controller_factory.get_stats().values()),
            speeds={
                "cutting": current_data.get("serit_kesme_hizi", 0) if current_data else 0,
                "feed": current_data.get("serit_inme_hizi", 0) if current_data else 0
            },
            sensor_data={
                "current": current_data.get("serit_motor_akim_a", 0) if current_data else 0,
                "deviation": current_data.get("serit_sapmasi", 0) if current_data else 0,
                "height": current_data.get("kafa_yuksekligi_mm", 0) if current_data else 0
            }
        )
    except Exception as e:
        logger.error(f"Status API hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/control/mode", response_model=APIResponse)
async def update_control_mode(update: ControllerUpdate):
    """Kontrol modunu değiştirir"""
    try:
        controller_type = ControllerType[update.mode.upper()]
        controller_factory.set_controller(controller_type)
        
        # WebSocket üzerinden bildirim gönder
        await ws_manager.broadcast(WebSocketMessage(
            type="controller_change",
            data={"mode": controller_type.value}
        ).dict())
        
        return APIResponse(
            status="success",
            message=f"Kontrol modu {controller_type.value} olarak değiştirildi",
            data={"mode": controller_type.value}
        )
    except Exception as e:
        logger.error(f"Kontrol modu değiştirme hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/control/speed", response_model=APIResponse)
async def update_speeds(update: SpeedUpdate):
    """Kesme ve inme hızlarını günceller"""
    try:
        modbus = ModbusClient()
        if not modbus.is_connected:
            raise HTTPException(status_code=503, detail="Modbus bağlantısı yok")

        # Hızları güncelle
        kesme_hizi = validate_speed_limits(update.cutting_speed, 'kesme')
        inme_hizi = validate_speed_limits(update.feed_speed, 'inme')
        
        reverse_calculate_value(modbus, kesme_hizi, 'serit_kesme_hizi', False)
        reverse_calculate_value(modbus, inme_hizi, 'serit_inme_hizi', False)
        
        # WebSocket üzerinden bildirim gönder
        await ws_manager.broadcast(WebSocketMessage(
            type="speed_update",
            data={
                "cutting_speed": kesme_hizi,
                "feed_speed": inme_hizi
            }
        ).dict())
        
        return APIResponse(
            status="success",
            message="Hızlar güncellendi",
            data={
                "cutting_speed": kesme_hizi,
                "feed_speed": inme_hizi
            }
        )
    except Exception as e:
        logger.error(f"Hız güncelleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/control/stop", response_model=APIResponse)
async def emergency_stop():
    """Acil duruş yapar"""
    try:
        modbus = ModbusClient()
        if not modbus.is_connected:
            raise HTTPException(status_code=503, detail="Modbus bağlantısı yok")

        # Hızları sıfırla
        reverse_calculate_value(modbus, 0, 'serit_kesme_hizi', False)
        reverse_calculate_value(modbus, 0, 'serit_inme_hizi', False)
        
        # Kontrol sistemini devre dışı bırak
        controller_factory.set_controller(None)
        
        # WebSocket üzerinden bildirim gönder
        await ws_manager.broadcast(WebSocketMessage(
            type="emergency_stop",
            data={"timestamp": datetime.now().isoformat()}
        ).dict())
        
        return APIResponse(
            status="success",
            message="Acil duruş yapıldı",
            data=None
        )
    except Exception as e:
        logger.error(f"Acil duruş hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket bağlantı noktası"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # İstemciden gelen mesajları işle
            await ws_manager.broadcast(data)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)