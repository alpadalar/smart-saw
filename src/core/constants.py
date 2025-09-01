from enum import Enum
import os

# Modbus Register Adresleri
KESME_HIZI_REGISTER_ADDRESS = 2066
INME_HIZI_REGISTER_ADDRESS = 2041

# Model yolu
ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", "")

# Hız Limitleri
MIN_SPEED = 5.0
MAX_SPEED = 100.0

SPEED_LIMITS = {
    'kesme': {
        'min': 40.0,
        'max': 90.0
    },
    'inme': {
        'min': 10.0,
        'max': 60.0
    }
}

# Tork -> Akım dönüşüm katsayıları
# f(x) = A2*x^2 + A1*x + A0
# x: serit_motor_tork_percentage (yüzde), çıktı: akım (A)
TORQUE_TO_CURRENT_A2 = 0.015
TORQUE_TO_CURRENT_A1 = -0.338
TORQUE_TO_CURRENT_A0 = 16.272

# Fuzzy Kontrol Parametreleri
IDEAL_AKIM = 17.0
MIN_SPEED_UPDATE_INTERVAL = 1.0 / 5.0  # 5 Hz
KATSAYI = 1.0

# Kontrol Sistemi Başlangıç Parametreleri
CONTROL_INITIAL_DELAY = {
    'MIN_DELAY_MS': 5000,      # Minimum bekleme süresi (5 saniye)
    'MAX_DELAY_MS': 60000,     # Maksimum bekleme süresi (60 saniye)
    'TARGET_DISTANCE_MM': 4, # Hedef inme mesafesi (mm)
    'DEFAULT_DELAY_MS': 30000, # Varsayılan bekleme süresi (30 saniye)
    'REGISTER_READ_TIMEOUT': 2.0  # Register okuma timeout (saniye)
}

# Buffer Parametreleri
BUFFER_SIZE = 3  # Her tampon için maksimum örnek sayısı
BUFFER_DURATION = 0.5  # Tampon süresi (saniye)

# Kamera Ayarları
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1200
CAMERA_FPS = 50
CAMERA_DEVICE_ID = 1  # 0: dahili kamera, 1: harici kamera
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

# Kontrol modları
class ControllerType(Enum):
    MANUAL = "manual"
    FUZZY = "fuzzy"
    LINEAR = "linear"
    DYNAMIC = "dynamic"
    LSTM = "lstm"
    ML = "ml"
    EXPERT = "expert"  # Uzman sistemi

# Geriye dönük uyumluluk için ControlMode'u da koruyalım
ControlMode = ControllerType