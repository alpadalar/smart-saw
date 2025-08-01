# src/utils/helpers.py
import time
import math
from datetime import datetime
from typing import Union, Optional
from core.logger import logger
from core.constants import (
    SPEED_LIMITS,
    KESME_HIZI_REGISTER_ADDRESS,
    INME_HIZI_REGISTER_ADDRESS
)

# Register adresleri
REGISTER_ADDRESSES = {
    'serit_kesme_hizi': KESME_HIZI_REGISTER_ADDRESS,  # Kesme hızı register adresi (2066)
    'serit_inme_hizi': INME_HIZI_REGISTER_ADDRESS,   # İnme hızı register adresi (2041)
}

def reverse_calculate_value(modbus_client, value: int, register_type: str, is_negative: bool = False) -> None:
    """
    Verilen int değeri direkt modbus register'ına yazar
    
    Args:
        modbus_client: Modbus bağlantı nesnesi
        value: Yazılacak int değer
        register_type: Register tipi ('serit_kesme_hizi' veya 'serit_inme_hizi')
        is_negative: Değer negatif mi (sadece inme hızı için)
    """
    try:
        if register_type == 'serit_kesme_hizi':
            # Kesme hızı için direkt int değer
            modbus_value = int(value)
            logger.debug(f"Kesme hızı yazılmaya çalışılıyor:")
            logger.debug(f"  Değer: {value}")
            logger.debug(f"  Modbus değeri: {modbus_value}")
            logger.debug(f"  Register: {REGISTER_ADDRESSES[register_type]}")
            
            result = modbus_client.write_register(REGISTER_ADDRESSES[register_type], modbus_value)
            logger.debug(f"  Yazma sonucu: {'Başarılı' if result else 'Başarısız'}")
            time.sleep(0.110)  # 110ms bekle
            
        elif register_type == 'serit_inme_hizi':
            # İnme hızı için direkt int değer
            modbus_value = int(value)
            logger.debug(f"İnme hızı yazılmaya çalışılıyor:")
            logger.debug(f"  Değer: {value}")
            logger.debug(f"  Modbus değeri: {modbus_value}")
            logger.debug(f"  Register: {REGISTER_ADDRESSES[register_type]}")
            
            result = modbus_client.write_register(REGISTER_ADDRESSES[register_type], modbus_value)
            logger.debug(f"  Yazma sonucu: {'Başarılı' if result else 'Başarısız'}")
            time.sleep(0.110)  # 110ms bekle
            
    except Exception as e:
        logger.error(f"Modbus yazma hatası: {str(e)}")
        logger.exception("Detaylı hata:")
        raise


def calculate_speed_value(raw_value: int, register_type: str) -> float:
    """
    Ham modbus değerini gerçek hız değerine çevirir
    
    Args:
        raw_value: Ham modbus değeri
        register_type: Register tipi ('serit_kesme_hizi' veya 'serit_inme_hizi')
        
    Returns:
        float: Gerçek hız değeri
    """
    try:
        if register_type == 'serit_kesme_hizi':
            return raw_value * 0.0754
            
        elif register_type == 'serit_inme_hizi':
            if raw_value == 0:
                return 0.0
            else:
                return (raw_value - 65535) * -0.06
                
    except Exception as e:
        logger.error(f"Hız hesaplama hatası: {str(e)}")
        raise


def validate_speed_limits(speed: float, speed_type: str) -> float:
    """
    Hız değerinin limitler içinde olduğunu kontrol eder
    
    Args:
        speed: Kontrol edilecek hız değeri
        speed_type: Hız tipi ('kesme' veya 'inme')
        
    Returns:
        float: Sınırlandırılmış hız değeri
    """
    limits = SPEED_LIMITS[speed_type]
    return max(limits['min'], min(speed, limits['max']))


def format_time(milliseconds: float) -> str:
    """
    Milisaniye cinsinden süreyi formatlar
    
    Args:
        milliseconds: Formatlanacak süre (milisaniye)
        
    Returns:
        str: "MM:SS.mmm" formatında süre
    """
    # Milisaniyeleri ayır
    ms = int(milliseconds % 1000)
    seconds = milliseconds // 1000
    
    # Dakika ve saniye hesapla
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    
    return f"{minutes:02d}:{seconds:02d}.{ms:03d}"


def get_current_time_ms() -> str:
    """
    Şu anki zamanı milisaniye hassasiyetinde döndürür
    
    Returns:
        str: "HH:MM:SS.mmm" formatında zaman
    """
    return datetime.now().strftime('%H:%M:%S.%f')[:-3]


def calculate_elapsed_time_ms(start_time: float) -> float:
    """
    Başlangıç zamanından bu yana geçen süreyi milisaniye cinsinden hesaplar
    
    Args:
        start_time: Başlangıç zamanı (time.time() * 1000)
        
    Returns:
        float: Geçen süre (milisaniye)
    """
    return (time.time() * 1000) - start_time


def calculate_moving_average(values: list, window_size: int = 5) -> Optional[float]:
    """
    Hareketli ortalama hesaplar
    
    Args:
        values: Değer listesi
        window_size: Pencere boyutu
        
    Returns:
        float: Hareketli ortalama veya None
    """
    if not values or len(values) < window_size:
        return None
        
    return sum(values[-window_size:]) / window_size


class DataValidator:
    """Veri doğrulama sınıfı"""
    
    @staticmethod
    def validate_current(current: float) -> bool:
        """Akım değerini kontrol eder"""
        return 0 <= current <= 30.0
        
    @staticmethod
    def validate_deviation(deviation: float) -> bool:
        """Sapma değerini kontrol eder"""
        return -2.0 <= deviation <= 2.0
        
    @staticmethod
    def validate_height(height: float) -> bool:
        """Yükseklik değerini kontrol eder"""
        return 0 <= height <= 300.0
        
    @staticmethod
    def validate_speed(speed: float, speed_type: str) -> bool:
        """Hız değerini kontrol eder"""
        limits = SPEED_LIMITS[speed_type]
        return limits['min'] <= abs(speed) <= limits['max']


# Test kodu
if __name__ == "__main__":
    # Örnek kullanım
    print(format_time(90061123))  # "1 gün 01:01:01.123"
    print(get_current_time_ms())  # "14:30:45.123"
    
    import time
    start = time.time() * 1000
    time.sleep(1.234)  # 1.234 saniye bekle
    elapsed = calculate_elapsed_time_ms(start)
    print(f"Geçen süre: {format_time(elapsed)}")  # "00:00:01.234"
    
    # Hız limitleri testi
    test_speed = 150
    limited_speed = validate_speed_limits(test_speed, 'kesme')
    print(f"Orijinal hız: {test_speed}, Sınırlandırılmış hız: {limited_speed}")