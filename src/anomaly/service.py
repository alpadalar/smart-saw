# src/anomaly/service.py
"""
Thread-safe Anomaly Detection Service
Mevcut sistem mimarisine uyumlu anomaly detection servisi
"""

import threading
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from .base_detector import BaseAnomalyDetector
from .serit_sapmasi import SeritSapmasiDetector
from .serit_motor_tork import SeritMotorTorkDetector
from .serit_motor_akim import SeritMotorAkimDetector

logger = logging.getLogger(__name__)


class AnomalyService:
    """
    Thread-safe anomaly detection service
    Mevcut Smart Saw sistem mimarisine uyumlu
    """
    
    def __init__(self, 
                 update_callback: Optional[Callable[[str, Dict], None]] = None,
                 processing_interval: float = 0.1):
        """
        Args:
            update_callback: Anomali tespit edildiğinde çağrılacak callback
            processing_interval: Veri işleme aralığı (saniye)
        """
        self.update_callback = update_callback
        self.processing_interval = processing_interval
        
        # Thread-safe state management
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._is_running = False
        
        # Anomaly detectors
        self._detectors: Dict[str, BaseAnomalyDetector] = {}
        self._detector_lock = threading.Lock()
        
        # Data queue for thread-safe processing
        self._data_queue = []
        self._queue_lock = threading.Lock()
        
        # Processing thread
        self._processing_thread: Optional[threading.Thread] = None
        
        # Statistics
        self._stats = {
            'total_processed': 0,
            'anomalies_detected': 0,
            'last_anomaly_time': None,
            'active_detectors': 0,
            'start_time': None
        }
        
        # Initialize detectors
        self._initialize_detectors()
        
        logger.info("AnomalyService başlatıldı")
    
    def _initialize_detectors(self):
        """Anomaly detector'ları başlatır"""
        try:
            with self._detector_lock:
                # Şerit sapması detector
                self._detectors['serit_sapmasi'] = SeritSapmasiDetector(
                    window_size=50,
                    threshold_multiplier=2.5,
                    min_samples=10,
                    update_callback=self._on_anomaly_detected
                )
                
                # Motor tork detector
                self._detectors['serit_motor_tork'] = SeritMotorTorkDetector(
                    window_size=100,
                    threshold_multiplier=2.0,
                    min_samples=15,
                    update_callback=self._on_anomaly_detected
                )
                
                # Motor akım detector
                self._detectors['serit_motor_akim'] = SeritMotorAkimDetector(
                    window_size=80,
                    threshold_multiplier=2.2,
                    min_samples=12,
                    update_callback=self._on_anomaly_detected
                )
                
                logger.info(f"{len(self._detectors)} anomaly detector başlatıldı")
                
        except Exception as e:
            logger.error(f"Detector başlatma hatası: {e}")
    
    def _on_anomaly_detected(self, anomaly_type: str, anomaly_info: Dict[str, Any]):
        """
        Anomali tespit edildiğinde çağrılır
        
        Args:
            anomaly_type: Anomali tipi
            anomaly_info: Anomali bilgileri
        """
        try:
            with self._lock:
                self._stats['anomalies_detected'] += 1
                self._stats['last_anomaly_time'] = time.time()
            
            logger.warning(f"Anomali tespit edildi: {anomaly_type} - {anomaly_info}")
            
            # External callback çağır
            if self.update_callback:
                try:
                    self.update_callback(anomaly_type, anomaly_info)
                except Exception as e:
                    logger.error(f"External callback hatası: {e}")
                    
        except Exception as e:
            logger.error(f"Anomali callback işleme hatası: {e}")
    
    def start(self):
        """Anomaly service'i başlatır (thread-safe)"""
        with self._lock:
            if self._is_running:
                logger.warning("AnomalyService zaten çalışıyor")
                return
            
            self._stop_event.clear()
            self._is_running = True
            self._stats['start_time'] = time.time()
            
            # Processing thread'i başlat
            self._processing_thread = threading.Thread(
                target=self._processing_loop, 
                daemon=True
            )
            self._processing_thread.start()
            
            logger.info("AnomalyService başlatıldı")
    
    def stop(self):
        """Anomaly service'i durdurur (thread-safe)"""
        with self._lock:
            if not self._is_running:
                logger.warning("AnomalyService zaten durmuş")
                return
            
            self._stop_event.set()
            self._is_running = False
            
            # Processing thread'i bekle
            if self._processing_thread and self._processing_thread.is_alive():
                self._processing_thread.join(timeout=2.0)
            
            logger.info("AnomalyService durduruldu")
    
    def _processing_loop(self):
        """Ana işleme döngüsü"""
        logger.info("Anomaly processing loop başlatıldı")
        
        while not self._stop_event.is_set():
            try:
                # Queue'dan veri al
                data_to_process = None
                with self._queue_lock:
                    if self._data_queue:
                        data_to_process = self._data_queue.pop(0)
                
                if data_to_process:
                    self._process_data(data_to_process)
                
                # Kısa bekleme
                time.sleep(self.processing_interval)
                
            except Exception as e:
                logger.error(f"Processing loop hatası: {e}")
                time.sleep(0.1)
        
        logger.info("Anomaly processing loop sonlandırıldı")
    
    def _process_data(self, data: Dict[str, Any]):
        """
        Veriyi tüm detector'lara gönderir
        
        Args:
            data: İşlenecek veri
        """
        try:
            with self._detector_lock:
                for detector_name, detector in self._detectors.items():
                    if detector.is_active():
                        try:
                            detector.add_data(data)
                        except Exception as e:
                            logger.error(f"Detector {detector_name} işleme hatası: {e}")
            
            with self._lock:
                self._stats['total_processed'] += 1
                
        except Exception as e:
            logger.error(f"Veri işleme hatası: {e}")
    
    def add_data(self, data: Dict[str, Any]):
        """
        Yeni veri ekler (thread-safe)
        
        Args:
            data: Ham sensör verisi
        """
        try:
            with self._queue_lock:
                # Queue boyutunu sınırla (memory koruması)
                if len(self._data_queue) < 1000:
                    self._data_queue.append(data.copy())
                else:
                    logger.warning("Anomaly data queue dolu, veri atlanıyor")
                    
        except Exception as e:
            logger.error(f"Veri ekleme hatası: {e}")
    
    def set_detector_active(self, detector_name: str, active: bool):
        """
        Detector'ı aktif/pasif yapar (thread-safe)
        
        Args:
            detector_name: Detector adı
            active: Aktif mi?
        """
        try:
            with self._detector_lock:
                if detector_name in self._detectors:
                    self._detectors[detector_name].set_active(active)
                    logger.info(f"Detector {detector_name} {'aktif' if active else 'pasif'} yapıldı")
                else:
                    logger.warning(f"Detector {detector_name} bulunamadı")
                    
        except Exception as e:
            logger.error(f"Detector durum ayarlama hatası: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        İstatistikleri döndürür (thread-safe)
        
        Returns:
            Dict: İstatistik bilgileri
        """
        try:
            with self._lock:
                stats = self._stats.copy()
            
            with self._detector_lock:
                detector_stats = {}
                for name, detector in self._detectors.items():
                    detector_stats[name] = detector.get_stats()
                stats['detectors'] = detector_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"İstatistik alma hatası: {e}")
            return {}
    
    def reset_stats(self):
        """İstatistikleri sıfırlar (thread-safe)"""
        try:
            with self._lock:
                self._stats = {
                    'total_processed': 0,
                    'anomalies_detected': 0,
                    'last_anomaly_time': None,
                    'active_detectors': 0,
                    'start_time': time.time()
                }
            
            with self._detector_lock:
                for detector in self._detectors.values():
                    detector.reset_stats()
            
            logger.info("Anomaly service istatistikleri sıfırlandı")
            
        except Exception as e:
            logger.error(f"İstatistik sıfırlama hatası: {e}")
    
    def is_running(self) -> bool:
        """Service çalışıyor mu?"""
        with self._lock:
            return self._is_running
    
    def get_active_detectors(self) -> List[str]:
        """Aktif detector'ları döndürür"""
        try:
            with self._detector_lock:
                active = []
                for name, detector in self._detectors.items():
                    if detector.is_active():
                        active.append(name)
                return active
        except Exception as e:
            logger.error(f"Aktif detector alma hatası: {e}")
            return []
