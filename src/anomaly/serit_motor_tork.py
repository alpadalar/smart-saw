# src/anomaly/serit_motor_tork.py
"""
Şerit motor tork anomaly detector'ı
"""

import logging
from typing import Dict, Any, Optional
from .base_detector import BaseAnomalyDetector

logger = logging.getLogger(__name__)


class SeritMotorTorkDetector(BaseAnomalyDetector):
    """
    Şerit motor tork anomalilerini tespit eden detector
    """
    
    def __init__(self, 
                 window_size: int = 50,
                 threshold_multiplier: float = 0.5,  # DBSCAN için eps değeri
                 min_samples: int = 15,
                 update_callback: Optional[callable] = None):
        """
        Args:
            window_size: Anomali tespiti için kullanılacak pencere boyutu
            threshold_multiplier: DBSCAN eps değeri (cluster mesafesi)
            min_samples: Anomali tespiti için minimum örnek sayısı
            update_callback: Anomali tespit edildiğinde çağrılacak callback
        """
        super().__init__(
            window_size=window_size,
            threshold_multiplier=threshold_multiplier,
            min_samples=min_samples,
            detection_method="dbscan",  # Motor tork için DBSCAN
            update_callback=update_callback
        )
        
        logger.info("SeritMotorTorkDetector başlatıldı")
    
    def _extract_value(self, data: Dict[str, Any]) -> Optional[float]:
        """
        Ham veriden motor tork değerini çıkarır
        
        Args:
            data: Ham sensör verisi
            
        Returns:
            float: Motor tork değeri, None ise veri geçersiz
        """
        try:
            # Sadece serit_motor_tork_percentage niteliğini kullan
            if 'serit_motor_tork_percentage' in data and data['serit_motor_tork_percentage'] is not None:
                value = float(data['serit_motor_tork_percentage'])
                # Geçerli aralık kontrolü (örnek: 0 ile 100 arası)
                if 0 <= value <= 100:
                    return value
                
            return None
            
        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"Motor tork değeri çıkarılamadı: {e}")
            return None
    
    def _get_anomaly_type(self) -> str:
        """Anomali tipini döndürür"""
        return "serit_motor_tork"
    
    def _check_anomaly(self, value: float) -> bool:
        """
        Motor tork için özel anomali kontrolü
        
        Args:
            value: Kontrol edilecek motor tork değeri
            
        Returns:
            bool: Anomali mi?
        """
        # Temel anomali kontrolü
        if not super()._check_anomaly(value):
            return False
        
        # Motor tork için ek kontroller
        # Eğer tork çok yüksekse anomali
        if value > 200:
            return True
        
        # Eğer tork çok düşükse ama motor çalışıyorsa anomali
        if value < 1:
            return True
        
        # Normal anomali kontrolü
        return True
