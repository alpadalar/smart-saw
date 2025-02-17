# src/api/api_models.py
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime
from core.constants import SPEED_LIMITS, ControllerType

class SpeedUpdate(BaseModel):
    """Hız güncelleme modeli"""
    cutting_speed: float = Field(
        ..., 
        ge=SPEED_LIMITS['kesme']['min'],
        le=SPEED_LIMITS['kesme']['max'],
        description="Kesme hızı (mm/s)"
    )
    feed_speed: float = Field(
        ...,
        ge=SPEED_LIMITS['inme']['min'],
        le=SPEED_LIMITS['inme']['max'],
        description="İnme hızı (mm/s)"
    )

class ControllerUpdate(BaseModel):
    """Kontrol modu güncelleme modeli"""
    mode: str = Field(
        ...,
        description=f"Kontrol modu: {[mode.value for mode in ControllerType]}"
    )

class SystemStatus(BaseModel):
    """Sistem durumu modeli"""
    status: str
    active_controller: Optional[str]
    modbus_connected: bool
    last_update: datetime
    error_count: int
    speeds: Dict[str, float]
    sensor_data: Dict[str, float]

class MachineData(BaseModel):
    """Makine verisi modeli"""
    timestamp: datetime
    serit_motor_akim_a: float
    serit_sapmasi: float
    kafa_yuksekligi_mm: float
    testere_durumu: int
    serit_kesme_hizi: float
    serit_inme_hizi: float
    controller_output: Optional[float]
    ivme_olcer_x_hz: Optional[float]
    ivme_olcer_y_hz: Optional[float]
    ivme_olcer_z_hz: Optional[float]

class WebSocketMessage(BaseModel):
    """WebSocket mesaj modeli"""
    type: str
    data: Dict
    timestamp: datetime = Field(default_factory=datetime.now)

class APIResponse(BaseModel):
    """API yanıt modeli"""
    status: str
    message: str
    data: Optional[Dict] = None