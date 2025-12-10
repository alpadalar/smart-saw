"""
Base Anomaly Detector Sınıfı
Tüm anomaly detector'lar için temel sınıf ve detection yöntemleri
"""

import threading
import numpy as np
from typing import Optional, List, Callable, Dict, Any
from enum import Enum
from collections import deque
import logging

try:
    from sklearn.cluster import DBSCAN
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class DetectionMethod(Enum):
    """Anomali tespit yöntemleri"""
    IQR = "iqr"
    Z_SCORE = "z_score"
    DBSCAN = "dbscan"


class BaseAnomalyDetector:
    """
    Tüm anomaly detector'lar için temel sınıf
    Thread-safe veri buffer'ı ve detection yöntemleri sağlar
    """
    
    def __init__(
        self,
        sensor_name: str,
        data_key: str,
        method: DetectionMethod = DetectionMethod.IQR,
        buffer_size: int = 100,
        min_samples: int = 10
    ):
        """
        Args:
            sensor_name: Sensör adı (örn: 'serit_sapmasi')
            data_key: Veri dictionary'sindeki anahtar (örn: 'serit_sapmasi')
            method: Detection yöntemi (IQR, Z_SCORE, DBSCAN)
            buffer_size: Veri buffer boyutu
            min_samples: Detection için minimum örnek sayısı
        """
        self.sensor_name = sensor_name
        self.data_key = data_key
        self.method = method
        self.buffer_size = buffer_size
        self.min_samples = min_samples
        
        # Thread-safe veri buffer'ı
        self._buffer = deque(maxlen=buffer_size)
        self._lock = threading.Lock()
        
        # Anomali durumu
        self._is_anomaly = False
        self._last_value: Optional[float] = None
        
        # Detection yöntem fonksiyonları
        self._detection_methods = {
            DetectionMethod.IQR: self._detect_iqr,
            DetectionMethod.Z_SCORE: self._detect_z_score,
            DetectionMethod.DBSCAN: self._detect_dbscan,
        }
    
    def add_data_point(self, value: float, is_cutting: bool = False) -> None:
        """
        Yeni veri noktası ekler (thread-safe)
        
        Args:
            value: Sensör değeri
            is_cutting: Kesim yapılıyor mu?
        """
        try:
            with self._lock:
                self._buffer.append({
                    'value': float(value),
                    'is_cutting': is_cutting,
                    'timestamp': None  # İhtiyaç olursa eklenebilir
                })
                self._last_value = float(value)
        except Exception as e:
            logger.error(f"{self.sensor_name} veri ekleme hatası: {e}")
    
    def detect(self) -> bool:
        """
        Anomali tespiti yapar (thread-safe)
        
        Returns:
            True if anomaly detected, False otherwise
        """
        try:
            with self._lock:
                if len(self._buffer) < self.min_samples:
                    return False
                
                # Buffer'dan değerleri al
                values = [item['value'] for item in self._buffer]
                
                if not values:
                    return False
                
                # Seçili yöntemle detection yap
                detection_func = self._detection_methods.get(self.method)
                if not detection_func:
                    logger.warning(f"{self.sensor_name}: Bilinmeyen detection yöntemi: {self.method}")
                    return False
                
                is_anomaly = detection_func(values)
                self._is_anomaly = is_anomaly
                return is_anomaly
                
        except Exception as e:
            logger.error(f"{self.sensor_name} detection hatası: {e}")
            return False
    
    def _detect_iqr(self, values: List[float]) -> bool:
        """
        IQR (Interquartile Range) yöntemi ile anomali tespiti
        
        Args:
            values: Veri listesi
            
        Returns:
            True if anomaly detected
        """
        try:
            if len(values) < 4:
                return False
            
            values_array = np.array(values)
            q1 = np.percentile(values_array, 25)
            q3 = np.percentile(values_array, 75)
            iqr = q3 - q1
            
            if iqr == 0:
                # IQR sıfırsa, standart sapma kullan
                std = np.std(values_array)
                mean = np.mean(values_array)
                if std == 0:
                    return False
                # Son değer ortalamadan 3 standart sapma dışındaysa anomali
                last_value = values[-1]
                return abs(last_value - mean) > 3 * std
            
            # IQR yöntemi: Q1 - 1.5*IQR ve Q3 + 1.5*IQR dışındaki değerler anomali
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            last_value = values[-1]
            
            return last_value < lower_bound or last_value > upper_bound
            
        except Exception as e:
            logger.error(f"{self.sensor_name} IQR detection hatası: {e}")
            return False
    
    def _detect_z_score(self, values: List[float]) -> bool:
        """
        Z-score yöntemi ile anomali tespiti
        
        Args:
            values: Veri listesi
            
        Returns:
            True if anomaly detected
        """
        try:
            if len(values) < 3:
                return False
            
            values_array = np.array(values)
            mean = np.mean(values_array)
            std = np.std(values_array)
            
            if std == 0:
                return False
            
            # Son değerin z-score'unu hesapla
            last_value = values[-1]
            z_score = abs((last_value - mean) / std)
            
            # Z-score > 3 ise anomali (3 sigma kuralı)
            return z_score > 3.0
            
        except Exception as e:
            logger.error(f"{self.sensor_name} Z-score detection hatası: {e}")
            return False
    
    def _detect_dbscan(self, values: List[float]) -> bool:
        """
        DBSCAN yöntemi ile anomali tespiti
        
        DBSCAN (Density-Based Spatial Clustering of Applications with Noise):
        - Yoğunluk tabanlı bir kümeleme algoritmasıdır
        - Veri noktalarını yoğun bölgeler (clusters) ve gürültü (noise/outliers) olarak ayırır
        - Noise olarak işaretlenen noktalar anomali olarak kabul edilir
        
        Args:
            values: Veri listesi
            
        Returns:
            True if anomaly detected (son değer noise olarak işaretlenirse)
        """
        try:
            if len(values) < 5:
                return False
            
            if not SKLEARN_AVAILABLE:
                # sklearn yoksa fallback: basit z-score yaklaşımı
                logger.warning(f"{self.sensor_name}: sklearn bulunamadı, DBSCAN için fallback yöntem kullanılıyor")
                values_array = np.array(values[:-1])
                last_value = values[-1]
                mean_value = np.mean(values_array)
                std_value = np.std(values_array)
                if std_value == 0:
                    return mean_value != last_value
                z_score = abs((last_value - mean_value) / (std_value + 1e-10))
                return z_score > 2.5
            
            # sklearn DBSCAN kullan
            # Verileri 2D array'e çevir (DBSCAN için gerekli)
            # Zaman serisi için: her değeri [index, value] şeklinde temsil ediyoruz
            values_array = np.array(values).reshape(-1, 1)
            
            # DBSCAN parametreleri:
            # eps: İki nokta arasındaki maksimum mesafe (komşu olarak kabul edilir)
            # min_samples: Bir cluster için minimum nokta sayısı
            # Bu parametreler veri dağılımına göre ayarlanmalı
            
            # Dinamik eps hesaplama: verilerin standart sapmasının bir katı
            std_value = np.std(values)
            eps = max(std_value * 0.5, np.ptp(values) * 0.1)  # ptp = peak-to-peak (max-min)
            
            # min_samples: buffer boyutunun %10'u, minimum 2
            min_samples = max(2, int(len(values) * 0.1))
            
            # DBSCAN uygula
            dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean')
            labels = dbscan.fit_predict(values_array)
            
            # Son değerin label'ını kontrol et
            # -1 label'ı noise/outlier/anomali anlamına gelir
            last_label = labels[-1]
            
            is_anomaly = last_label == -1
            
            if is_anomaly:
                logger.debug(f"{self.sensor_name}: DBSCAN anomali tespit edildi (label: {last_label}, eps: {eps:.3f})")
            
            return is_anomaly
            
        except Exception as e:
            logger.error(f"{self.sensor_name} DBSCAN detection hatası: {e}")
            # Hata durumunda fallback
            try:
                values_array = np.array(values)
                mean_value = np.mean(values_array)
                std_value = np.std(values_array)
                if std_value == 0:
                    return False
                last_value = values[-1]
                z_score = abs((last_value - mean_value) / std_value)
                return z_score > 3.0
            except:
                return False
    
    def get_last_value(self) -> Optional[float]:
        """Son değeri döndürür (thread-safe)"""
        with self._lock:
            return self._last_value
    
    def is_anomaly(self) -> bool:
        """Anomali durumunu döndürür (thread-safe)"""
        with self._lock:
            return self._is_anomaly
    
    def set_method(self, method: DetectionMethod) -> None:
        """Detection yöntemini değiştirir"""
        self.method = method
        logger.info(f"{self.sensor_name} detection yöntemi değiştirildi: {method.value}")
    
    def clear_buffer(self) -> None:
        """Buffer'ı temizler (thread-safe)"""
        with self._lock:
            self._buffer.clear()
            self._is_anomaly = False
    
    def get_buffer_size(self) -> int:
        """Mevcut buffer boyutunu döndürür (thread-safe)"""
        with self._lock:
            return len(self._buffer)

