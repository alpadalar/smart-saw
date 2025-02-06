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

class ControllerType(Enum):
    """Kontrol sistemi tipleri"""
    EXPERT = "expert"
    LINEAR = "linear"
    FUZZY = "fuzzy"


class ControllerFactory:
    """Kontrol sistemi factory sınıfı"""
    
    def __init__(self, modbus_client=None):
        self.modbus_client = modbus_client
        self._controllers: Dict[ControllerType, Callable] = {
            ControllerType.FUZZY: fuzzy_adjust,
            ControllerType.EXPERT: expert_adjust,
            ControllerType.LINEAR: linear_adjust,
        }
        self._active_controller: Optional[ControllerType] = None
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

    def adjust_speeds(self, *args, **kwargs) -> tuple:
        """
        Aktif kontrol sistemi ile hız ayarlaması yapar
        
        Returns:
            tuple: (last_modbus_write_time, output_value)
            
        Raises:
            ControllerNotFoundError: Aktif kontrol sistemi yoksa
        """
        if not self._active_controller:
            return kwargs.get('last_modbus_write_time', 0), None

        try:
            # İstatistikleri güncelle
            stats = self._controller_stats[self._active_controller]
            stats["total_runs"] += 1
            stats["last_run"] = time.time()
            
            # Modbus client'ı kwargs'a ekle
            if self.modbus_client and 'modbus_client' not in kwargs:
                kwargs['modbus_client'] = self.modbus_client
            
            # Kontrol sistemini çalıştır
            start_time = time.time()
            result = self._controllers[self._active_controller](*args, **kwargs)
            elapsed = time.time() - start_time
            
            # Çalışma süresini ekle
            stats["total_time"] += elapsed
            
            if result is None:
                logger.warning(f"Kontrol sistemi ({self._active_controller.value}) çıktı üretmedi")
                return kwargs.get('last_modbus_write_time', 0), None
                
            # Sonucu kontrol et
            if not isinstance(result, tuple) or len(result) != 2:
                logger.error(f"Kontrol sistemi ({self._active_controller.value}) geçersiz çıktı üretti: {result}")
                return kwargs.get('last_modbus_write_time', 0), None
                
            last_modbus_write_time, output_value = result
            logger.debug(f"Kontrol sistemi ({self._active_controller.value}) çıktısı: {output_value}")
            
            return result
            
        except Exception as e:
            # Hata istatistiğini güncelle
            stats["errors"] += 1
            logger.error(f"Kontrol sistemi hatası ({self._active_controller.value}): {str(e)}")
            logger.exception("Detaylı hata:")
            return kwargs.get('last_modbus_write_time', 0), None

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

