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
# Buffer sizes match old working project: 3 samples for averaging
BUFFER_SIZE = 3  # Standard buffer size for ML input averaging (matches old project)
TORQUE_BUFFER_SIZE = 3  # Torque buffer (matches old project)
KATSAYI = 1.0  # Global ML coefficient multiplier

# Torque Guard Parameters (matches old project values)
ENABLE_TORQUE_GUARD = True
TORQUE_GUARD_ACTIVATION_DELAY_S = 5.0  # Wait 5s after ML activation
TORQUE_HEIGHT_LOOKBACK_MM = 2.5  # Look back 2.5mm in height (matches old project)
TORQUE_INITIAL_THRESHOLD_MM = 2.5  # Skip first 2.5mm of descent (matches old project)
TORQUE_INCREASE_THRESHOLD = 40.0  # Trigger if >40% torque increase (matches old project)
DESCENT_REDUCTION_PERCENT = 25.0  # Reduce speed by 25%

# Torque → Current Polynomial Coefficients
# Formula: f(x) = A2*x^2 + A1*x + A0
# Calibrated from motor datasheet: matches old working project values
TORQUE_TO_CURRENT_A2 = 0.015
TORQUE_TO_CURRENT_A1 = -0.278
TORQUE_TO_CURRENT_A0 = 15.656

# Speed Change Write Thresholds
INME_HIZI_WRITE_THRESHOLD = 1.0  # mm/min
KESME_HIZI_WRITE_THRESHOLD = 0.9  # mm/min

# Speed Limits (default, overridden by config)
# Matches old project values
SPEED_LIMITS = {
    'kesme': {'min': 40.0, 'max': 90.0},
    'inme': {'min': 10.0, 'max': 60.0}
}

# Update Intervals
MIN_SPEED_UPDATE_INTERVAL = 0.2  # 5 Hz (200ms)

# Database
DATA_PROCESSING_WARNING_THRESHOLD = 45  # Warn if <45 writes/second
