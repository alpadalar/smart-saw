"""
Anomaly Manager
Tüm anomaly detector'ları yönetir ve thread-safe çalışır
"""

import threading
from typing import Dict, Optional, Callable
import logging

from .serit_sapmasi import SeritSapmasiDetector
from .serit_motor_akim import SeritMotorAkimDetector
from .serit_motor_tork import SeritMotorTorkDetector
from .serit_kesme_hizi import SeritKesmeHiziDetector
from .serit_inme_hizi import SeritInmeHiziDetector
from .titresim_x import TitresimXDetector
from .titresim_y import TitresimYDetector
from .titresim_z import TitresimZDetector
from .serit_gerginligi import SeritGerginligiDetector

logger = logging.getLogger(__name__)


class AnomalyManager:
    """
    Tüm anomaly detector'ları yöneten thread-safe manager sınıfı
    """
    
    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        """
        Args:
            buffer_size: Her detector için buffer boyutu
            min_samples: Detection için minimum örnek sayısı
        """
        self.buffer_size = buffer_size
        self.min_samples = min_samples
        
        # Thread-safe lock
        self._lock = threading.Lock()
        
        # Detector'ları oluştur
        self.detectors = {
            'serit_sapmasi': SeritSapmasiDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'serit_motor_akim': SeritMotorAkimDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'serit_motor_tork': SeritMotorTorkDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'serit_kesme_hizi': SeritKesmeHiziDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'serit_inme_hizi': SeritInmeHiziDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'titresim_x': TitresimXDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'titresim_y': TitresimYDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'titresim_z': TitresimZDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'serit_gerginligi': SeritGerginligiDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
        }
        
        # Anomali durumları (pyside_sensor.py'deki anahtarlarla eşleşmeli)
        self.anomaly_states = {
            'SeritSapmasi': False,
            'SeritAkim': False,
            'KesmeHizi': False,
            'IlerlemeHizi': False,
            'TitresimX': False,
            'TitresimY': False,
            'TitresimZ': False,
            'SeritGerginligi': False,
            'SeritTork': False,
        }
        
        # Callback fonksiyonu (pyside_sensor.py'deki anomaly_states'i güncellemek için)
        self._update_callback: Optional[Callable[[str, bool], None]] = None
        
        logger.info("AnomalyManager başlatıldı")
        logger.info(f"  - Detector sayısı: {len(self.detectors)}")
        logger.info(f"  - Buffer boyutu: {buffer_size}")
        logger.info(f"  - Minimum örnek sayısı: {min_samples}")
    
    def set_update_callback(self, callback: Callable[[str, bool], None]) -> None:
        """
        Anomali durumu güncelleme callback'ini ayarlar
        
        Args:
            callback: (sensor_key, is_anomaly) -> None fonksiyonu
        """
        self._update_callback = callback
        logger.info("AnomalyManager update callback ayarlandı")
    
    def process_data(self, data: Dict, is_cutting: bool = False) -> Dict[str, bool]:
        """
        Yeni veri işler ve anomali tespiti yapar (thread-safe)
        
        Args:
            data: İşlenmiş veri dictionary'si
            is_cutting: Kesim yapılıyor mu?
            
        Returns:
            Anomali durumları dictionary'si
        """
        try:
            with self._lock:
                # Her detector için veri ekle ve detection yap
                results = {}
                
                # Serit sapması
                if 'serit_sapmasi' in data:
                    value = data.get('serit_sapmasi', 0.0)
                    self.detectors['serit_sapmasi'].add_data_point(value, is_cutting)
                    is_anomaly = self.detectors['serit_sapmasi'].detect()
                    results['SeritSapmasi'] = is_anomaly
                    self.anomaly_states['SeritSapmasi'] = is_anomaly
                
                # Serit motor akım
                if 'serit_motor_akim_a' in data:
                    value = data.get('serit_motor_akim_a', 0.0)
                    self.detectors['serit_motor_akim'].add_data_point(value, is_cutting)
                    is_anomaly = self.detectors['serit_motor_akim'].detect()
                    results['SeritAkim'] = is_anomaly
                    self.anomaly_states['SeritAkim'] = is_anomaly
                
                # Serit motor tork
                if 'serit_motor_tork_percentage' in data:
                    value = data.get('serit_motor_tork_percentage', 0.0)
                    self.detectors['serit_motor_tork'].add_data_point(value, is_cutting)
                    is_anomaly = self.detectors['serit_motor_tork'].detect()
                    results['SeritTork'] = is_anomaly
                    self.anomaly_states['SeritTork'] = is_anomaly
                
                # Serit kesme hızı
                if 'serit_kesme_hizi' in data:
                    value = data.get('serit_kesme_hizi', 0.0)
                    self.detectors['serit_kesme_hizi'].add_data_point(value, is_cutting)
                    is_anomaly = self.detectors['serit_kesme_hizi'].detect()
                    results['KesmeHizi'] = is_anomaly
                    self.anomaly_states['KesmeHizi'] = is_anomaly
                
                # Serit inme hızı
                if 'serit_inme_hizi' in data:
                    value = data.get('serit_inme_hizi', 0.0)
                    self.detectors['serit_inme_hizi'].add_data_point(value, is_cutting)
                    is_anomaly = self.detectors['serit_inme_hizi'].detect()
                    results['IlerlemeHizi'] = is_anomaly
                    self.anomaly_states['IlerlemeHizi'] = is_anomaly
                
                # Titresim X
                if 'ivme_olcer_x_hz' in data:
                    value = data.get('ivme_olcer_x_hz', 0.0)
                    self.detectors['titresim_x'].add_data_point(value, is_cutting)
                    is_anomaly = self.detectors['titresim_x'].detect()
                    results['TitresimX'] = is_anomaly
                    self.anomaly_states['TitresimX'] = is_anomaly
                
                # Titresim Y
                if 'ivme_olcer_y_hz' in data:
                    value = data.get('ivme_olcer_y_hz', 0.0)
                    self.detectors['titresim_y'].add_data_point(value, is_cutting)
                    is_anomaly = self.detectors['titresim_y'].detect()
                    results['TitresimY'] = is_anomaly
                    self.anomaly_states['TitresimY'] = is_anomaly
                
                # Titresim Z
                if 'ivme_olcer_z_hz' in data:
                    value = data.get('ivme_olcer_z_hz', 0.0)
                    self.detectors['titresim_z'].add_data_point(value, is_cutting)
                    is_anomaly = self.detectors['titresim_z'].detect()
                    results['TitresimZ'] = is_anomaly
                    self.anomaly_states['TitresimZ'] = is_anomaly
                
                # Serit gerginliği
                if 'serit_gerginligi_bar' in data:
                    value = data.get('serit_gerginligi_bar', 0.0)
                    self.detectors['serit_gerginligi'].add_data_point(value, is_cutting)
                    is_anomaly = self.detectors['serit_gerginligi'].detect()
                    results['SeritGerginligi'] = is_anomaly
                    self.anomaly_states['SeritGerginligi'] = is_anomaly
                
                # Callback'i çağır (lock dışında)
                if self._update_callback:
                    for key, is_anomaly in results.items():
                        try:
                            self._update_callback(key, is_anomaly)
                        except Exception as e:
                            logger.error(f"Anomaly callback hatası ({key}): {e}")
                
                return results
                
        except Exception as e:
            logger.error(f"AnomalyManager process_data hatası: {e}")
            return {}
    
    def get_anomaly_states(self) -> Dict[str, bool]:
        """
        Mevcut anomali durumlarını döndürür (thread-safe)
        
        Returns:
            Anomali durumları dictionary'si
        """
        with self._lock:
            return dict(self.anomaly_states)
    
    def reset_anomaly_states(self) -> None:
        """Tüm anomali durumlarını sıfırlar (thread-safe)"""
        with self._lock:
            for key in self.anomaly_states:
                self.anomaly_states[key] = False
            
            # Detector buffer'larını da temizle
            for detector in self.detectors.values():
                detector.clear_buffer()
        
        logger.info("AnomalyManager: Tüm anomali durumları sıfırlandı")
    
    def get_detector(self, sensor_name: str):
        """
        Belirli bir detector'ı döndürür
        
        Args:
            sensor_name: Detector adı ('serit_sapmasi', 'serit_motor_akim', vb.)
            
        Returns:
            Detector instance veya None
        """
        return self.detectors.get(sensor_name)
    
    def set_detection_method(self, sensor_name: str, method) -> None:
        """
        Belirli bir detector'ın yöntemini değiştirir
        
        Args:
            sensor_name: Detector adı
            method: DetectionMethod enum değeri
        """
        detector = self.detectors.get(sensor_name)
        if detector:
            detector.set_method(method)
            logger.info(f"{sensor_name} detection yöntemi değiştirildi: {method.value}")
        else:
            logger.warning(f"Detector bulunamadı: {sensor_name}")

