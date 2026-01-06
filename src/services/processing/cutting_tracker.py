"""
Cutting session tracking (singleton pattern).
"""

import logging
import threading
from datetime import datetime
from typing import Optional

from ...domain.enums import TesereDurumu

logger = logging.getLogger(__name__)


class CuttingTracker:
    """
    Singleton: Track cutting sessions with integer kesim_id.

    Features:
    - Detects cutting start/end (testere_durumu transitions)
    - Generates sequential kesim_id (integer, increments each cutting)
    - Tracks start/end height for each session
    - Stores session metadata to database
    - Thread-safe singleton implementation
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
        Initialize cutting tracker.

        Args:
            db_service: SQLiteService for total.db (optional)
        """
        # Prevent re-initialization
        if hasattr(self, '_initialized'):
            return

        self.db = db_service

        # Current session state
        self._current_kesim_id: Optional[int] = None
        self._previous_state = TesereDurumu.BOSTA
        self._data_count = 0

        # Session tracking
        self._session_start_time: Optional[datetime] = None
        self._session_controller_type: Optional[str] = None
        self._session_start_height: Optional[float] = None

        # Global kesim_id counter (persists across app restarts via DB)
        self._next_kesim_id = 1
        self._load_last_kesim_id()

        # Statistics
        self._total_sessions = 0
        self._total_cutting_time = 0.0

        # Thread safety
        self._state_lock = threading.RLock()

        self._initialized = True

        logger.info(f"CuttingTracker initialized (singleton), next_kesim_id={self._next_kesim_id}")

    def _load_last_kesim_id(self):
        """Load last kesim_id from database to continue sequence."""
        if not self.db:
            return

        try:
            result = self.db.read(
                "SELECT MAX(kesim_id) FROM cutting_sessions"
            )
            if result and result[0][0] is not None:
                self._next_kesim_id = result[0][0] + 1
                logger.info(f"Loaded last kesim_id from DB: {result[0][0]}")
        except Exception as e:
            logger.debug(f"Could not load last kesim_id: {e}")

    def update(
        self,
        testere_durumu: int,
        controller_type: str,
        kafa_yuksekligi_mm: float = 0.0
    ) -> Optional[int]:
        """
        Update cutting state and manage sessions.

        Args:
            testere_durumu: Current saw state (0-5)
            controller_type: "manual" or "ml"
            kafa_yuksekligi_mm: Current head height (mm)

        Returns:
            Current kesim_id (int) if cutting, None otherwise
        """
        with self._state_lock:
            try:
                current_state = TesereDurumu(testere_durumu)

                # Detect cutting start
                if (current_state == TesereDurumu.KESIYOR and
                    self._previous_state != TesereDurumu.KESIYOR):
                    self._start_session(controller_type, kafa_yuksekligi_mm)

                # Detect cutting end
                elif (self._previous_state == TesereDurumu.KESIYOR and
                      current_state != TesereDurumu.KESIYOR):
                    self._end_session(kafa_yuksekligi_mm)

                # Increment data count if cutting
                if current_state == TesereDurumu.KESIYOR and self._current_kesim_id is not None:
                    self._data_count += 1

                # Update state
                self._previous_state = current_state

                # Return current kesim_id
                return self._current_kesim_id

            except Exception as e:
                logger.error(f"Error updating cutting tracker: {e}", exc_info=True)
                return None

    def _start_session(self, controller_type: str, start_height: float):
        """
        Start new cutting session.

        Args:
            controller_type: "manual" or "ml"
            start_height: Head height at cutting start (mm)
        """
        self._current_kesim_id = self._next_kesim_id
        self._next_kesim_id += 1

        self._session_start_time = datetime.now()
        self._session_controller_type = controller_type
        self._session_start_height = start_height
        self._data_count = 0
        self._total_sessions += 1

        logger.info(
            f"Cutting session started: "
            f"kesim_id={self._current_kesim_id}, "
            f"controller={controller_type}, "
            f"start_height={start_height:.2f}mm"
        )

    def _end_session(self, end_height: float):
        """
        End current cutting session and save to database.

        Args:
            end_height: Head height at cutting end (mm)
        """
        if self._current_kesim_id is None:
            return

        end_time = datetime.now()

        # Calculate duration
        duration_ms = 0
        if self._session_start_time:
            duration_ms = int(
                (end_time - self._session_start_time).total_seconds() * 1000
            )
            self._total_cutting_time += duration_ms

        logger.info(
            f"Cutting session ended: "
            f"kesim_id={self._current_kesim_id}, "
            f"duration={duration_ms}ms, "
            f"data_count={self._data_count}, "
            f"height: {self._session_start_height:.2f} -> {end_height:.2f}mm"
        )

        # Save to database
        if self.db:
            self._save_session_to_db(
                kesim_id=self._current_kesim_id,
                start_time=self._session_start_time,
                end_time=end_time,
                controller_type=self._session_controller_type,
                start_height=self._session_start_height,
                end_height=end_height,
                duration_ms=duration_ms,
                data_count=self._data_count
            )

        # Clear current session
        self._current_kesim_id = None
        self._session_start_time = None
        self._session_controller_type = None
        self._session_start_height = None
        self._data_count = 0

    def _save_session_to_db(
        self,
        kesim_id: int,
        start_time: datetime,
        end_time: datetime,
        controller_type: str,
        start_height: float,
        end_height: float,
        duration_ms: int,
        data_count: int
    ):
        """
        Save session metadata to database.
        """
        try:
            sql = """
                INSERT INTO cutting_sessions (
                    kesim_id,
                    start_time,
                    end_time,
                    controller_type,
                    start_height_mm,
                    end_height_mm,
                    duration_ms,
                    data_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                kesim_id,
                start_time.isoformat() if start_time else None,
                end_time.isoformat() if end_time else None,
                controller_type,
                start_height,
                end_height,
                duration_ms,
                data_count
            )

            self.db.write_async(sql, params)

        except Exception as e:
            logger.error(f"Error saving session to database: {e}")

    def get_current_kesim_id(self) -> Optional[int]:
        """
        Get current kesim_id.

        Returns:
            kesim_id (int) if cutting, None otherwise
        """
        with self._state_lock:
            return self._current_kesim_id

    def is_cutting(self) -> bool:
        """
        Check if currently cutting.

        Returns:
            True if cutting, False otherwise
        """
        with self._state_lock:
            return self._current_kesim_id is not None

    def get_stats(self) -> dict:
        """
        Get tracker statistics.

        Returns:
            Dictionary with statistics
        """
        with self._state_lock:
            return {
                'total_sessions': self._total_sessions,
                'total_cutting_time_ms': self._total_cutting_time,
                'current_kesim_id': self._current_kesim_id,
                'is_cutting': self.is_cutting(),
                'current_data_count': self._data_count if self._current_kesim_id else 0
            }
