# src/utils/delay_calculator.py
import time
from typing import Optional
from core.logger import logger
from core.constants import CONTROL_INITIAL_DELAY, INME_HIZI_REGISTER_ADDRESS


class DelayCalculator:
    """İnme hızına göre dinamik başlangıç gecikmesi hesaplayan sınıf"""
    
    def __init__(self):
        self.last_calculated_delay = CONTROL_INITIAL_DELAY['DEFAULT_DELAY_MS']
        self.last_read_time = 0
        self.cache_duration = 5.0  # 5 saniye cache
    
    def calculate_initial_delay(self, modbus_client, target_distance_mm: Optional[float] = None) -> int:
        """
        Modbus register'dan inme hızını okuyarak dinamik gecikme hesaplar
        
        Args:
            modbus_client: Modbus istemcisi
            target_distance_mm: Hedef inme mesafesi (None ise constants'tan alır)
            
        Returns:
            int: Hesaplanan gecikme süresi (milisaniye)
        """
        try:
            # Cache kontrolü - son 5 saniye içinde hesaplanmışsa tekrar hesaplama
            current_time = time.time()
            if current_time - self.last_read_time < self.cache_duration:
                logger.debug(f"Cache'den gecikme döndürülüyor: {self.last_calculated_delay/1000:.1f} saniye")
                return self.last_calculated_delay
            
            # İnme hızını register'dan oku
            inme_hizi = self._read_inme_hizi_from_register(modbus_client)
            
            if inme_hizi is None or inme_hizi <= 0:
                logger.warning("İnme hızı okunamadı veya sıfır, varsayılan gecikme kullanılıyor")
                return CONTROL_INITIAL_DELAY['DEFAULT_DELAY_MS']
            
            # Hedef mesafeyi belirle
            if target_distance_mm is None:
                target_distance_mm = CONTROL_INITIAL_DELAY['TARGET_DISTANCE_MM']
            
            # Gecikme hesapla: Hedef mesafe / İnme hızı * 60 (dakika->saniye) * 1000 (saniye->ms)
            delay_ms = (target_distance_mm / inme_hizi) * 60 * 1000
            
            # Sınırları uygula
            delay_ms = max(
                CONTROL_INITIAL_DELAY['MIN_DELAY_MS'],
                min(delay_ms, CONTROL_INITIAL_DELAY['MAX_DELAY_MS'])
            )
            
            # Cache güncelle
            self.last_calculated_delay = int(delay_ms)
            self.last_read_time = current_time
            
            logger.info(
                f"İnme hızı register'dan okundu: {inme_hizi:.2f} mm/dakika, "
                f"Hedef mesafe: {target_distance_mm:.0f}mm, "
                f"Hesaplanan gecikme: {delay_ms/1000:.1f} saniye"
            )
            
            return int(delay_ms)
            
        except Exception as e:
            logger.error(f"Gecikme hesaplama hatası: {str(e)}")
            return CONTROL_INITIAL_DELAY['DEFAULT_DELAY_MS']
    
    def _read_inme_hizi_from_register(self, modbus_client) -> Optional[float]:
        """
        İnme hızını doğrudan modbus register'dan okur
        
        Args:
            modbus_client: Modbus istemcisi
            
        Returns:
            Optional[float]: İnme hızı değeri (mm/dakika) veya None
        """
        try:
            if not modbus_client or not modbus_client.is_connected:
                logger.warning("Modbus bağlantısı yok")
                return None
            
            # İnme hızı register'ını oku
            start_time = time.time()
            registers = modbus_client.read_registers(
                address=INME_HIZI_REGISTER_ADDRESS, 
                count=1
            )
            read_time = time.time() - start_time
            
            if registers is None or len(registers) == 0:
                logger.warning(f"İnme hızı register'ı okunamadı (adres: {INME_HIZI_REGISTER_ADDRESS})")
                return None
            
            # Register değerini direkt inme hızı olarak al (zaten int değer)
            inme_hizi = registers[0]
            
            # İnme hızını 100'e böl
            inme_hizi = inme_hizi / 100.0
            
            # Sıfır veya negatif değer kontrolü
            if inme_hizi <= 0:
                logger.warning(f"Geçersiz inme hızı değeri: {inme_hizi}")
                return None
            
            logger.debug(f"Register {INME_HIZI_REGISTER_ADDRESS} okundu: {inme_hizi} mm/dakika (Süre: {read_time*1000:.1f}ms)")
            
            return float(inme_hizi)
            
        except Exception as e:
            logger.error(f"İnme hızı register okuma hatası: {str(e)}")
            return None
    
    def get_last_calculated_delay(self) -> int:
        """Son hesaplanan gecikme değerini döndürür"""
        return self.last_calculated_delay
    
    def reset_cache(self):
        """Cache'i sıfırlar"""
        self.last_read_time = 0
        logger.debug("Gecikme hesaplama cache'i sıfırlandı")


# Global instance
_delay_calculator = DelayCalculator()


def calculate_control_delay(modbus_client, target_distance_mm: Optional[float] = None) -> int:
    """
    Global delay calculator kullanarak gecikme hesaplar
    
    Args:
        modbus_client: Modbus istemcisi
        target_distance_mm: Hedef inme mesafesi (opsiyonel)
        
    Returns:
        int: Hesaplanan gecikme süresi (milisaniye)
    """
    return _delay_calculator.calculate_initial_delay(modbus_client, target_distance_mm)


def reset_delay_cache():
    """Global delay calculator cache'ini sıfırlar"""
    _delay_calculator.reset_cache()


def get_last_delay() -> int:
    """Son hesaplanan gecikme değerini döndürür"""
    return _delay_calculator.get_last_calculated_delay()
