"""
Domain enumerations.
"""

from enum import Enum


class TesereDurumu(Enum):
    """
    Saw machine operational states.

    Values match Modbus register values from PLC.
    """
    BOSTA = 0              # BOŞTA - Machine is idle
    HIDROLIK_AKTIF = 1     # HİDROLİK AKTİF - Hydraulic active
    SERIT_MOTOR = 2        # ŞERİT MOTOR ÇALIŞIYOR - Band motor running
    KESIYOR = 3            # KESİM YAPILIYOR - Actively cutting
    KESIM_BITTI = 4        # KESİM BİTTİ - Cutting completed
    SERIT_YUKARI = 5       # ŞERİT YUKARI ÇIKIYOR - Saw moving up
    MALZEME_BESLEME = 6    # MALZEME BESLEME - Material feeding


class ControlMode(Enum):
    """Control operation modes."""
    MANUAL = "manual"  # Manual speed control (GUI-driven)
    ML = "ml"          # ML-based automatic control
