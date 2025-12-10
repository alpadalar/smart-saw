"""
Serit Kesme Hizi Anomaly Detector
IQR yöntemi ile anomali tespiti yapar
"""

from .base import BaseAnomalyDetector, DetectionMethod
import logging

logger = logging.getLogger(__name__)


class SeritKesmeHiziDetector(BaseAnomalyDetector):
    """
    Serit kesme hızı için anomali detector
    IQR yöntemi kullanır
    """
    
    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="serit_kesme_hizi",
            data_key="serit_kesme_hizi",
            method=DetectionMethod.IQR,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("SeritKesmeHiziDetector başlatıldı (IQR yöntemi)")

