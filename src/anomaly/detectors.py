"""
Specialized Anomaly Detectors

Each sensor has a dedicated detector with optimized detection method.
"""

from .base import BaseAnomalyDetector, DetectionMethod
import logging

logger = logging.getLogger(__name__)


class SeritSapmasiDetector(BaseAnomalyDetector):
    """Band deviation anomaly detector - Uses IQR method (robust to outliers)"""

    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="serit_sapmasi",
            data_key="serit_sapmasi",
            method=DetectionMethod.IQR,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("SeritSapmasiDetector initialized (IQR method)")


class SeritMotorAkimDetector(BaseAnomalyDetector):
    """Band motor current anomaly detector - Uses Z-Score method (fast)"""

    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="serit_motor_akim",
            data_key="serit_motor_akim_a",
            method=DetectionMethod.Z_SCORE,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("SeritMotorAkimDetector initialized (Z-Score method)")


class SeritMotorTorkDetector(BaseAnomalyDetector):
    """Band motor torque anomaly detector - Uses Z-Score method"""

    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="serit_motor_tork",
            data_key="serit_motor_tork_percentage",
            method=DetectionMethod.Z_SCORE,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("SeritMotorTorkDetector initialized (Z-Score method)")


class SeritKesmeHiziDetector(BaseAnomalyDetector):
    """Cutting speed anomaly detector - Uses IQR method"""

    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="serit_kesme_hizi",
            data_key="serit_kesme_hizi",
            method=DetectionMethod.IQR,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("SeritKesmeHiziDetector initialized (IQR method)")


class SeritInmeHiziDetector(BaseAnomalyDetector):
    """Feed rate anomaly detector - Uses IQR method"""

    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="serit_inme_hizi",
            data_key="serit_inme_hizi",
            method=DetectionMethod.IQR,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("SeritInmeHiziDetector initialized (IQR method)")


class TitresimXDetector(BaseAnomalyDetector):
    """Vibration X anomaly detector - Uses DBSCAN method (advanced)"""

    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="titresim_x",
            data_key="ivme_olcer_x_hz",
            method=DetectionMethod.DBSCAN,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("TitresimXDetector initialized (DBSCAN method)")


class TitresimYDetector(BaseAnomalyDetector):
    """Vibration Y anomaly detector - Uses DBSCAN method (advanced)"""

    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="titresim_y",
            data_key="ivme_olcer_y_hz",
            method=DetectionMethod.DBSCAN,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("TitresimYDetector initialized (DBSCAN method)")


class TitresimZDetector(BaseAnomalyDetector):
    """Vibration Z anomaly detector - Uses DBSCAN method (advanced)"""

    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="titresim_z",
            data_key="ivme_olcer_z_hz",
            method=DetectionMethod.DBSCAN,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("TitresimZDetector initialized (DBSCAN method)")


class SeritGerginligiDetector(BaseAnomalyDetector):
    """Band tension anomaly detector - Uses IQR method"""

    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        super().__init__(
            sensor_name="serit_gerginligi",
            data_key="serit_gerginligi_bar",
            method=DetectionMethod.IQR,
            buffer_size=buffer_size,
            min_samples=min_samples
        )
        logger.info("SeritGerginligiDetector initialized (IQR method)")
