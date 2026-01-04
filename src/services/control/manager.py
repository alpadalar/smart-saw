"""
Control manager - orchestrates Manual/ML controller switching.
"""

import asyncio
import logging
import threading
from typing import Optional

from ...domain.enums import ControlMode
from ...domain.models import ControlCommand, ProcessedData
from .manual import ManualController
from .ml_controller import MLController

logger = logging.getLogger(__name__)


class ControlManager:
    """
    Orchestrates controller mode switching and initial delay logic.

    Features:
    - Thread-safe mode switching (RLock)
    - Initial delay calculation (based on head height)
    - Delegates to active controller (Manual or ML)
    - Health monitoring
    """

    def __init__(
        self,
        config: dict,
        modbus_service,
        ml_db_service
    ):
        """
        Initialize control manager.

        Args:
            config: System configuration dictionary
            modbus_service: AsyncModbusService instance
            ml_db_service: SQLiteService for ml.db
        """
        self.config = config

        # Initial delay configuration
        self.initial_delay_enabled = config['control']['initial_delay']['enabled']
        self.target_distance_mm = config['control']['initial_delay']['target_distance_mm']
        self.default_delay_ms = config['control']['initial_delay']['default_delay_ms']

        # Current mode
        default_mode = config['control']['default_mode']
        self._current_mode = ControlMode(default_mode)
        self._lock = threading.RLock()

        # Controllers
        self.manual_controller = ManualController(config)
        self.ml_controller = MLController(config, modbus_service, ml_db_service)

        # State tracking
        self._cutting_started_time: Optional[float] = None
        self._initial_head_height: Optional[float] = None
        self._initial_delay_passed = False

        logger.info(
            f"ControlManager initialized: "
            f"mode={self._current_mode.value}, "
            f"initial_delay={self.initial_delay_enabled}"
        )

    async def process_data(
        self,
        processed_data: ProcessedData
    ) -> Optional[ControlCommand]:
        """
        Process sensor data and generate speed commands.

        Decision tree:
        1. Check cutting state
        2. Calculate/check initial delay
        3. Delegate to active controller

        Args:
            processed_data: ProcessedData with sensor readings

        Returns:
            ControlCommand if speeds should be updated, None otherwise
        """
        with self._lock:
            try:
                raw_data = processed_data.raw_data

                # Check cutting state
                is_cutting = (raw_data.testere_durumu == 3)

                if is_cutting:
                    # Check initial delay
                    if not self._check_initial_delay(raw_data):
                        # Still in initial delay period
                        return None

                    # Delegate to active controller
                    if self._current_mode == ControlMode.ML:
                        return await self.ml_controller.calculate_speeds(processed_data)
                    else:
                        # Manual mode - no automatic speed changes
                        return None
                else:
                    # Not cutting - reset state
                    self._reset_cutting_state()
                    return None

            except Exception as e:
                logger.error(f"Error in control manager: {e}", exc_info=True)
                return None

    def _check_initial_delay(self, raw_data) -> bool:
        """
        Check if initial delay period has passed.

        Logic:
        - Record start time and head height on first cutting iteration
        - Calculate expected delay based on descent to target distance
        - ML control disabled until delay passes

        Args:
            raw_data: RawSensorData with current readings

        Returns:
            True if delay passed (or disabled), False if still waiting
        """
        if not self.initial_delay_enabled:
            return True

        if self._initial_delay_passed:
            return True

        now = asyncio.get_event_loop().time()

        # Record initial state
        if self._cutting_started_time is None:
            self._cutting_started_time = now
            self._initial_head_height = raw_data.kafa_yuksekligi_mm
            logger.info(
                f"Cutting started: "
                f"initial_height={self._initial_head_height:.1f}mm"
            )

        # Calculate expected delay based on current height
        if self._initial_head_height is not None:
            current_height = raw_data.kafa_yuksekligi_mm
            descended_distance = self._initial_head_height - current_height

            # Check if target distance reached
            if descended_distance >= self.target_distance_mm:
                self._initial_delay_passed = True
                elapsed = (now - self._cutting_started_time) * 1000  # ms
                logger.info(
                    f"Initial delay passed: "
                    f"descended={descended_distance:.1f}mm, "
                    f"elapsed={elapsed:.0f}ms"
                )
                return True

        # Check default timeout (fallback)
        elapsed_ms = (now - self._cutting_started_time) * 1000
        if elapsed_ms >= self.default_delay_ms:
            self._initial_delay_passed = True
            logger.warning(
                f"Initial delay passed by timeout: "
                f"elapsed={elapsed_ms:.0f}ms (default={self.default_delay_ms}ms)"
            )
            return True

        return False

    def _reset_cutting_state(self):
        """
        Reset cutting state when cutting stops.
        """
        if self._cutting_started_time is not None:
            self._cutting_started_time = None
            self._initial_head_height = None
            self._initial_delay_passed = False
            logger.debug("Cutting state reset")

    async def set_mode(self, mode: ControlMode) -> bool:
        """
        Switch control mode.

        Args:
            mode: ControlMode.MANUAL or ControlMode.ML

        Returns:
            True if mode changed successfully
        """
        with self._lock:
            try:
                if mode == self._current_mode:
                    logger.debug(f"Already in {mode.value} mode")
                    return True

                old_mode = self._current_mode
                self._current_mode = mode

                logger.info(f"Control mode changed: {old_mode.value} → {mode.value}")

                # Reset state on mode change
                self._reset_cutting_state()

                return True

            except Exception as e:
                logger.error(f"Error changing control mode: {e}", exc_info=True)
                return False

    def get_current_mode(self) -> ControlMode:
        """
        Get current control mode.

        Returns:
            Current ControlMode
        """
        with self._lock:
            return self._current_mode

    async def manual_set_speeds(
        self,
        kesme_hizi: float,
        inme_hizi: float
    ) -> Optional[ControlCommand]:
        """
        Set speeds manually (GUI button press).

        Only works in Manual mode.

        Args:
            kesme_hizi: Target cutting speed
            inme_hizi: Target descent speed

        Returns:
            ControlCommand if successful, None otherwise
        """
        with self._lock:
            if self._current_mode != ControlMode.MANUAL:
                logger.warning(
                    f"Manual speed setting rejected: "
                    f"current mode is {self._current_mode.value}"
                )
                return None

            return await self.manual_controller.set_speeds(kesme_hizi, inme_hizi)

    def get_status(self) -> dict:
        """
        Get control manager status.

        Returns:
            Dictionary with status information
        """
        with self._lock:
            status = {
                'mode': self._current_mode.value,
                'initial_delay_enabled': self.initial_delay_enabled,
                'initial_delay_passed': self._initial_delay_passed,
                'cutting_started_time': self._cutting_started_time,
                'initial_head_height': self._initial_head_height
            }

            # Add ML controller stats if in ML mode
            if self._current_mode == ControlMode.ML:
                status['ml_stats'] = self.ml_controller.get_stats()

            return status

    def get_speed_limits(self) -> dict:
        """
        Get speed limits for GUI.

        Returns:
            Dictionary with min/max limits
        """
        return self.manual_controller.get_current_limits()
