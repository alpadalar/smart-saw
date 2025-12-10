"""
Titresim X Anomaly Detector
IQR yöntemi ile anomali tespiti yapar
"""

from .base import BaseAnomalyDetector, DetectionMethod
import logging

logger = logging.getLogger(__name__)


class TitresimXDetector(BaseAnomalyDetector):
    """
    Titresim X (ivme_olcer_x_hz) için anomali detector
    IQR yöntemi kullanır
    """
    
    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="titresim_x",
            data_key="ivme_olcer_x_hz",
            method=DetectionMethod.IQR,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("TitresimXDetector başlatıldı (IQR yöntemi)")

