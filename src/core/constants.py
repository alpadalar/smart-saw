from enum import Enum

# Modbus Register Adresleri
KESME_HIZI_REGISTER_ADDRESS = 2066
INME_HIZI_REGISTER_ADDRESS = 2041

# Model yolu
ML_MODEL_PATH = "src/control/ml/dataset_v5_model_MLPRegressor.pkl"

# Hız Limitleri
MIN_SPEED = 5.0
MAX_SPEED = 100.0

SPEED_LIMITS = {
    'kesme': {
        'min': 40.0,
        'max': 110.0
    },
    'inme': {
        'min': 10.0,
        'max': 80.0
    }
}

# Fuzzy Kontrol Parametreleri
IDEAL_AKIM = 17.0
MIN_SPEED_UPDATE_INTERVAL = 0.33  # 3 Hz
BASLANGIC_GECIKMESI = 12000.0  # 15 saniye (ms)
KATSAYI = 1.0

# Buffer Parametreleri
BUFFER_SIZE = 6  # Her tampon için maksimum örnek sayısı
BUFFER_DURATION = 1.0  # Tampon süresi (saniye)

# Kamera Ayarları
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1200
CAMERA_FPS = 50
CAMERA_DEVICE_ID = 0  # 0: dahili kamera, 1: harici kamera
CAMERA_JPEG_QUALITY = 92
CAMERA_NUM_THREADS = 4
CAMERA_RECORDINGS_DIR = "recordings"  # Kayıtların saklanacağı ana dizin

# Testere Durumları
class TestereState(Enum):
    BOSTA = 0
    HIDROLIK_AKTIF = 1
    SERIT_MOTOR_CALISIYOR = 2
    KESIM_YAPILIYOR = 3
    KESIM_BITTI = 4
    SERIT_YUKARI_CIKIYOR = 5
    MALZEME_BESLEME = 6

class ControlMode(Enum):
    MANUAL = "manual"
    FUZZY = "fuzzy"
    LINEAR = "linear"
    DYNAMIC = "dynamic"
    LSTM = "lstm"
    ML = "ml"  # Yeni kontrol modu