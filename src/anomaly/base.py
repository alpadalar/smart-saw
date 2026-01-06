"""
Base Anomaly Detector Class

Provides base class for all anomaly detectors with multiple detection methods.
Thread-safe implementation with rolling window buffers.
"""

import threading
import numpy as np
from typing import Optional, List
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
    """Anomaly detection methods"""
    IQR = "iqr"
    Z_SCORE = "z_score"
    DBSCAN = "dbscan"


class BaseAnomalyDetector:
    """
    Base class for all anomaly detectors.

    Provides thread-safe data buffering and multiple detection methods.
    Each sensor can use a different detection method optimized for its characteristics.
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
        Initialize anomaly detector.

        Args:
            sensor_name: Sensor name (e.g., 'serit_sapmasi')
            data_key: Key in data dictionary (e.g., 'serit_sapmasi')
            method: Detection method (IQR, Z_SCORE, DBSCAN)
            buffer_size: Rolling window size
            min_samples: Minimum samples required for detection
        """
        self.sensor_name = sensor_name
        self.data_key = data_key
        self.method = method
        self.buffer_size = buffer_size
        self.min_samples = min_samples

        # Thread-safe data buffer
        self._buffer = deque(maxlen=buffer_size)
        self._lock = threading.Lock()

        # Anomaly state
        self._is_anomaly = False
        self._last_value: Optional[float] = None

        # Detection method functions
        self._detection_methods = {
            DetectionMethod.IQR: self._detect_iqr,
            DetectionMethod.Z_SCORE: self._detect_z_score,
            DetectionMethod.DBSCAN: self._detect_dbscan,
        }

        logger.debug(f"{sensor_name} detector initialized: method={method.value}, buffer={buffer_size}")

    def add_data_point(self, value: float, is_cutting: bool = False) -> None:
        """
        Add new data point (thread-safe).

        Args:
            value: Sensor value
            is_cutting: Whether cutting is active
        """
        try:
            with self._lock:
                self._buffer.append({
                    'value': float(value),
                    'is_cutting': is_cutting,
                    'timestamp': None  # Can be added if needed
                })
                self._last_value = float(value)
        except Exception as e:
            logger.error(f"{self.sensor_name} data add error: {e}")

    def detect(self) -> bool:
        """
        Perform anomaly detection (thread-safe).

        Returns:
            True if anomaly detected, False otherwise
        """
        try:
            with self._lock:
                if len(self._buffer) < self.min_samples:
                    return False

                # Extract values from buffer
                values = [item['value'] for item in self._buffer]

                if not values:
                    return False

                # Detect using selected method
                detection_func = self._detection_methods.get(self.method)
                if not detection_func:
                    logger.warning(f"{self.sensor_name}: Unknown detection method: {self.method}")
                    return False

                is_anomaly = detection_func(values)
                self._is_anomaly = is_anomaly
                return is_anomaly

        except Exception as e:
            logger.error(f"{self.sensor_name} detection error: {e}")
            return False

    def _detect_iqr(self, values: List[float]) -> bool:
        """
        IQR (Interquartile Range) anomaly detection.

        More robust to outliers than z-score.
        Anomalies are values outside Q1 - 1.5*IQR to Q3 + 1.5*IQR range.

        Args:
            values: Data list

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
                # If IQR is zero, use standard deviation
                std = np.std(values_array)
                mean = np.mean(values_array)
                if std == 0:
                    return False
                # Anomaly if last value is > 3 sigma from mean
                last_value = values[-1]
                return abs(last_value - mean) > 3 * std

            # IQR method: values outside Q1 - 1.5*IQR and Q3 + 1.5*IQR are anomalies
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            last_value = values[-1]

            return last_value < lower_bound or last_value > upper_bound

        except Exception as e:
            logger.error(f"{self.sensor_name} IQR detection error: {e}")
            return False

    def _detect_z_score(self, values: List[float]) -> bool:
        """
        Z-score anomaly detection.

        Fast statistical method using 3-sigma rule.
        Assumes normal distribution.

        Args:
            values: Data list

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

            # Calculate z-score of last value
            last_value = values[-1]
            z_score = abs((last_value - mean) / std)

            # Anomaly if z-score > 3 (3-sigma rule)
            return z_score > 3.0

        except Exception as e:
            logger.error(f"{self.sensor_name} Z-score detection error: {e}")
            return False

    def _detect_dbscan(self, values: List[float]) -> bool:
        """
        DBSCAN anomaly detection.

        DBSCAN (Density-Based Spatial Clustering of Applications with Noise):
        - Density-based clustering algorithm
        - Separates data into dense regions (clusters) and noise (outliers)
        - Points marked as noise are considered anomalies

        Most sophisticated method - can detect complex anomaly patterns.

        Args:
            values: Data list

        Returns:
            True if anomaly detected (last value marked as noise)
        """
        try:
            if len(values) < 5:
                return False

            if not SKLEARN_AVAILABLE:
                # sklearn not available, fallback to simple z-score
                logger.warning(f"{self.sensor_name}: sklearn not found, using fallback for DBSCAN")
                values_array = np.array(values[:-1])
                last_value = values[-1]
                mean_value = np.mean(values_array)
                std_value = np.std(values_array)
                if std_value == 0:
                    return mean_value != last_value
                z_score = abs((last_value - mean_value) / (std_value + 1e-10))
                return z_score > 2.5

            # Use sklearn DBSCAN
            # Convert to 2D array (required by DBSCAN)
            # For time series: represent each value as [index, value]
            values_array = np.array(values).reshape(-1, 1)

            # DBSCAN parameters:
            # eps: Maximum distance between two samples to be considered neighbors
            # min_samples: Minimum points to form a cluster
            # These should be tuned based on data distribution

            # Dynamic eps calculation: fraction of standard deviation
            std_value = np.std(values)
            ptp_value = np.ptp(values)  # ptp = peak-to-peak (max-min)

            # Ensure eps is always positive (DBSCAN requires eps > 0)
            # Use a small minimum value when data has zero variance
            eps = max(std_value * 0.5, ptp_value * 0.1, 1e-6)

            # min_samples: 10% of buffer size, minimum 2
            min_samples = max(2, int(len(values) * 0.1))

            # Apply DBSCAN
            dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean')
            labels = dbscan.fit_predict(values_array)

            # Check last value's label
            # Label -1 means noise/outlier/anomaly
            last_label = labels[-1]

            is_anomaly = last_label == -1

            if is_anomaly:
                logger.debug(f"{self.sensor_name}: DBSCAN anomaly detected (label: {last_label}, eps: {eps:.3f})")

            return is_anomaly

        except Exception as e:
            logger.error(f"{self.sensor_name} DBSCAN detection error: {e}")
            # Fallback on error
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
        """Get last value (thread-safe)"""
        with self._lock:
            return self._last_value

    def is_anomaly(self) -> bool:
        """Get anomaly state (thread-safe)"""
        with self._lock:
            return self._is_anomaly

    def set_method(self, method: DetectionMethod) -> None:
        """Change detection method"""
        self.method = method
        logger.info(f"{self.sensor_name} detection method changed: {method.value}")

    def clear_buffer(self) -> None:
        """Clear buffer (thread-safe)"""
        with self._lock:
            self._buffer.clear()
            self._is_anomaly = False

    def get_buffer_size(self) -> int:
        """Get current buffer size (thread-safe)"""
        with self._lock:
            return len(self._buffer)
