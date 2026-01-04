"""
Cutting session tracking (singleton pattern).
"""

import logging
import threading
from datetime import datetime
from typing import Optional
from uuid import uuid4

from ...domain.models import CuttingSession
from ...domain.enums import TesereDurumu

logger = logging.getLogger(__name__)


class CuttingTracker:
    """
    Singleton: Track cutting sessions and generate session IDs.

    Features:
    - Detects cutting start/end (testere_durumu transitions)
    - Generates unique session IDs (UUID)
    - Stores session metadata
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
        self._current_session: Optional[CuttingSession] = None
        self._previous_state = TesereDurumu.IDLE
        self._data_count = 0

        # Statistics
        self._total_sessions = 0
        self._total_cutting_time = 0.0

        # Thread safety
        self._state_lock = threading.RLock()

        self._initialized = True

        logger.info("CuttingTracker initialized (singleton)")

    def update(self, testere_durumu: int, controller_type: str) -> Optional[str]:
        """
        Update cutting state and manage sessions.

        Args:
            testere_durumu: Current saw state (0-5)
            controller_type: "manual" or "ml"

        Returns:
            Current session ID if cutting, None otherwise
        """
        with self._state_lock:
            try:
                current_state = TesereDurumu(testere_durumu)

                # Detect cutting start
                if (current_state == TesereDurumu.CUTTING and
                    self._previous_state != TesereDurumu.CUTTING):
                    self._start_session(controller_type)

                # Detect cutting end
                elif (self._previous_state == TesereDurumu.CUTTING and
                      current_state != TesereDurumu.CUTTING):
                    self._end_session()

                # Increment data count if cutting
                if current_state == TesereDurumu.CUTTING and self._current_session:
                    self._data_count += 1

                # Update state
                self._previous_state = current_state

                # Return current session ID
                return self._current_session.session_id if self._current_session else None

            except Exception as e:
                logger.error(f"Error updating cutting tracker: {e}", exc_info=True)
                return None

    def _start_session(self, controller_type: str):
        """
        Start new cutting session.

        Args:
            controller_type: "manual" or "ml"
        """
        session_id = str(uuid4())

        self._current_session = CuttingSession(
            session_id=session_id,
            start_time=datetime.now(),
            end_time=None,
            controller_type=controller_type,
            data_count=0,
            duration_ms=None
        )

        self._data_count = 0
        self._total_sessions += 1

        logger.info(
            f"Cutting session started: "
            f"id={session_id}, "
            f"controller={controller_type}"
        )

    def _end_session(self):
        """
        End current cutting session and save to database.
        """
        if self._current_session is None:
            return

        # Update session data
        self._current_session.end_time = datetime.now()
        self._current_session.data_count = self._data_count

        # Calculate duration
        duration = (
            self._current_session.end_time - self._current_session.start_time
        ).total_seconds() * 1000  # milliseconds

        self._current_session.duration_ms = duration
        self._total_cutting_time += duration

        logger.info(
            f"Cutting session ended: "
            f"id={self._current_session.session_id}, "
            f"duration={duration:.0f}ms, "
            f"data_count={self._data_count}"
        )

        # Save to database
        if self.db:
            self._save_session_to_db(self._current_session)

        # Clear current session
        self._current_session = None
        self._data_count = 0

    def _save_session_to_db(self, session: CuttingSession):
        """
        Save session metadata to database.

        Args:
            session: CuttingSession to save
        """
        try:
            sql = """
                INSERT INTO cutting_sessions (
                    session_id,
                    start_time,
                    end_time,
                    controller_type,
                    data_count,
                    duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?)
            """

            params = (
                session.session_id,
                session.start_time.isoformat(),
                session.end_time.isoformat() if session.end_time else None,
                session.controller_type,
                session.data_count,
                session.duration_ms
            )

            self.db.write_async(sql, params)

        except Exception as e:
            logger.error(f"Error saving session to database: {e}")

    def get_current_session_id(self) -> Optional[str]:
        """
        Get current session ID.

        Returns:
            Session ID if cutting, None otherwise
        """
        with self._state_lock:
            return self._current_session.session_id if self._current_session else None

    def is_cutting(self) -> bool:
        """
        Check if currently cutting.

        Returns:
            True if cutting, False otherwise
        """
        with self._state_lock:
            return self._current_session is not None

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
                'current_session_id': self.get_current_session_id(),
                'is_cutting': self.is_cutting(),
                'current_data_count': self._data_count if self._current_session else 0
            }
