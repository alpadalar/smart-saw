"""
Anomaly tracking with database persistence and reset functionality.
"""

import logging
import threading
from datetime import datetime
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class AnomalyTracker:
    """
    Tracks anomalies with database persistence and reset functionality.

    Features:
    - Saves each anomaly event to database
    - Tracks last reset time
    - Provides summary by sensor (first/last timestamp, count)
    - Only shows anomalies after last reset
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_service=None):
        """
        Initialize anomaly tracker.

        Args:
            db_service: SQLiteService for anomaly.db
        """
        if hasattr(self, '_initialized'):
            return

        self.db = db_service
        self._state_lock = threading.RLock()

        # Last reset time (loaded from DB or set to app start)
        self._last_reset_time: datetime = datetime.now()
        self._load_last_reset_time()

        # In-memory cache of anomalies since last reset
        # Format: {sensor_name: {'first_time': datetime, 'last_time': datetime, 'count': int, 'last_value': float}}
        self._anomaly_cache: Dict[str, Dict[str, Any]] = {}

        self._initialized = True
        logger.info(f"AnomalyTracker initialized, last_reset={self._last_reset_time.isoformat()}")

    def _load_last_reset_time(self):
        """Load last reset time from database."""
        if not self.db:
            return

        try:
            result = self.db.read(
                "SELECT reset_time FROM anomaly_resets ORDER BY id DESC LIMIT 1"
            )
            if result and result[0][0]:
                self._last_reset_time = datetime.fromisoformat(result[0][0])
                logger.info(f"Loaded last reset time from DB: {self._last_reset_time}")
        except Exception as e:
            logger.debug(f"Could not load last reset time: {e}")

    def record_anomaly(
        self,
        sensor_name: str,
        sensor_value: float,
        detection_method: str = "unknown",
        kesim_id: Optional[int] = None
    ):
        """
        Record a new anomaly event.

        Args:
            sensor_name: Name of the sensor that detected anomaly
            sensor_value: Current value of the sensor
            detection_method: Detection method used (z_score, iqr, etc.)
            kesim_id: Current cutting session ID (if cutting)
        """
        with self._state_lock:
            now = datetime.now()

            # Update in-memory cache
            if sensor_name not in self._anomaly_cache:
                self._anomaly_cache[sensor_name] = {
                    'first_time': now,
                    'last_time': now,
                    'count': 1,
                    'last_value': sensor_value,
                    'detection_method': detection_method
                }
            else:
                self._anomaly_cache[sensor_name]['last_time'] = now
                self._anomaly_cache[sensor_name]['count'] += 1
                self._anomaly_cache[sensor_name]['last_value'] = sensor_value

            # Save to database
            if self.db:
                self._save_anomaly_to_db(
                    timestamp=now,
                    sensor_name=sensor_name,
                    sensor_value=sensor_value,
                    detection_method=detection_method,
                    kesim_id=kesim_id
                )

    def _save_anomaly_to_db(
        self,
        timestamp: datetime,
        sensor_name: str,
        sensor_value: float,
        detection_method: str,
        kesim_id: Optional[int]
    ):
        """Save anomaly event to database."""
        try:
            sql = """
                INSERT INTO anomaly_events (
                    timestamp,
                    sensor_name,
                    sensor_value,
                    detection_method,
                    kesim_id
                ) VALUES (?, ?, ?, ?, ?)
            """
            params = (
                timestamp.isoformat(),
                sensor_name,
                sensor_value,
                detection_method,
                kesim_id
            )
            self.db.write_async(sql, params)
        except Exception as e:
            logger.error(f"Error saving anomaly to database: {e}")

    def reset(self, reset_by: str = "user"):
        """
        Reset anomaly tracking (clear cache and record reset time).

        Args:
            reset_by: Who/what triggered the reset
        """
        with self._state_lock:
            now = datetime.now()
            self._last_reset_time = now
            self._anomaly_cache.clear()

            # Save reset to database
            if self.db:
                try:
                    sql = "INSERT INTO anomaly_resets (reset_time, reset_by) VALUES (?, ?)"
                    self.db.write_async(sql, (now.isoformat(), reset_by))
                except Exception as e:
                    logger.error(f"Error saving reset to database: {e}")

            logger.info(f"Anomaly tracking reset by {reset_by}")

    def get_anomaly_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary of anomalies since last reset.

        Returns:
            Dictionary with format:
            {
                'sensor_name': {
                    'first_time': 'ISO timestamp',
                    'last_time': 'ISO timestamp',
                    'count': int,
                    'last_value': float,
                    'detection_method': str
                },
                ...
            }
        """
        with self._state_lock:
            result = {}
            for sensor_name, data in self._anomaly_cache.items():
                result[sensor_name] = {
                    'first_time': data['first_time'].isoformat(),
                    'last_time': data['last_time'].isoformat(),
                    'count': data['count'],
                    'last_value': data['last_value'],
                    'detection_method': data.get('detection_method', 'unknown')
                }
            return result

    def get_anomaly_list_for_gui(self) -> List[Dict[str, Any]]:
        """
        Get anomaly list formatted for GUI display.

        Returns:
            List of anomaly info dictionaries sorted by count (descending)
        """
        with self._state_lock:
            result = []
            for sensor_name, data in self._anomaly_cache.items():
                # Format time range string
                first_time = data['first_time']
                last_time = data['last_time']
                count = data['count']

                if count == 1:
                    time_str = first_time.strftime("%H:%M:%S")
                else:
                    time_str = f"{first_time.strftime('%H:%M:%S')} - {last_time.strftime('%H:%M:%S')}"

                result.append({
                    'sensor': sensor_name,
                    'time_range': time_str,
                    'count': count,
                    'last_value': data['last_value'],
                    'detection_method': data.get('detection_method', 'unknown')
                })

            # Sort by count descending
            result.sort(key=lambda x: x['count'], reverse=True)
            return result

    def get_last_reset_time(self) -> datetime:
        """Get last reset time."""
        with self._state_lock:
            return self._last_reset_time

    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics."""
        with self._state_lock:
            total_anomalies = sum(d['count'] for d in self._anomaly_cache.values())
            return {
                'last_reset_time': self._last_reset_time.isoformat(),
                'sensor_count': len(self._anomaly_cache),
                'total_anomalies': total_anomalies,
                'sensors_with_anomalies': list(self._anomaly_cache.keys())
            }
