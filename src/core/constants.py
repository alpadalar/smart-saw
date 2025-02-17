from enum import Enum

# Modbus Register Adresleri
KESME_HIZI_REGISTER_ADDRESS = 2066
INME_HIZI_REGISTER_ADDRESS = 2041

# Model yolu
ML_MODEL_PATH = "src/control/ml/trained_model_Support Vector Regressor.pkl"

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

# Fuzzy Kontrol Parametreleri
IDEAL_AKIM = 17.0
MIN_SPEED_UPDATE_INTERVAL = 1.0  # 1 Hz
BASLANGIC_GECIKMESI = 15000.0  # 15 saniye (ms)
KATSAYI = 1.2

# Buffer Parametreleri
BUFFER_SIZE = 10  # Her tampon için maksimum örnek sayısı
BUFFER_DURATION = 1.0  # Tampon süresi (saniye)

class TestereState(Enum):
    IDLE = 0
    READY = 1
    STARTING = 2
    CUTTING = 3
    FINISHING = 4
    MOVING_UP = 5
    MATERIAL_FEED = 6

class ControlMode(Enum):
    MANUAL = "manual"
    FUZZY = "fuzzy"
    LINEAR = "linear"
    DYNAMIC = "dynamic"
    LSTM = "lstm"
    ML = "ml"  # Yeni kontrol modu