"""
ML-based speed controller with Torque Guard protection.

This is the most complex component in the system, implementing:
- ML model inference (Bagging ensemble)
- Buffer-based noise reduction
- Torque Guard (spike detection and emergency response)
- Speed change accumulation (threshold-based writing)
- Database logging (ML predictions)
"""

import asyncio
import logging
import numpy as np
import sqlite3
import threading
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from ...ml.model_loader import MLModelLoader
from ...ml.preprocessor import MLPreprocessor
from ...domain.models import ControlCommand, ProcessedData
from ...domain.validators import validate_speed

logger = logging.getLogger(__name__)


class MLController:
    """
    ML-based speed controller with intelligent torque protection.

    Architecture:
    - ML inference: Bagging model predicts coefficient [-1, 1]
    - Preprocessor: Averages sensor data from buffers (noise reduction)
    - Torque Guard: Detects rapid torque increases, applies emergency reduction
    - Accumulation: Buffers small speed changes, writes when threshold exceeded
    - Database: Logs all ML predictions for analysis

    Thread Safety:
    - Uses thread-local storage for SQLite connections
    - RLock for shared state access
    """

    def __init__(self, config: dict, modbus_service, db_service):
        """
        Initialize ML controller.

        Args:
            config: Full system configuration dictionary
            modbus_service: AsyncModbusService instance
            db_service: SQLiteService instance for ml.db
        """
        self.config = config
        self.modbus = modbus_service
        self.db = db_service

        # ML components
        model_path = Path(config['ml']['model_path'])
        self.model_loader = MLModelLoader(model_path)
        self.preprocessor = MLPreprocessor(config['ml'])

        # Torque Guard configuration
        tg_config = config['ml']['torque_guard']
        self.torque_guard_enabled = tg_config['enabled']
        self.tg_activation_delay = tg_config['activation_delay_seconds']
        self.tg_height_threshold = tg_config['height_threshold_mm']
        self.tg_torque_threshold = tg_config['torque_increase_threshold']
        self.tg_reduction_factor = tg_config['speed_reduction_factor']

        # Torque Guard state
        self.height_torque_buffer: List[Tuple[float, float]] = []
        self.ml_activation_time: Optional[float] = None
        self.torque_guard_triggered = False
        self.torque_guard_monitoring_started = False  # Track first activation

        # Speed change accumulators
        self.kesme_hizi_degisim_buffer = 0.0
        self.inme_hizi_degisim_buffer = 0.0

        # Speed change thresholds (when to write to Modbus)
        write_thresholds = config['ml'].get('write_thresholds', {})

        # Inme threshold config
        inme_config = write_thresholds.get('inme_hizi', {})
        self.inme_threshold_enabled = inme_config.get('enabled', True) if isinstance(inme_config, dict) else True
        self.inme_threshold = inme_config.get('threshold', 1.0) if isinstance(inme_config, dict) else inme_config

        # Kesme threshold config
        kesme_config = write_thresholds.get('kesme_hizi', {})
        self.kesme_threshold_enabled = kesme_config.get('enabled', True) if isinstance(kesme_config, dict) else True
        self.kesme_threshold = kesme_config.get('threshold', 0.9) if isinstance(kesme_config, dict) else kesme_config

        # State tracking
        self.is_cutting = False
        self.last_update_time: Optional[float] = None
        self.min_update_interval = config['ml'].get('min_speed_update_interval', 0.1)

        # Global coefficient multiplier
        self.katsayi = config['ml'].get('katsayi', 1.0)

        # Speed limits
        self.limits = config['control']['speed_limits']

        # Lock for thread safety
        self._lock = threading.RLock()

        # Statistics
        self._stats = {
            'predictions': 0,
            'torque_guard_activations': 0,
            'speed_commands_sent': 0,
            'errors': 0
        }

        logger.info(
            f"MLController initialized: "
            f"torque_guard={self.torque_guard_enabled}, "
            f"katsayi={self.katsayi}, "
            f"inme_threshold={'enabled' if self.inme_threshold_enabled else 'disabled'} "
            f"({self.inme_threshold if self.inme_threshold_enabled else 'immediate write'}), "
            f"kesme_threshold={'enabled' if self.kesme_threshold_enabled else 'disabled'} "
            f"({self.kesme_threshold if self.kesme_threshold_enabled else 'immediate write'})"
        )

    async def calculate_speeds(
        self,
        processed_data: 'ProcessedData'
    ) -> Optional[ControlCommand]:
        """
        Main control loop entry point.

        Decision tree:
        1. Check if cutting (testere_durumu == 3)
        2. Check update interval (rate limiting)
        3. Record ML activation time (first cutting iteration)
        4. Add data to preprocessor buffers
        5. Check Torque Guard (priority over normal ML)
        6. Normal ML prediction
        7. Calculate new speeds
        8. Accumulate changes
        9. Return command if thresholds exceeded

        Args:
            processed_data: ProcessedData with sensor readings

        Returns:
            ControlCommand if speeds should be updated, None otherwise
        """
        with self._lock:
            try:
                raw_data = processed_data.raw_data

                # 1. Check cutting state
                if raw_data.testere_durumu != 3:  # Not cutting
                    if self.is_cutting:
                        self._reset_cutting_state()
                    return None

                # Mark as cutting
                if not self.is_cutting:
                    self.is_cutting = True
                    logger.info("Cutting started - ML controller activated")

                # 2. Check update interval (rate limiting)
                if not self._should_update():
                    return None

                # 3. Record ML activation time (first iteration)
                if self.ml_activation_time is None:
                    self.ml_activation_time = asyncio.get_event_loop().time()
                    logger.info(
                        f"ML control activated. "
                        f"Torque Guard will activate after {self.tg_activation_delay:.1f}s"
                    )

                # 4. Add data to preprocessor buffers
                if not self.preprocessor.add_data_point(raw_data):
                    logger.error("Failed to add data to preprocessor")
                    return None

                # Wait for buffers to fill
                if not self.preprocessor.is_ready():
                    logger.debug("Preprocessor buffers not ready yet")
                    return None

                # 5. Check Torque Guard (highest priority)
                if self.torque_guard_enabled:
                    torque_guard_command = self._check_and_apply_torque_guard(raw_data)
                    if torque_guard_command:
                        return torque_guard_command

                # 6. Normal ML prediction
                coefficient = self._predict_coefficient(raw_data)
                if coefficient is None:
                    logger.error("ML prediction failed")
                    self._stats['errors'] += 1
                    return None

                # 7. Calculate new speeds
                speed_changes = self._calculate_new_speeds(
                    coefficient,
                    raw_data.serit_kesme_hizi,
                    raw_data.serit_inme_hizi
                )

                # 8. Accumulate changes in buffers
                self.kesme_hizi_degisim_buffer += speed_changes['kesme_degisim']
                self.inme_hizi_degisim_buffer += speed_changes['inme_degisim']

                logger.debug(
                    f"Speed changes accumulated: "
                    f"kesme={self.kesme_hizi_degisim_buffer:.2f}, "
                    f"inme={self.inme_hizi_degisim_buffer:.2f}"
                )

                # 9. Check if thresholds exceeded
                if self._should_write_to_modbus():
                    command = ControlCommand(
                        timestamp=datetime.now(),
                        kesme_hizi_target=speed_changes['kesme_hizi'],
                        inme_hizi_target=speed_changes['inme_hizi'],
                        source="ml"
                    )

                    # Reset accumulators
                    self.kesme_hizi_degisim_buffer = 0.0
                    self.inme_hizi_degisim_buffer = 0.0
                    self._stats['speed_commands_sent'] += 1

                    logger.info(
                        f"Speed command: "
                        f"kesme={command.kesme_hizi_target:.1f}, "
                        f"inme={command.inme_hizi_target:.1f}"
                    )

                    return command

                return None

            except Exception as e:
                logger.error(f"Error in ML control loop: {e}", exc_info=True)
                self._stats['errors'] += 1
                return None

    def _predict_coefficient(self, raw_data) -> Optional[float]:
        """
        ML model inference.

        Process:
        1. Get averaged features from preprocessor
        2. Load ML model
        3. Predict coefficient
        4. Clamp to [-1, 1]
        5. Apply global KATSAYI
        6. Log to database (with torque and head height)

        Args:
            raw_data: RawSensorData with current sensor readings

        Returns:
            Coefficient in [-1.0, 1.0] range, or None on error
        """
        try:
            # Get model input
            input_df = self.preprocessor.get_model_input()
            if input_df is None:
                return None

            # Load model
            model = self.model_loader.load()

            # Predict
            coefficient = model.predict(input_df)[0]

            # Clamp to valid range
            coefficient = max(-1.0, min(coefficient, 1.0))

            # Apply global multiplier
            coefficient *= self.katsayi

            # Log to database with torque and head height values
            self._log_ml_prediction(
                input_df,
                coefficient,
                raw_data.serit_motor_tork_percentage,
                raw_data.kafa_yuksekligi_mm
            )

            self._stats['predictions'] += 1

            logger.debug(f"ML coefficient: {coefficient:.4f}")

            return coefficient

        except Exception as e:
            logger.error(f"ML prediction error: {e}", exc_info=True)
            return None

    def _calculate_new_speeds(
        self,
        coefficient: float,
        current_kesme: float,
        current_inme: float
    ) -> Dict[str, float]:
        """
        Convert ML coefficient to speed adjustments.

        Logic (from ml_model_analizi.txt):
        1. inme_degisim = coefficient (direct mapping)
        2. Calculate inme percentage change
        3. Apply same percentage to kesme (proportional adjustment)

        Args:
            coefficient: ML output [-1, 1]
            current_kesme: Current cutting speed (mm/min)
            current_inme: Current descent speed (mm/min)

        Returns:
            Dictionary with new speeds and changes
        """
        # Inme speed change (direct from coefficient)
        new_inme = current_inme + coefficient
        new_inme = validate_speed(
            new_inme,
            self.limits['inme_hizi']['min'],
            self.limits['inme_hizi']['max'],
            'inme_hizi'
        )
        inme_degisim = new_inme - current_inme

        # Calculate inme percentage change
        if inme_degisim < 0:
            # Decreasing
            inme_range = current_inme - self.limits['inme_hizi']['min']
        else:
            # Increasing
            inme_range = self.limits['inme_hizi']['max'] - current_inme

        inme_degisim_pct = (
            (abs(inme_degisim) / inme_range * 100) if inme_range > 0 else 0
        )

        # Kesme speed change (proportional to inme change)
        if inme_degisim < 0:
            # Decreasing
            kesme_range = current_kesme - self.limits['kesme_hizi']['min']
            kesme_degisim = -(kesme_range * inme_degisim_pct / 100)
        else:
            # Increasing
            kesme_range = self.limits['kesme_hizi']['max'] - current_kesme
            kesme_degisim = (kesme_range * inme_degisim_pct / 100)

        new_kesme = current_kesme + kesme_degisim
        new_kesme = validate_speed(
            new_kesme,
            self.limits['kesme_hizi']['min'],
            self.limits['kesme_hizi']['max'],
            'kesme_hizi'
        )

        return {
            'kesme_hizi': new_kesme,
            'inme_hizi': new_inme,
            'kesme_degisim': kesme_degisim,
            'inme_degisim': inme_degisim
        }

    def _check_and_apply_torque_guard(
        self,
        raw_data
    ) -> Optional[ControlCommand]:
        """
        Torque Guard: Detect and respond to rapid torque increases.

        Logic (from ml_model_analizi.txt):
        1. Wait 5s after ML activation (stability period)
        2. Skip first 3mm of descent (initial contact phase)
        3. Record (height, torque) history
        4. Look back 3mm in height
        5. Calculate torque increase percentage
        6. If >50% increase: trigger emergency reduction

        Args:
            raw_data: RawSensorData with current readings

        Returns:
            ControlCommand for emergency reduction, or None if not triggered
        """
        if self.torque_guard_triggered:
            # Already triggered, don't check again this cycle
            return None

        # Check activation delay
        if self.ml_activation_time is None:
            return None

        elapsed = asyncio.get_event_loop().time() - self.ml_activation_time
        if elapsed < self.tg_activation_delay:
            # Still waiting for Torque Guard activation delay
            return None

        # Log first activation
        if not self.torque_guard_monitoring_started:
            self.torque_guard_monitoring_started = True
            logger.info(
                f"Torque Guard monitoring started "
                f"({elapsed:.1f}s after ML activation)"
            )

        # Record current (height, torque) pair
        avg_torque = (
            np.mean(list(self.preprocessor.torque_buffer))
            if len(self.preprocessor.torque_buffer) > 0
            else raw_data.serit_motor_tork_percentage
        )

        self.height_torque_buffer.append((
            raw_data.kafa_yuksekligi_mm,
            avg_torque
        ))

        # Skip initial descent phase
        if len(self.height_torque_buffer) < 10:  # Need some history
            return None

        # Find torque at (current_height + lookback_mm)
        lookback_mm = self.tg_height_threshold
        target_height = raw_data.kafa_yuksekligi_mm + lookback_mm

        previous_torque = self._interpolate_torque_at_height(target_height)
        if previous_torque is None:
            return None

        # Calculate torque increase percentage
        torque_increase_pct = (
            ((avg_torque - previous_torque) / previous_torque * 100)
            if previous_torque > 0
            else 0
        )

        logger.debug(
            f"Torque Guard check: "
            f"current={avg_torque:.1f}%, "
            f"previous={previous_torque:.1f}%, "
            f"increase={torque_increase_pct:.1f}%"
        )

        # Check threshold
        if torque_increase_pct > self.tg_torque_threshold:
            logger.warning(
                f"TORQUE GUARD TRIGGERED! "
                f"Torque increase: {torque_increase_pct:.1f}% "
                f"(threshold: {self.tg_torque_threshold}%)"
            )

            self.torque_guard_triggered = True
            self._stats['torque_guard_activations'] += 1

            return self._apply_torque_guard_reduction(raw_data)

        return None

    def _interpolate_torque_at_height(self, target_height: float) -> Optional[float]:
        """
        Interpolate torque value at specific height from history.

        Uses linear interpolation between nearest height samples.

        Args:
            target_height: Height (mm) to find torque at

        Returns:
            Interpolated torque percentage, or None if not enough data
        """
        if len(self.height_torque_buffer) < 2:
            return None

        # Sort by height (ascending)
        sorted_buffer = sorted(self.height_torque_buffer, key=lambda x: x[0])

        # Find bounding samples
        lower = None
        upper = None

        for height, torque in sorted_buffer:
            if height <= target_height:
                lower = (height, torque)
            elif height > target_height:
                upper = (height, torque)
                break

        # Check if we have bounds
        if lower is None or upper is None:
            # Use closest available
            closest = min(sorted_buffer, key=lambda x: abs(x[0] - target_height))
            return closest[1]

        # Linear interpolation
        h1, t1 = lower
        h2, t2 = upper

        if h2 == h1:
            return t1

        interpolated_torque = t1 + (t2 - t1) * (target_height - h1) / (h2 - h1)
        return interpolated_torque

    def _apply_torque_guard_reduction(self, raw_data) -> ControlCommand:
        """
        Apply emergency speed reduction.

        Reduction:
        - Reduce both speeds by configured percentage (default 25%)
        - Apply speed limits
        - Bypass accumulators (immediate write)
        - Reset Torque Guard state

        Args:
            raw_data: RawSensorData with current speeds

        Returns:
            ControlCommand for emergency reduction
        """
        reduction_factor = 1 - (self.tg_reduction_factor / 100)

        new_inme = raw_data.serit_inme_hizi * reduction_factor
        new_kesme = raw_data.serit_kesme_hizi * reduction_factor

        # Apply limits
        new_inme = validate_speed(
            new_inme,
            self.limits['inme_hizi']['min'],
            self.limits['inme_hizi']['max'],
            'inme_hizi'
        )
        new_kesme = validate_speed(
            new_kesme,
            self.limits['kesme_hizi']['min'],
            self.limits['kesme_hizi']['max'],
            'kesme_hizi'
        )

        # Reset Torque Guard state
        self.height_torque_buffer.clear()
        self.kesme_hizi_degisim_buffer = 0.0
        self.inme_hizi_degisim_buffer = 0.0

        logger.warning(
            f"TORQUE GUARD REDUCTION: "
            f"kesme {raw_data.serit_kesme_hizi:.1f} → {new_kesme:.1f}, "
            f"inme {raw_data.serit_inme_hizi:.1f} → {new_inme:.1f}"
        )

        return ControlCommand(
            timestamp=datetime.now(),
            kesme_hizi_target=new_kesme,
            inme_hizi_target=new_inme,
            source="torque_guard"
        )

    def _should_update(self) -> bool:
        """
        Check if enough time elapsed since last update (rate limiting).

        Returns:
            True if update allowed, False otherwise
        """
        now = asyncio.get_event_loop().time()

        if self.last_update_time is None:
            self.last_update_time = now
            return True

        elapsed = now - self.last_update_time

        if elapsed >= self.min_update_interval:
            self.last_update_time = now
            return True

        return False

    def _should_write_to_modbus(self) -> bool:
        """
        Check if accumulated changes exceed write thresholds.

        If threshold is disabled for a speed, always returns True for that speed.
        If threshold is enabled, checks if accumulated change exceeds threshold.

        Thresholds:
        - inme: >= 1.0 (default) if enabled
        - kesme: >= 0.9 (default) if enabled

        Returns:
            True if should write, False otherwise
        """
        # If inme threshold disabled, always write when there's any change
        inme_should_write = (
            not self.inme_threshold_enabled or
            abs(self.inme_hizi_degisim_buffer) >= self.inme_threshold
        )

        # If kesme threshold disabled, always write when there's any change
        kesme_should_write = (
            not self.kesme_threshold_enabled or
            abs(self.kesme_hizi_degisim_buffer) >= self.kesme_threshold
        )

        # Write if either speed needs writing
        return inme_should_write or kesme_should_write

    def _reset_cutting_state(self):
        """
        Reset all state when cutting stops.
        """
        self.is_cutting = False
        self.ml_activation_time = None
        self.torque_guard_triggered = False
        self.torque_guard_monitoring_started = False
        self.height_torque_buffer.clear()
        self.kesme_hizi_degisim_buffer = 0.0
        self.inme_hizi_degisim_buffer = 0.0
        self.preprocessor.reset_buffers()

        logger.info("Cutting stopped - ML state reset")

    def _log_ml_prediction(
        self,
        input_df,
        coefficient: float,
        serit_motor_tork: float,
        kafa_yuksekligi: float
    ):
        """
        Log ML prediction to database for analysis.

        Args:
            input_df: Input DataFrame with features
            coefficient: Predicted coefficient
            serit_motor_tork: Band motor torque percentage at prediction time
            kafa_yuksekligi: Head height in mm at prediction time
        """
        try:
            sql = """
                INSERT INTO ml_predictions (
                    timestamp,
                    akim_input,
                    sapma_input,
                    kesme_hizi_input,
                    inme_hizi_input,
                    serit_motor_tork,
                    kafa_yuksekligi,
                    ml_output
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                datetime.now().isoformat(),
                float(input_df['akim_input'].iloc[0]),
                float(input_df['sapma_input'].iloc[0]),
                float(input_df['kesme_hizi'].iloc[0]),
                float(input_df['inme_hizi'].iloc[0]),
                float(serit_motor_tork),
                float(kafa_yuksekligi),
                float(coefficient)
            )

            self.db.write_async(sql, params)

        except Exception as e:
            logger.error(f"Error logging ML prediction: {e}")

    def get_stats(self) -> Dict:
        """
        Get controller statistics.

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                **self._stats,
                'is_cutting': self.is_cutting,
                'torque_guard_active': self.torque_guard_triggered,
                'preprocessor_status': self.preprocessor.get_buffer_status(),
                'accumulated_kesme': self.kesme_hizi_degisim_buffer,
                'accumulated_inme': self.inme_hizi_degisim_buffer
            }
