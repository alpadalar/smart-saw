# src/anomaly/serit_motor_akim.py
"""
Şerit motor akım anomaly detector'ı
"""

import logging
from typing import Dict, Any, Optional
from .base_detector import BaseAnomalyDetector

logger = logging.getLogger(__name__)


class SeritMotorAkimDetector(BaseAnomalyDetector):
    """
    Şerit motor akım anomalilerini tespit eden detector
    """
    
    def __init__(self, 
                 window_size: int = 20,
                 threshold_multiplier: float = 1.5,  # IQR için çarpan
                 min_samples: int = 10,
                 update_callback: Optional[callable] = None):
        """
        Args:
            window_size: Anomali tespiti için kullanılacak pencere boyutu
            threshold_multiplier: IQR çarpanı (çeyrekler açıklığı * çarpan)
            min_samples: Anomali tespiti için minimum örnek sayısı
            update_callback: Anomali tespit edildiğinde çağrılacak callback
        """
        super().__init__(
            window_size=window_size,
            threshold_multiplier=threshold_multiplier,
            min_samples=min_samples,
            detection_method="iqr",  # Motor akım için IQR
            update_callback=update_callback
        )
        
        logger.info("SeritMotorAkimDetector başlatıldı")
    
    def _extract_value(self, data: Dict[str, Any]) -> Optional[float]:
        """
        Ham veriden motor akım değerini çıkarır
        
        Args:
            data: Ham sensör verisi
            
        Returns:
            float: Motor akım değeri, None ise veri geçersiz
        """
        try:
            # Sadece serit_motor_akim_a niteliğini kullan
            if 'serit_motor_akim_a' in data and data['serit_motor_akim_a'] is not None:
                value = float(data['serit_motor_akim_a'])
                # Geçerli aralık kontrolü (örnek: 0 ile 100 arası)
                if 0 <= value <= 100:
                    return value
                
            return None
            
        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"Motor akım değeri çıkarılamadı: {e}")
            return None
    
    def _get_anomaly_type(self) -> str:
        """Anomali tipini döndürür"""
        return "serit_motor_akim"
    
    def _check_anomaly(self, value: float) -> bool:
        """
        Motor akım için özel anomali kontrolü
        
        Args:
            value: Kontrol edilecek motor akım değeri
            
        Returns:
            bool: Anomali mi?
        """
        # Temel anomali kontrolü
        if not super()._check_anomaly(value):
            return False
        
        # Motor akım için ek kontroller
        # Eğer akım çok yüksekse anomali
        if value > 50:
            return True
        
        # Eğer akım çok düşükse ama motor çalışıyorsa anomali
        if value < 1:
            return True
        
        # Normal anomali kontrolü
        return True
