# src/models/data_models.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from core.data_processor import ProcessedData

@dataclass
class ModbusRegisters:
    """Modbus register adresleri"""
    REGISTERS: Dict[str, int] = field(default_factory=lambda: {
        # Giriş registerleri
        'SERIT_MOTOR_AKIM': 0,
        'SERIT_SAPMA': 1,
        'KAFA_YUKSEKLIK': 2,
        'TESTERE_DURUM': 3,
        
        # Çıkış registerleri
        'KESME_HIZ': 100,
        'INME_HIZ': 101
    })

@dataclass
class RawData:
    """Ham modbus verisi"""
    timestamp: datetime
    registers: Dict[int, float] = field(default_factory=dict)

@dataclass
class SpeedData:
    """Hız verisi"""
    kesme_hizi: float = 0.0
    inme_hizi: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SystemState:
    """Sistem durumu"""
    IDLE: int = 0
    PREPARING: int = 1
    READY: int = 2
    CUTTING: int = 3
    COMPLETED: int = 4
    ERROR: int = 5

    @staticmethod
    def get_state_name(state: int) -> str:
        state_names = {
            0: "Bekleniyor",
            1: "Hazırlanıyor",
            2: "Hazır",
            3: "Kesim Yapılıyor",
            4: "Tamamlandı",
            5: "Hata"
        }
        return state_names.get(state, "Bilinmiyor")

@dataclass
class ControllerOutput:
    """Kontrol sistemi çıktısı"""
    timestamp: datetime
    output_value: float
    controller_type: str
    input_values: Dict[str, float] = field(default_factory=dict)
    parameters: Dict[str, float] = field(default_factory=dict)

@dataclass
class DataPoint:
    """Veri noktası"""
    timestamp: datetime
    value: float
    tag: str
    metadata: Dict[str, any] = field(default_factory=dict)

@dataclass
class TimeWindow:
    """Zaman penceresi"""
    start_time: datetime
    end_time: datetime
    duration_ms: float = field(init=False)

    def __post_init__(self):
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

@dataclass
class DataBuffer:
    """Veri tamponu"""
    max_size: int
    data: List[DataPoint] = field(default_factory=list)
    window_size_ms: float = 1000.0

    def add_point(self, point: DataPoint):
        self.data.append(point)
        if len(self.data) > self.max_size:
            self.data.pop(0)

    def get_window(self, window_size_ms: Optional[float] = None) -> List[DataPoint]:
        if not window_size_ms:
            window_size_ms = self.window_size_ms
        
        current_time = datetime.now()
        window_start = current_time.timestamp() - (window_size_ms / 1000)
        
        return [
            point for point in self.data 
            if point.timestamp.timestamp() >= window_start
        ]

@dataclass
class ControllerConfig:
    """Kontrol sistemi konfigürasyonu"""
    type: str
    parameters: Dict[str, float] = field(default_factory=dict)
    enabled: bool = False
    last_update: datetime = field(default_factory=datetime.now)