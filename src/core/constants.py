"""
System constants, enums, and configuration values.
"""

from enum import Enum


class TesereDurumu(Enum):
    """Saw machine states."""
    IDLE = 0
    PREPARING = 1
    READY = 2
    CUTTING = 3
    COMPLETED = 4
    ERROR = 5


class ControlMode(Enum):
    """Control operation modes."""
    MANUAL = "manual"
    ML = "ml"


# ML Control Constants
BUFFER_SIZE = 10  # Standard buffer size for ML input averaging
TORQUE_BUFFER_SIZE = 50  # Larger buffer for torque averaging
KATSAYI = 1.0  # Global ML coefficient multiplier

# Torque Guard Parameters
ENABLE_TORQUE_GUARD = True
TORQUE_GUARD_ACTIVATION_DELAY_S = 5.0  # Wait 5s after ML activation
TORQUE_HEIGHT_LOOKBACK_MM = 3.0  # Look back 3mm in height
TORQUE_INITIAL_THRESHOLD_MM = 3.0  # Skip first 3mm of descent
TORQUE_INCREASE_THRESHOLD = 50.0  # Trigger if >50% torque increase (%)
DESCENT_REDUCTION_PERCENT = 25.0  # Reduce speed by 25%

# Torque → Current Polynomial Coefficients
# Formula: f(x) = A2*x^2 + A1*x + A0
TORQUE_TO_CURRENT_A2 = 0.0001
TORQUE_TO_CURRENT_A1 = 0.285
TORQUE_TO_CURRENT_A0 = 8.5

# Speed Change Write Thresholds
INME_HIZI_WRITE_THRESHOLD = 1.0  # mm/min
KESME_HIZI_WRITE_THRESHOLD = 0.9  # mm/min

# Speed Limits (default, overridden by config)
SPEED_LIMITS = {
    'kesme': {'min': 40.0, 'max': 90.0},
    'inme': {'min': 10.0, 'max': 80.0}
}

# Update Intervals
MIN_SPEED_UPDATE_INTERVAL = 0.2  # 5 Hz (200ms)

# Database
DATA_PROCESSING_WARNING_THRESHOLD = 45  # Warn if <45 writes/second
