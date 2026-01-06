"""
Domain data models using dataclasses.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any

from .enums import TesereDurumu, ControlMode


@dataclass
class RawSensorData:
    """
    Raw sensor data from Modbus registers.

    All values are in engineering units (scaled from raw register values).
    """
    timestamp: datetime

    # Motor measurements
    serit_motor_akim_a: float = 0.0              # Band motor current (A)
    serit_motor_tork_percentage: float = 0.0     # Band motor torque (%)
    inme_motor_akim_a: float = 0.0               # Descent motor current (A)
    inme_motor_tork_percentage: float = 0.0      # Descent motor torque (%)

    # Speed values (actual - from registers 1033/1034)
    serit_kesme_hizi: float = 0.0                # Cutting speed (mm/min)
    serit_inme_hizi: float = 0.0                 # Descent speed (mm/min)

    # Target speed values (from registers 2066/2041 - what we write to PLC)
    kesme_hizi_hedef: float = 0.0                # Target cutting speed (mm/min)
    inme_hizi_hedef: float = 0.0                 # Target descent speed (mm/min)

    # Mechanical measurements
    kafa_yuksekligi_mm: float = 0.0              # Head height (mm)
    serit_sapmasi: float = 0.0                   # Band deviation (mm, signed)
    serit_gerginligi_bar: float = 0.0            # Band tension (bar)
    mengene_basinc_bar: float = 0.0              # Vice pressure (bar)

    # Environmental measurements
    ortam_sicakligi_c: float = 0.0               # Ambient temperature (°C)
    ortam_nem_percentage: float = 0.0            # Ambient humidity (%)
    sogutma_sivi_sicakligi_c: float = 0.0        # Coolant temperature (°C)
    hidrolik_yag_sicakligi_c: float = 0.0        # Hydraulic oil temperature (°C)

    # Vibration measurements
    ivme_olcer_x: float = 0.0                    # X-axis acceleration (g)
    ivme_olcer_y: float = 0.0                    # Y-axis acceleration (g)
    ivme_olcer_z: float = 0.0                    # Z-axis acceleration (g)
    ivme_olcer_x_hz: float = 0.0                 # X-axis frequency (Hz)
    ivme_olcer_y_hz: float = 0.0                 # Y-axis frequency (Hz)
    ivme_olcer_z_hz: float = 0.0                 # Z-axis frequency (Hz)
    max_titresim_hz: float = 0.0                 # Maximum vibration frequency (Hz)

    # State information
    testere_durumu: int = 0                      # Saw state (see TesereDurumu enum)
    alarm_status: int = 0                        # Alarm status code
    alarm_bilgisi: str = "0x0000"                # Alarm information (hex string)

    # Machine & band identification
    makine_id: int = 1                           # Machine ID
    serit_id: int = 1                            # Band ID

    # Material information
    malzeme_cinsi: str = ""                      # Material type
    malzeme_sertlik: str = ""                    # Material hardness
    kesit_yapisi: str = ""                       # Cross-section structure
    malzeme_a_mm: float = 0.0                    # Material dimension A (mm)
    malzeme_b_mm: float = 0.0                    # Material dimension B (mm)
    malzeme_c_mm: float = 0.0                    # Material dimension C (mm)
    malzeme_d_mm: float = 0.0                    # Material dimension D (mm)
    malzeme_genisligi: float = 0.0               # Material width (mm)

    # Band information
    serit_tip: str = ""                          # Band type
    serit_marka: str = ""                        # Band brand
    serit_malz: str = ""                         # Band material
    serit_dis_mm: int = 0                        # Band tooth pitch (mm)

    # Statistics
    kesilen_parca_adeti: int = 0                 # Cut piece count

    # Power measurement
    guc_kwh: float = 0.0                         # Power consumption (kWh)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ProcessedData:
    """
    Processed data with ML outputs and anomaly detection results.
    """
    timestamp: datetime
    raw_data: RawSensorData

    # ML control outputs
    ml_output: Optional[float] = None            # ML model coefficient output
    kesme_hizi_degisim: Optional[float] = None   # Cutting speed change (mm/min)
    inme_hizi_degisim: Optional[float] = None    # Descent speed change (mm/min)
    torque_guard_active: bool = False            # Torque Guard triggered flag

    # Anomaly detection
    anomalies: Dict[str, Any] = field(default_factory=dict)

    # Cutting session tracking
    is_cutting: bool = False
    cutting_session_id: Optional[int] = None  # Integer kesim_id
    controller_type: str = "manual"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'raw_data': self.raw_data.to_dict(),
            'ml_output': self.ml_output,
            'kesme_hizi_degisim': self.kesme_hizi_degisim,
            'inme_hizi_degisim': self.inme_hizi_degisim,
            'torque_guard_active': self.torque_guard_active,
            'anomalies': self.anomalies,
            'is_cutting': self.is_cutting,
            'cutting_session_id': self.cutting_session_id,
            'controller_type': self.controller_type
        }


@dataclass
class ControlCommand:
    """
    Control command to be sent to machine (Modbus write).
    """
    timestamp: datetime
    kesme_hizi_target: float                     # Target cutting speed (mm/min)
    inme_hizi_target: float                      # Target descent speed (mm/min)
    source: str                                  # "manual", "ml", or "torque_guard"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'kesme_hizi_target': self.kesme_hizi_target,
            'inme_hizi_target': self.inme_hizi_target,
            'source': self.source
        }


@dataclass
class CuttingSession:
    """
    Cutting session metadata.
    """
    session_id: str                              # Unique session ID (UUID)
    start_time: datetime                         # Session start timestamp
    end_time: Optional[datetime] = None          # Session end timestamp
    controller_type: str = "manual"              # "manual" or "ml"
    data_count: int = 0                          # Number of data points recorded
    duration_ms: Optional[int] = None            # Session duration (milliseconds)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'controller_type': self.controller_type,
            'data_count': self.data_count,
            'duration_ms': self.duration_ms
        }
