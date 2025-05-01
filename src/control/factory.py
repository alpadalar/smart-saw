# src/control/factory.py
import time
from enum import Enum
from typing import Optional, Callable, Dict, Any
from core.logger import logger
from core.exceptions import ControllerNotFoundError
from core.constants import CONTROL_INITIAL_DELAY, SPEED_LIMITS, TestereState, ControllerType

# Kontrol sistemleri
from .expert.controller import adjust_speeds as expert_adjust
from .linear.controller import adjust_speeds_linear as linear_adjust
from .fuzzy.controller import adjust_speeds_fuzzy as fuzzy_adjust
from .ml.controller import adjust_speeds_ml as ml_adjust


class ControllerFactory:
    """Kontrol sistemi factory sınıfı"""
    
    def __init__(self, modbus_client=None):
        self.modbus_client = modbus_client
        self._active_controller = None
        self._controllers: Dict[ControllerType, Callable] = {
            ControllerType.FUZZY: fuzzy_adjust,
            ControllerType.EXPERT: expert_adjust,
            ControllerType.LINEAR: linear_adjust,
            ControllerType.ML: ml_adjust,  # Yeni kontrol sistemi
        }
        self._controller_stats: Dict[ControllerType, Dict[str, Any]] = {
            controller_type: {
                "total_runs": 0,
                "total_time": 0,
                "last_run": None,
                "errors": 0
            } for controller_type in ControllerType
        }
        
        # Başlangıç gecikmesi için değişkenler
        self.cutting_start_time = None
        self.is_cutting = False
        self.initial_delay = CONTROL_INITIAL_DELAY['DEFAULT_DELAY_MS']
        self.last_processed_data = None

    def _calculate_initial_delay(self, inme_hizi: float) -> int:
        """İnme hızına göre hedef mesafeyi inecek süreyi hesaplar"""
        try:
            # İnme hızı mm/dakika cinsinden
            if inme_hizi <= 0:
                return CONTROL_INITIAL_DELAY['DEFAULT_DELAY_MS']
            
            # Hedef mesafeyi inmek için gereken süreyi hesapla (milisaniye cinsinden)
            # inme_hizi mm/dakika -> mm/saniye -> hedef_mesafe için gereken süre
            delay_ms = (CONTROL_INITIAL_DELAY['TARGET_DISTANCE_MM'] / (inme_hizi / 60)) * 1000
            
            # Minimum ve maksimum sınırları uygula
            delay_ms = max(
                CONTROL_INITIAL_DELAY['MIN_DELAY_MS'],
                min(delay_ms, CONTROL_INITIAL_DELAY['MAX_DELAY_MS'])
            )
            
            logger.info(f"İnme hızı: {inme_hizi:.2f} mm/dakika için hesaplanan bekleme süresi: {delay_ms/1000:.1f} saniye")
            return int(delay_ms)
            
        except Exception as e:
            logger.error(f"Bekleme süresi hesaplama hatası: {str(e)}")
            return CONTROL_INITIAL_DELAY['DEFAULT_DELAY_MS']

    def _check_cutting_state(self, testere_durumu: int) -> bool:
        """Kesim durumunu kontrol eder ve başlangıç gecikmesini yönetir"""
        try:
            current_time = time.time() * 1000
            
            # Kesim durumu değişikliğini kontrol et
            if testere_durumu != TestereState.KESIM_YAPILIYOR.value:  # KESIM_YAPILIYOR
                if self.is_cutting:
                    self.is_cutting = False
                    self.cutting_start_time = None
                return False

            # Kesim başlangıcını kontrol et
            if not self.is_cutting:
                self.is_cutting = True
                self.cutting_start_time = current_time
                
                # İnme hızını al ve dinamik bekleme süresini hesapla
                inme_hizi = float(self.last_processed_data.get('serit_inme_hizi', SPEED_LIMITS['inme']['min'])) if self.last_processed_data else SPEED_LIMITS['inme']['min']
                self.initial_delay = self._calculate_initial_delay(inme_hizi)
                logger.info(f"Yeni bekleme süresi: {self.initial_delay/1000:.1f} saniye")

            # Başlangıç gecikmesi kontrolü
            if current_time - self.cutting_start_time < self.initial_delay:
                kalan_sure = int((self.initial_delay - (current_time - self.cutting_start_time)) / 1000)
                if kalan_sure % 5 == 0:
                    logger.info(f"Kontrol sisteminin devreye girmesine {kalan_sure} saniye kaldı...")
                return False

            return True
            
        except Exception as e:
            logger.error(f"Kesim durumu kontrol hatası: {str(e)}")
            return False

    @property
    def active_controller(self) -> Optional[ControllerType]:
        """Aktif kontrol sistemini döndürür"""
        return self._active_controller

    @active_controller.setter
    def active_controller(self, value):
        """Aktif kontrol sistemini ayarlar"""
        self._active_controller = value

    def set_controller(self, controller_type: Optional[ControllerType]) -> None:
        """
        Aktif kontrol sistemini değiştirir
        
        Args:
            controller_type: Kullanılacak kontrol sistemi tipi. None ise kontrol sistemi kapatılır.
            
        Raises:
            ControllerNotFoundError: Belirtilen kontrol sistemi bulunamadığında
        """
        if controller_type is None:
            logger.info("Kontrol sistemi kapatıldı")
            self._active_controller = None
            return
            
        if not isinstance(controller_type, ControllerType):
            raise ControllerNotFoundError(f"Geçersiz kontrol sistemi tipi: {controller_type}")
            
        if controller_type not in self._controllers:
            raise ControllerNotFoundError(f"Kontrol sistemi bulunamadı: {controller_type.value}")
            
        if self._active_controller != controller_type:
            logger.info(f"Kontrol sistemi değiştirildi: {controller_type.value}")
            self._active_controller = controller_type

    def set_modbus_client(self, modbus_client):
        """Modbus client'ı ayarlar"""
        self.modbus_client = modbus_client

    def get_controller(self) -> Callable:
        """
        Aktif kontrol sisteminin fonksiyonunu döndürür
        
        Returns:
            Callable: Kontrol sistemi fonksiyonu
            
        Raises:
            ControllerNotFoundError: Aktif kontrol sistemi yoksa
        """
        if not self._active_controller:
            raise ControllerNotFoundError("Aktif kontrol sistemi bulunamadı")
            
        return self._controllers[self._active_controller]

    def adjust_speeds(self, processed_data, modbus_client, last_modbus_write_time, 
                     speed_adjustment_interval, prev_current):
        """Aktif kontrolcü ile hız ayarlaması yapar"""
        try:
            # Son işlenen veriyi güncelle
            self.last_processed_data = processed_data
            
            # İnme hızı kontrolü - 0 ise hiçbir işlem yapma
            current_inme_hizi = float(processed_data.get('serit_inme_hizi', 0))
            if current_inme_hizi == 0:
                logger.debug("İnme hızı 0, hız ayarlaması yapılmayacak")
                return last_modbus_write_time, None

            # Kesim durumu kontrolü
            testere_durumu = int(processed_data.get('testere_durumu', 0))
            if not self._check_cutting_state(testere_durumu):
                logger.debug("Kesim durumu uygun değil veya başlangıç gecikmesi devam ediyor")
                return last_modbus_write_time, None

            # Aktif kontrolcü ile hız ayarlaması yap
            if self._active_controller:
                return self._controllers[self._active_controller](
                    processed_data=processed_data,
                    modbus_client=modbus_client,
                    last_modbus_write_time=last_modbus_write_time,
                    speed_adjustment_interval=speed_adjustment_interval,
                    prev_current=prev_current
                )
            return last_modbus_write_time, None
            
        except Exception as e:
            # Hata istatistiğini güncelle
            if self._active_controller:
                stats = self._controller_stats[self._active_controller]
                stats["errors"] += 1
            logger.error(f"Hız ayarlama hatası: {str(e)}")
            logger.exception("Detaylı hata:")
            return last_modbus_write_time, None

    def get_stats(self, controller_type: Optional[ControllerType] = None) -> Dict:
        """
        Kontrol sistemi istatistiklerini döndürür
        
        Args:
            controller_type: İstatistikleri istenilen kontrol sistemi (None ise tümü)
            
        Returns:
            Dict: İstatistik bilgileri
        """
        if controller_type:
            stats = self._controller_stats[controller_type]
            avg_time = stats["total_time"] / stats["total_runs"] if stats["total_runs"] > 0 else 0
            return {
                "type": controller_type.value,
                "total_runs": stats["total_runs"],
                "total_time": stats["total_time"],
                "average_time": avg_time,
                "last_run": stats["last_run"],
                "errors": stats["errors"]
            }
        else:
            return {
                ct.value: self.get_stats(ct)
                for ct in ControllerType
            }


# Global controller factory nesnesi
_controller_factory = ControllerFactory()


def get_controller_factory() -> ControllerFactory:
    """Global controller factory nesnesini döndürür"""
    return _controller_factory

