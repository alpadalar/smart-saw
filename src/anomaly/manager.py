"""
Anomaly Manager

Manages all anomaly detectors with thread-safe operation and callback system.
"""

import threading
from typing import Dict, Optional, Callable
import logging

from .detectors import (
    SeritSapmasiDetector,
    SeritMotorAkimDetector,
    SeritMotorTorkDetector,
    SeritKesmeHiziDetector,
    SeritInmeHiziDetector,
    TitresimXDetector,
    TitresimYDetector,
    TitresimZDetector,
    SeritGerginligiDetector
)

logger = logging.getLogger(__name__)


class AnomalyManager:
    """
    Thread-safe manager for all anomaly detectors.

    Features:
    - Manages 9 specialized detectors
    - Thread-safe state management
    - Callback system for real-time UI updates
    - Runtime method switching
    """

    def __init__(self, buffer_size: int = 100, min_samples: int = 10):
        """
        Initialize anomaly manager.

        Args:
            buffer_size: Buffer size for each detector
            min_samples: Minimum samples required for detection
        """
        self.buffer_size = buffer_size
        self.min_samples = min_samples

        # Thread-safe lock
        self._lock = threading.Lock()

        # Create detectors with optimized methods per sensor
        self.detectors = {
            'serit_sapmasi': SeritSapmasiDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'serit_motor_akim': SeritMotorAkimDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'serit_motor_tork': SeritMotorTorkDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'serit_kesme_hizi': SeritKesmeHiziDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'serit_inme_hizi': SeritInmeHiziDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'titresim_x': TitresimXDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'titresim_y': TitresimYDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'titresim_z': TitresimZDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
            'serit_gerginligi': SeritGerginligiDetector(
                buffer_size=buffer_size,
                min_samples=min_samples
            ),
        }

        # Anomaly states (keys match pyside_sensor.py)
        self.anomaly_states = {
            'SeritSapmasi': False,
            'SeritAkim': False,
            'KesmeHizi': False,
            'IlerlemeHizi': False,
            'TitresimX': False,
            'TitresimY': False,
            'TitresimZ': False,
            'SeritGerginligi': False,
            'SeritTork': False,
        }

        # Callback function for UI updates
        self._update_callback: Optional[Callable[[str, bool], None]] = None

        logger.info("AnomalyManager initialized")
        logger.info(f"  - Detector count: {len(self.detectors)}")
        logger.info(f"  - Buffer size: {buffer_size}")
        logger.info(f"  - Min samples: {min_samples}")

    def set_update_callback(self, callback: Callable[[str, bool], None]) -> None:
        """
        Set anomaly state update callback.

        Args:
            callback: Function (sensor_key, is_anomaly) -> None
        """
        self._update_callback = callback
        logger.info("AnomalyManager update callback set")

    def process_data(self, data: Dict, is_cutting: bool = False) -> Dict[str, bool]:
        """
        Process new data and detect anomalies (thread-safe).

        Args:
            data: Processed data dictionary
            is_cutting: Whether cutting is active

        Returns:
            Anomaly states dictionary
        """
        try:
            results = {}

            # Process each sensor
            # Band deviation
            if 'serit_sapmasi' in data:
                value = data.get('serit_sapmasi', 0.0)
                self.detectors['serit_sapmasi'].add_data_point(value, is_cutting)
                is_anomaly = self.detectors['serit_sapmasi'].detect()
                results['SeritSapmasi'] = is_anomaly
                with self._lock:
                    self.anomaly_states['SeritSapmasi'] = is_anomaly

            # Band motor current
            if 'serit_motor_akim_a' in data:
                value = data.get('serit_motor_akim_a', 0.0)
                self.detectors['serit_motor_akim'].add_data_point(value, is_cutting)
                is_anomaly = self.detectors['serit_motor_akim'].detect()
                results['SeritAkim'] = is_anomaly
                with self._lock:
                    self.anomaly_states['SeritAkim'] = is_anomaly

            # Band motor torque
            if 'serit_motor_tork_percentage' in data:
                value = data.get('serit_motor_tork_percentage', 0.0)
                self.detectors['serit_motor_tork'].add_data_point(value, is_cutting)
                is_anomaly = self.detectors['serit_motor_tork'].detect()
                results['SeritTork'] = is_anomaly
                with self._lock:
                    self.anomaly_states['SeritTork'] = is_anomaly

            # Cutting speed
            if 'serit_kesme_hizi' in data:
                value = data.get('serit_kesme_hizi', 0.0)
                self.detectors['serit_kesme_hizi'].add_data_point(value, is_cutting)
                is_anomaly = self.detectors['serit_kesme_hizi'].detect()
                results['KesmeHizi'] = is_anomaly
                with self._lock:
                    self.anomaly_states['KesmeHizi'] = is_anomaly

            # Feed rate
            if 'serit_inme_hizi' in data:
                value = data.get('serit_inme_hizi', 0.0)
                self.detectors['serit_inme_hizi'].add_data_point(value, is_cutting)
                is_anomaly = self.detectors['serit_inme_hizi'].detect()
                results['IlerlemeHizi'] = is_anomaly
                with self._lock:
                    self.anomaly_states['IlerlemeHizi'] = is_anomaly

            # Vibration X
            if 'ivme_olcer_x_hz' in data:
                value = data.get('ivme_olcer_x_hz', 0.0)
                self.detectors['titresim_x'].add_data_point(value, is_cutting)
                is_anomaly = self.detectors['titresim_x'].detect()
                results['TitresimX'] = is_anomaly
                with self._lock:
                    self.anomaly_states['TitresimX'] = is_anomaly

            # Vibration Y
            if 'ivme_olcer_y_hz' in data:
                value = data.get('ivme_olcer_y_hz', 0.0)
                self.detectors['titresim_y'].add_data_point(value, is_cutting)
                is_anomaly = self.detectors['titresim_y'].detect()
                results['TitresimY'] = is_anomaly
                with self._lock:
                    self.anomaly_states['TitresimY'] = is_anomaly

            # Vibration Z
            if 'ivme_olcer_z_hz' in data:
                value = data.get('ivme_olcer_z_hz', 0.0)
                self.detectors['titresim_z'].add_data_point(value, is_cutting)
                is_anomaly = self.detectors['titresim_z'].detect()
                results['TitresimZ'] = is_anomaly
                with self._lock:
                    self.anomaly_states['TitresimZ'] = is_anomaly

            # Band tension
            if 'serit_gerginligi_bar' in data:
                value = data.get('serit_gerginligi_bar', 0.0)
                self.detectors['serit_gerginligi'].add_data_point(value, is_cutting)
                is_anomaly = self.detectors['serit_gerginligi'].detect()
                results['SeritGerginligi'] = is_anomaly
                with self._lock:
                    self.anomaly_states['SeritGerginligi'] = is_anomaly

            # Call callback for each result
            if self._update_callback:
                for key, is_anomaly in results.items():
                    try:
                        self._update_callback(key, is_anomaly)
                    except Exception as e:
                        logger.error(f"Anomaly callback error ({key}): {e}")

            return results

        except Exception as e:
            logger.error(f"AnomalyManager process_data error: {e}")
            return {}

    def get_anomaly_states(self) -> Dict[str, bool]:
        """
        Get current anomaly states (thread-safe).

        Returns:
            Anomaly states dictionary
        """
        with self._lock:
            return dict(self.anomaly_states)

    def reset_anomaly_states(self) -> None:
        """Reset all anomaly states (thread-safe)"""
        with self._lock:
            for key in self.anomaly_states:
                self.anomaly_states[key] = False

            # Clear detector buffers
            for detector in self.detectors.values():
                detector.clear_buffer()

        logger.info("AnomalyManager: All anomaly states reset")

    def get_detector(self, sensor_name: str):
        """
        Get specific detector.

        Args:
            sensor_name: Detector name ('serit_sapmasi', 'serit_motor_akim', etc.)

        Returns:
            Detector instance or None
        """
        return self.detectors.get(sensor_name)

    def set_detection_method(self, sensor_name: str, method) -> None:
        """
        Change detection method for specific detector.

        Args:
            sensor_name: Detector name
            method: DetectionMethod enum value
        """
        detector = self.detectors.get(sensor_name)
        if detector:
            detector.set_method(method)
            logger.info(f"{sensor_name} detection method changed: {method.value}")
        else:
            logger.warning(f"Detector not found: {sensor_name}")

    def get_stats(self) -> Dict:
        """
        Get statistics from all detectors.

        Returns:
            Statistics dictionary
        """
        stats = {}
        with self._lock:
            stats['anomaly_states'] = dict(self.anomaly_states)
            stats['detector_methods'] = {
                name: detector.method.value
                for name, detector in self.detectors.items()
            }
            stats['buffer_fills'] = {
                name: f"{detector.get_buffer_size()}/{detector.buffer_size}"
                for name, detector in self.detectors.items()
            }
        return stats
