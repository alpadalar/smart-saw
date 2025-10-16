# src/anomaly/base_detector.py
"""
Base anomaly detector sınıfı - tüm anomaly detector'lar için ortak yapı
"""

import threading
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from collections import deque
import numpy as np
from sklearn.cluster import DBSCAN

logger = logging.getLogger(__name__)


class BaseAnomalyDetector(ABC):
    """
    Tüm anomaly detector'lar için base sınıf
    Thread-safe yapıda tasarlanmıştır
    """
    
    def __init__(self, 
                 window_size: int = 100,
                 threshold_multiplier: float = 2.0,
                 min_samples: int = 10,
                 detection_method: str = "z_score",
                 update_callback: Optional[Callable[[str, Dict], None]] = None):
        """
        Args:
            window_size: Anomali tespiti için kullanılacak pencere boyutu
            threshold_multiplier: Anomali eşik çarpanı (standart sapma * çarpan)
            min_samples: Anomali tespiti için minimum örnek sayısı
            detection_method: Anomali tespit yöntemi ("z_score", "dbscan", "iqr")
            update_callback: Anomali tespit edildiğinde çağrılacak callback
        """
        self.window_size = window_size
        self.threshold_multiplier = threshold_multiplier
        self.min_samples = min_samples
        self.detection_method = detection_method
        self.update_callback = update_callback
        
        # Thread-safe veri yapıları
        self._data_buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        
        # İstatistikler
        self._stats = {
            'total_samples': 0,
            'anomalies_detected': 0,
            'last_anomaly_time': None,
            'current_mean': 0.0,
            'current_std': 0.0,
            'current_threshold': 0.0
        }
        
        # Durum bilgileri
        self._is_active = False
        self._last_update_time = 0.0
        
    @abstractmethod
    def _extract_value(self, data: Dict[str, Any]) -> Optional[float]:
        """
        Ham veriden anomaly tespiti için kullanılacak değeri çıkarır
        Her detector kendi implementasyonunu yapar
        
        Args:
            data: Ham sensör verisi
            
        Returns:
            float: Tespit edilecek değer, None ise veri geçersiz
        """
        pass
    
    @abstractmethod
    def _get_anomaly_type(self) -> str:
        """
        Anomali tipini döndürür
        
        Returns:
            str: Anomali tipi (örn: "serit_sapmasi", "motor_tork")
        """
        pass
    
    def add_data(self, data: Dict[str, Any]) -> bool:
        """
        Yeni veri ekler ve anomali kontrolü yapar (thread-safe)
        
        Args:
            data: Ham sensör verisi
            
        Returns:
            bool: Anomali tespit edildi mi?
        """
        try:
            value = self._extract_value(data)
            if value is None:
                return False
                
            with self._lock:
                self._data_buffer.append(value)
                self._stats['total_samples'] += 1
                self._last_update_time = time.time()
                
                # Yeterli veri yoksa anomali kontrolü yapma
                if len(self._data_buffer) < self.min_samples:
                    return False
                
                # İstatistikleri güncelle
                self._update_statistics()
                
                # Anomali kontrolü
                is_anomaly = self._check_anomaly(value)
                
                if is_anomaly:
                    self._handle_anomaly(value, data)
                    
                return is_anomaly
                
        except Exception as e:
            logger.error(f"Anomaly detector veri ekleme hatası: {e}")
            return False
    
    def _update_statistics(self):
        """İstatistikleri günceller"""
        if len(self._data_buffer) < 2:
            return
            
        data_array = np.array(list(self._data_buffer))
        self._stats['current_mean'] = float(np.mean(data_array))
        self._stats['current_std'] = float(np.std(data_array))
        self._stats['current_threshold'] = self._stats['current_std'] * self.threshold_multiplier
    
    def _check_anomaly(self, value: float) -> bool:
        """
        Verilen değerin anomali olup olmadığını kontrol eder
        
        Args:
            value: Kontrol edilecek değer
            
        Returns:
            bool: Anomali mi?
        """
        if len(self._data_buffer) < self.min_samples:
            return False
            
        if self.detection_method == "z_score":
            return self._check_z_score_anomaly(value)
        elif self.detection_method == "dbscan":
            return self._check_dbscan_anomaly(value)
        elif self.detection_method == "iqr":
            return self._check_iqr_anomaly(value)
        else:
            logger.warning(f"Bilinmeyen detection method: {self.detection_method}")
            return self._check_z_score_anomaly(value)
    
    def _check_z_score_anomaly(self, value: float) -> bool:
        """Z-score tabanlı anomali tespiti"""
        if self._stats['current_std'] == 0:
            return False
            
        z_score = abs(value - self._stats['current_mean']) / self._stats['current_std']
        return z_score > self.threshold_multiplier
    
    def _check_dbscan_anomaly(self, value: float) -> bool:
        """DBSCAN tabanlı anomali tespiti"""
        try:
            if len(self._data_buffer) < 10:  # DBSCAN için minimum örnek
                return False
                
            # Mevcut veriyi numpy array'e çevir
            data_array = np.array(list(self._data_buffer)).reshape(-1, 1)
            
            # DBSCAN uygula
            dbscan = DBSCAN(eps=self.threshold_multiplier, min_samples=3)
            clusters = dbscan.fit_predict(data_array)
            
            # Yeni değerin cluster'ını kontrol et
            new_value_array = np.array([[value]])
            new_cluster = dbscan.fit_predict(np.vstack([data_array, new_value_array]))[-1]
            
            # -1 cluster'ı outlier/anomali demektir
            return new_cluster == -1
            
        except Exception as e:
            logger.error(f"DBSCAN anomali tespiti hatası: {e}")
            return False
    
    def _check_iqr_anomaly(self, value: float) -> bool:
        """Interquartile Range (IQR) tabanlı anomali tespiti"""
        try:
            if len(self._data_buffer) < 4:  # IQR için minimum örnek
                return False
                
            data_array = np.array(list(self._data_buffer))
            
            # Q1, Q3 ve IQR hesapla
            q1 = np.percentile(data_array, 25)
            q3 = np.percentile(data_array, 75)
            iqr = q3 - q1
            
            # Alt ve üst sınırları hesapla
            lower_bound = q1 - (self.threshold_multiplier * iqr)
            upper_bound = q3 + (self.threshold_multiplier * iqr)
            
            # Değer sınırlar dışında mı kontrol et
            return value < lower_bound or value > upper_bound
            
        except Exception as e:
            logger.error(f"IQR anomali tespiti hatası: {e}")
            return False
    
    def _handle_anomaly(self, value: float, original_data: Dict[str, Any]):
        """
        Anomali tespit edildiğinde çağrılır
        
        Args:
            value: Anomali değeri
            original_data: Orijinal ham veri
        """
        self._stats['anomalies_detected'] += 1
        self._stats['last_anomaly_time'] = time.time()
        
        # Anomali bilgilerini hazırla
        anomaly_info = {
            'type': self._get_anomaly_type(),
            'value': value,
            'timestamp': time.time(),
            'mean': self._stats['current_mean'],
            'std': self._stats['current_std'],
            'threshold': self._stats['current_threshold'],
            'z_score': abs(value - self._stats['current_mean']) / self._stats['current_std'],
            'original_data': original_data.copy()
        }
        
        logger.warning(f"Anomali tespit edildi: {self._get_anomaly_type()} = {value:.3f} "
                      f"(mean: {self._stats['current_mean']:.3f}, "
                      f"std: {self._stats['current_std']:.3f})")
        
        # Callback çağır
        if self.update_callback:
            try:
                self.update_callback(self._get_anomaly_type(), anomaly_info)
            except Exception as e:
                logger.error(f"Anomaly callback hatası: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Mevcut istatistikleri döndürür (thread-safe)
        
        Returns:
            Dict: İstatistik bilgileri
        """
        with self._lock:
            return self._stats.copy()
    
    def reset_stats(self):
        """İstatistikleri sıfırlar (thread-safe)"""
        with self._lock:
            self._stats = {
                'total_samples': 0,
                'anomalies_detected': 0,
                'last_anomaly_time': None,
                'current_mean': 0.0,
                'current_std': 0.0,
                'current_threshold': 0.0
            }
            self._data_buffer.clear()
    
    def is_active(self) -> bool:
        """Detector aktif mi?"""
        return self._is_active
    
    def set_active(self, active: bool):
        """Detector durumunu ayarlar"""
        self._is_active = active
