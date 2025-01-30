# src/api/routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from datetime import datetime

from core import logger
from control import ControllerType, get_controller_factory
from models.api_models import (
    SystemStatus,
    ControllerStats,
    SpeedData,
    ProcessedDataResponse,
    ControllerConfig
)

router = APIRouter(prefix="/api/v1")
controller_factory = get_controller_factory()

@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Sistem durumunu döndürür"""
    try:
        return {
            "status": "running",
            "active_controller": controller_factory.active_controller.value,
            "last_update": datetime.now().isoformat(),
            "error_count": 0  # TODO: Implement error counting
        }
    except Exception as e:
        logger.error(f"Status API hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/controllers", response_model=List[str])
async def get_available_controllers():
    """Kullanılabilir kontrol sistemlerini listeler"""
    return [ct.value for ct in ControllerType]

@router.get("/controller/stats", response_model=Dict[str, ControllerStats])
async def get_controller_stats():
    """Kontrol sistemi istatistiklerini döndürür"""
    return controller_factory.get_stats()

@router.post("/controller/{controller_type}")
async def set_controller(controller_type: str):
    """Aktif kontrol sistemini değiştirir"""
    try:
        controller_factory.set_controller(ControllerType[controller_type.upper()])
        return {"message": f"Kontrol sistemi değiştirildi: {controller_type}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/data/current", response_model=ProcessedDataResponse)
async def get_current_data():
    """Anlık işlenmiş veriyi döndürür"""
    # TODO: Implement data access
    pass

@router.get("/data/history", response_model=List[ProcessedDataResponse])
async def get_data_history(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
):
    """Geçmiş veriyi döndürür"""
    # TODO: Implement historical data access
    pass

def create_api_router() -> APIRouter:
    return router