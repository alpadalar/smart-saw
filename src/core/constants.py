from enum import Enum
import os

# Modbus Register Adresleri
KESME_HIZI_REGISTER_ADDRESS = 2066
INME_HIZI_REGISTER_ADDRESS = 2041

# Model yolları (platform-independent paths)
ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", os.path.join("src", "control", "ml", "Bagging_dataset_v17_20250509.pkl"))
BROKEN_DETECTION_MODEL_PATH = os.getenv("BROKEN_MODEL_PATH", "best.pt")
CRACK_DETECTION_MODEL_PATH = os.getenv("CRACK_MODEL_PATH", "catlak-best.pt")

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
TORQUE_TO_CURRENT_A1 = -0.278
TORQUE_TO_CURRENT_A0 = 15.656

# Fuzzy Kontrol Parametreleri
IDEAL_AKIM = 17.0
MIN_SPEED_UPDATE_INTERVAL = 1.0 / 5.0  # 5 Hz (ML controller için minimum güncelleme aralığı)
KATSAYI = 1.0

# ============================================================================
# MODBUS VE VERİ İŞLEME HIZ PARAMETRELERİ
# ============================================================================

# Modbus Bağlantı Parametreleri
MODBUS_RECONNECT_INTERVAL = 2.0           # Bağlantı koptuğunda yeniden bağlanma aralığı (saniye)
MODBUS_CONNECTION_STABILIZATION_DELAY = 0.15  # Bağlantı sonrası stabilizasyon gecikmesi (saniye)
MODBUS_WRITE_INTERVAL = 0.1               # Minimum yazma aralığı (saniye) - max 10 yazma/sn

# Veri İşleme Parametreleri
MAIN_LOOP_DELAY = 0.0                     # Ana döngü gecikmesi (saniye) - 0 = maksimum hız
DATA_PROCESSING_WARNING_THRESHOLD = 6     # Saniyede minimum veri sayısı (altında uyarı verir)

# ============================================================================
# TORQUE GUARD PARAMETRELERİ (Kafa Yüksekliği Bazlı Tork Kontrolü)
# ============================================================================

TORQUE_BUFFER_SIZE = 3                    # Ortalama alınacak son tork örneği sayısı
TORQUE_HEIGHT_LOOKBACK_MM = 2.5           # Kaç mm geriye bakılacak
TORQUE_INITIAL_THRESHOLD_MM = 2.5         # İlk kaç mm'den sonra kontrol başlayacak
TORQUE_INCREASE_THRESHOLD = 40.0          # %50 artış eşiği (yüzde)
DESCENT_REDUCTION_PERCENT = 25.0          # İnme hızı azaltma oranı (yüzde)
ENABLE_TORQUE_GUARD = True                # Torque Guard aktif/pasif

# Kontrol Sistemi Başlangıç Parametreleri
CONTROL_INITIAL_DELAY = {
    'MIN_DELAY_MS': 5000,      # Minimum bekleme süresi (5 saniye)
    'MAX_DELAY_MS': 60000,     # Maksimum bekleme süresi (60 saniye)
    'TARGET_DISTANCE_MM': 10, # Hedef inme mesafesi (mm)
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