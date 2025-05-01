# src/api/api_models.py
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any
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

class DetailedMachineData(BaseModel):
    """Detaylı makine veri modeli"""
    timestamp: datetime
    serit_motor_akim_a: float
    serit_motor_tork_percentage: Optional[float]
    inme_motor_akim_a: Optional[float]
    inme_motor_tork_percentage: Optional[float]
    serit_sapmasi: float
    kafa_yuksekligi_mm: float
    testere_durumu: int
    serit_kesme_hizi: float
    serit_inme_hizi: float
    controller_output: Optional[float]
    fuzzy_output: Optional[float]
    kesme_hizi_degisim: Optional[float]
    ivme_olcer_x: Optional[float]
    ivme_olcer_y: Optional[float]
    ivme_olcer_z: Optional[float]
    ivme_olcer_x_hz: Optional[float]
    ivme_olcer_y_hz: Optional[float]
    ivme_olcer_z_hz: Optional[float]
    ortam_sicakligi_c: Optional[float]
    ortam_nem_percentage: Optional[float]
    sogutma_sivi_sicakligi_c: Optional[float]
    hidrolik_yag_sicakligi_c: Optional[float]
    mengene_basinc_bar: Optional[float]
    serit_gerginligi_bar: Optional[float]
    modbus_connected: Optional[bool]
    active_controller: Optional[str]

class RealtimeData(BaseModel):
    """Gerçek zamanlı veri modeli"""
    timestamp: datetime
    testere_durumu: int
    serit_motor_akim_a: float
    serit_sapmasi: float
    kafa_yuksekligi_mm: float
    serit_kesme_hizi: float
    serit_inme_hizi: float
    controller_output: Optional[float]
    is_cutting: bool

class CuttingInfo(BaseModel):
    """Kesim bilgisi modeli"""
    cutting_active: bool
    last_cutting_start: Optional[datetime]
    last_cutting_end: Optional[datetime]
    last_cutting_duration_ms: Optional[int]
    last_cutting_duration_formatted: Optional[str]
    cutting_count: int
    active_controller: Optional[str]

class LogEntry(BaseModel):
    """Log satırı modeli"""
    timestamp: datetime
    level: str
    message: str
    source: Optional[str] = None
    line_number: Optional[int] = None

class LogFilter(BaseModel):
    """Log filtreleme modeli"""
    level: Optional[str] = None
    search_term: Optional[str] = None
    source_file: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)

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