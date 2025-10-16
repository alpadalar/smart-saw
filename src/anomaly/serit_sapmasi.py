# src/anomaly/serit_sapmasi.py
"""
Şerit sapması anomaly detector'ı
"""

import logging
from typing import Dict, Any, Optional
from .base_detector import BaseAnomalyDetector

logger = logging.getLogger(__name__)


class SeritSapmasiDetector(BaseAnomalyDetector):
    """
    Şerit sapması anomalilerini tespit eden detector
    """
    
    def __init__(self, 
                 window_size: int = 50,
                 threshold_multiplier: float = 2.5,
                 min_samples: int = 10,
                 update_callback: Optional[callable] = None):
        """
        Args:
            window_size: Anomali tespiti için kullanılacak pencere boyutu
            threshold_multiplier: Anomali eşik çarpanı (şerit sapması için daha hassas)
            min_samples: Anomali tespiti için minimum örnek sayısı
            update_callback: Anomali tespit edildiğinde çağrılacak callback
        """
        super().__init__(
            window_size=window_size,
            threshold_multiplier=threshold_multiplier,
            min_samples=min_samples,
            detection_method="z_score",  # Şerit sapması için Z-score
            update_callback=update_callback
        )
        
        logger.info("SeritSapmasiDetector başlatıldı")
    
    def _extract_value(self, data: Dict[str, Any]) -> Optional[float]:
        """
        Ham veriden şerit sapması değerini çıkarır
        
        Args:
            data: Ham sensör verisi
            
        Returns:
            float: Şerit sapması değeri, None ise veri geçersiz
        """
        try:
            # Sadece serit_sapmasi niteliğini kullan
            if 'serit_sapmasi' in data and data['serit_sapmasi'] is not None:
                value = float(data['serit_sapmasi'])
                # Geçerli aralık kontrolü (örnek: -100 ile +100 arası)
                if -1000 <= value <= 1000:
                    return value
                
            return None
            
        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"Şerit sapması değeri çıkarılamadı: {e}")
            return None
    
    def _get_anomaly_type(self) -> str:
        """Anomali tipini döndürür"""
        return "serit_sapmasi"
    
    def _check_anomaly(self, value: float) -> bool:
        """
        Şerit sapması için özel anomali kontrolü
        
        Args:
            value: Kontrol edilecek şerit sapması değeri
            
        Returns:
            bool: Anomali mi?
        """
        # Temel anomali kontrolü
        if not super()._check_anomaly(value):
            return False
        
        # Şerit sapması için ek kontroller
        # Eğer sapma çok büyükse anomali
        if abs(value) > 1:
            return True
        
        # Normal anomali kontrolü
        return True
