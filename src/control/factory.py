# src/control/factory.py
import time
from enum import Enum
from typing import Optional, Callable, Dict, Any
from core.logger import logger
from core.exceptions import ControllerNotFoundError

# Kontrol sistemleri
from .expert.controller import adjust_speeds as expert_adjust
from .linear.controller import adjust_speeds_linear as linear_adjust
from .fuzzy.controller import adjust_speeds_fuzzy as fuzzy_adjust
from .ml.controller import adjust_speeds_ml as ml_adjust

class ControllerType(Enum):
    """Kontrol sistemi tipleri"""
    EXPERT = "expert"
    LINEAR = "linear"
    FUZZY = "fuzzy"
    ML = "ml"  # Yeni kontrol sistemi


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
            # İnme hızı kontrolü - 0 ise hiçbir işlem yapma
            current_inme_hizi = float(processed_data.get('serit_inme_hizi', 0))
            if current_inme_hizi == 0:
                logger.debug("İnme hızı 0, hız ayarlaması yapılmayacak")
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

