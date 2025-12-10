"""
Titresim Y Anomaly Detector
IQR yöntemi ile anomali tespiti yapar
"""

from .base import BaseAnomalyDetector, DetectionMethod
import logging

logger = logging.getLogger(__name__)


class TitresimYDetector(BaseAnomalyDetector):
    """
    Titresim Y (ivme_olcer_y_hz) için anomali detector
    IQR yöntemi kullanır
    """
    
    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="titresim_y",
            data_key="ivme_olcer_y_hz",
            method=DetectionMethod.IQR,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("TitresimYDetector başlatıldı (IQR yöntemi)")

