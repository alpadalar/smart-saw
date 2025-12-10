"""
Serit Motor Akim Anomaly Detector
Z-score yöntemi ile anomali tespiti yapar
"""

from .base import BaseAnomalyDetector, DetectionMethod
import logging

logger = logging.getLogger(__name__)


class SeritMotorAkimDetector(BaseAnomalyDetector):
    """
    Serit motor akımı için anomali detector
    Z-score yöntemi kullanır
    """
    
    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="serit_motor_akim",
            data_key="serit_motor_akim_a",
            method=DetectionMethod.Z_SCORE,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("SeritMotorAkimDetector başlatıldı (Z-score yöntemi)")

