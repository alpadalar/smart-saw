"""
Anomaly detection for sensor data.
"""

import logging
import numpy as np
from collections import deque
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalies in sensor data using statistical methods.

    Methods:
    - Z-score: Detect outliers based on standard deviation
    - IQR (Interquartile Range): Robust outlier detection
    - Range checks: Hard limits for sensor values

    Features:
    - Configurable thresholds per sensor
    - Rolling window for baseline calculation
    - Multiple detection methods
    """

    def __init__(self, config: dict):
        """
        Initialize anomaly detector.

        Args:
            config: Anomaly detection configuration
        """
        self.config = config

        # Window size for baseline calculation
        self.window_size = config.get('window_size', 100)

        # Detection thresholds
        self.z_score_threshold = config.get('z_score_threshold', 3.0)
        self.iqr_multiplier = config.get('iqr_multiplier', 1.5)

        # Sensor-specific hard limits (configurable)
        self.sensor_limits = config.get('sensor_limits', {})

        # Rolling windows for each sensor
        self._windows: Dict[str, deque] = {}

        # Statistics
        self._anomalies_detected = 0

        logger.info(
            f"AnomalyDetector initialized: "
            f"window={self.window_size}, "
            f"z_threshold={self.z_score_threshold}"
        )

    def detect(self, raw_data) -> Dict[str, List[str]]:
        """
        Detect anomalies in sensor data.

        Args:
            raw_data: RawSensorData instance

        Returns:
            Dictionary mapping sensor names to list of anomaly types detected
        """
        anomalies = {}

        # Check each sensor field
        sensors_to_check = [
            ('serit_motor_akim_a', raw_data.serit_motor_akim_a),
            ('serit_motor_tork_percentage', raw_data.serit_motor_tork_percentage),
            ('inme_motor_akim_a', raw_data.inme_motor_akim_a),
            ('serit_sapmasi', raw_data.serit_sapmasi),
            ('serit_gerginligi_bar', raw_data.serit_gerginligi_bar),
            ('mengene_basinc_bar', raw_data.mengene_basinc_bar),
            ('ortam_sicakligi_c', raw_data.ortam_sicakligi_c),
            ('sogutma_sivi_sicakligi_c', raw_data.sogutma_sivi_sicakligi_c),
            ('hidrolik_yag_sicakligi_c', raw_data.hidrolik_yag_sicakligi_c),
            ('max_titresim_hz', raw_data.max_titresim_hz)
        ]

        for sensor_name, value in sensors_to_check:
            detected = self._check_sensor(sensor_name, value)
            if detected:
                anomalies[sensor_name] = detected
                self._anomalies_detected += 1

        if anomalies:
            logger.warning(f"Anomalies detected: {anomalies}")

        return anomalies

    def _check_sensor(self, sensor_name: str, value: float) -> List[str]:
        """
        Check single sensor for anomalies.

        Args:
            sensor_name: Name of sensor
            value: Current sensor value

        Returns:
            List of anomaly types detected (empty if none)
        """
        anomalies = []

        # Skip if value is None or invalid
        if value is None or not isinstance(value, (int, float)):
            return anomalies

        # Initialize window if needed
        if sensor_name not in self._windows:
            self._windows[sensor_name] = deque(maxlen=self.window_size)

        # Add to window
        self._windows[sensor_name].append(value)

        # Need sufficient data for statistical methods
        if len(self._windows[sensor_name]) < 10:
            return anomalies

        # 1. Range check (hard limits)
        if sensor_name in self.sensor_limits:
            limits = self.sensor_limits[sensor_name]
            if 'min' in limits and value < limits['min']:
                anomalies.append('below_min')
            if 'max' in limits and value > limits['max']:
                anomalies.append('above_max')

        # 2. Z-score check
        if self._check_z_score(sensor_name, value):
            anomalies.append('z_score_outlier')

        # 3. IQR check
        if self._check_iqr(sensor_name, value):
            anomalies.append('iqr_outlier')

        return anomalies

    def _check_z_score(self, sensor_name: str, value: float) -> bool:
        """
        Z-score based outlier detection.

        Args:
            sensor_name: Name of sensor
            value: Current value

        Returns:
            True if outlier detected
        """
        try:
            window = list(self._windows[sensor_name])
            mean = np.mean(window)
            std = np.std(window)

            if std == 0:
                return False

            z_score = abs((value - mean) / std)

            return z_score > self.z_score_threshold

        except Exception as e:
            logger.error(f"Error calculating z-score for {sensor_name}: {e}")
            return False

    def _check_iqr(self, sensor_name: str, value: float) -> bool:
        """
        IQR (Interquartile Range) based outlier detection.

        More robust to outliers than z-score.

        Args:
            sensor_name: Name of sensor
            value: Current value

        Returns:
            True if outlier detected
        """
        try:
            window = list(self._windows[sensor_name])

            q1 = np.percentile(window, 25)
            q3 = np.percentile(window, 75)
            iqr = q3 - q1

            lower_bound = q1 - (self.iqr_multiplier * iqr)
            upper_bound = q3 + (self.iqr_multiplier * iqr)

            return value < lower_bound or value > upper_bound

        except Exception as e:
            logger.error(f"Error calculating IQR for {sensor_name}: {e}")
            return False

    def reset(self):
        """
        Reset all windows (called when cutting stops).
        """
        self._windows.clear()
        logger.debug("Anomaly detector windows reset")

    def get_stats(self) -> dict:
        """
        Get detector statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'anomalies_detected': self._anomalies_detected,
            'active_windows': len(self._windows),
            'window_sizes': {
                name: len(window)
                for name, window in self._windows.items()
            }
        }
