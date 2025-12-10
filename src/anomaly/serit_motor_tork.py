"""
Serit Motor Tork Anomaly Detector
DBSCAN yöntemi ile anomali tespiti yapar
"""

from .base import BaseAnomalyDetector, DetectionMethod
import logging

logger = logging.getLogger(__name__)


class SeritMotorTorkDetector(BaseAnomalyDetector):
    """
    Serit motor torku için anomali detector
    DBSCAN yöntemi kullanır
    """
    
    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="serit_motor_tork",
            data_key="serit_motor_tork_percentage",
            method=DetectionMethod.DBSCAN,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("SeritMotorTorkDetector başlatıldı (DBSCAN yöntemi)")

