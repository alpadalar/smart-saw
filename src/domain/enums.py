"""
Domain enumerations.
"""

from enum import Enum


class TesereDurumu(Enum):
    """
    Saw machine operational states.

    Values match Modbus register values.
    """
    IDLE = 0          # Machine is idle
    PREPARING = 1     # Preparing for cutting
    READY = 2         # Ready to cut
    CUTTING = 3       # Actively cutting
    COMPLETED = 4     # Cutting completed
    ERROR = 5         # Error state


class ControlMode(Enum):
    """Control operation modes."""
    MANUAL = "manual"  # Manual speed control (GUI-driven)
    ML = "ml"          # ML-based automatic control
