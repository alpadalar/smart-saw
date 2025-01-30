from enum import Enum

# Modbus Register Adresleri
KESME_HIZI_REGISTER_ADDRESS = 2066
INME_HIZI_REGISTER_ADDRESS = 2041

# Hız Limitleri
MIN_SPEED = 5.0
MAX_SPEED = 100.0

SPEED_LIMITS = {
    'kesme': {
        'min': 60.0,
        'max': 80.0
    },
    'inme': {
        'min': 20.0,
        'max': 100.0
    }
}

class TestereState(Enum):
    IDLE = 0
    READY = 1
    STARTING = 2
    CUTTING = 3
    FINISHING = 4
    MOVING_UP = 5
    MATERIAL_FEED = 7

class ControlMode(Enum):
    MANUAL = "manual"
    FUZZY = "fuzzy"
    LINEAR = "linear"
    DYNAMIC = "dynamic"
    LSTM = "lstm"