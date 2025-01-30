# src/models/api_models.py
from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime

class SystemStatus(BaseModel):
    status: str
    active_controller: str
    last_update: datetime
    error_count: int

class ControllerStats(BaseModel):
    total_runs: int
    total_time: float
    average_time: float
    last_run: Optional[float]
    errors: int

class SpeedData(BaseModel):
    kesme_hizi: float
    inme_hizi: float
    timestamp: datetime

class ProcessedDataResponse(BaseModel):
    timestamp: datetime
    serit_motor_akim_a: float
    serit_sapmasi: float
    kafa_yuksekligi_mm: float
    testere_durumu: int
    speeds: SpeedData
    controller_output: Optional[float]

class ControllerConfig(BaseModel):
    type: str
    parameters: Dict[str, float]