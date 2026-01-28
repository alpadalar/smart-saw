"""
ML data preprocessing with buffer management and feature engineering.

This module handles:
- Sensor data buffering (noise reduction via averaging)
- Torque-to-current conversion using polynomial model
- Feature preparation for ML model input
"""

import logging
import numpy as np
import pandas as pd
from collections import deque
from typing import Optional, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MLPreprocessor:
    """
    Prepares sensor data for ML model inference.

    Features:
    - Buffer-based averaging (10 samples for standard features)
    - Extended torque buffering (50 samples)
    - Polynomial torque-to-current conversion
    - Feature order enforcement for model compatibility

    CRITICAL: Feature order must match training data:
    ['akim_input', 'sapma_input', 'kesme_hizi', 'inme_hizi']
    """

    def __init__(self, config: dict):
        """
        Initialize preprocessor with configuration.

        Args:
            config: ML configuration dictionary with buffer sizes and coefficients
        """
        self.config = config

        # Standard feature buffers (10 samples)
        buffer_size = config.get('buffer_size', 10)
        self.akim_buffer = deque(maxlen=buffer_size)
        self.sapma_buffer = deque(maxlen=buffer_size)
        self.kesme_hizi_buffer = deque(maxlen=buffer_size)
        self.inme_hizi_buffer = deque(maxlen=buffer_size)

        # Extended torque buffer (50 samples for smoother conversion)
        torque_buffer_size = config.get('torque_buffer_size', 50)
        self.torque_buffer = deque(maxlen=torque_buffer_size)

        # Polynomial coefficients for torque → current conversion
        # f(x) = A2*x^2 + A1*x + A0
        self.poly_a2 = config.get('torque_to_current', {}).get('a2', 0.0001)
        self.poly_a1 = config.get('torque_to_current', {}).get('a1', 0.285)
        self.poly_a0 = config.get('torque_to_current', {}).get('a0', 8.5)

        # Statistics
        self._samples_processed = 0
        self._last_update_time: Optional[datetime] = None

        logger.info(
            f"MLPreprocessor initialized: "
            f"buffer_size={buffer_size}, "
            f"torque_buffer_size={torque_buffer_size}"
        )

    def torque_to_current(self, torque_percentage: float) -> float:
        """
        Convert motor torque percentage to current using polynomial model.

        Model: f(x) = A2*x^2 + A1*x + A0
        Coefficients calibrated from motor datasheet and field measurements.

        Note: No clamping applied to match old codebase behavior.
        The polynomial handles any input value.

        Args:
            torque_percentage: Motor torque as percentage (typically 0-100)

        Returns:
            Estimated current in Amperes
        """
        try:
            # Apply polynomial (no clamping - matches old code)
            current = (
                self.poly_a2 * (torque_percentage ** 2) +
                self.poly_a1 * torque_percentage +
                self.poly_a0
            )
            return current
        except Exception:
            return 0.0

    def add_data_point(self, raw_data) -> bool:
        """
        Add new sensor data point to buffers.

        Process:
        1. Add torque to torque buffer
        2. Calculate average torque from buffer
        3. Convert average torque to current
        4. Add current to akim buffer
        5. Add other features to respective buffers

        Args:
            raw_data: RawSensorData instance with sensor readings

        Returns:
            True if data added successfully, False otherwise
        """
        try:
            # Add torque to extended buffer
            self.torque_buffer.append(raw_data.serit_motor_tork_percentage)

            # Calculate average torque from buffer
            if len(self.torque_buffer) > 0:
                avg_torque = np.mean(list(self.torque_buffer))
            else:
                avg_torque = raw_data.serit_motor_tork_percentage

            # Convert average torque to current
            estimated_current = self.torque_to_current(avg_torque)

            # Add to feature buffers
            self.akim_buffer.append(estimated_current)
            self.sapma_buffer.append(raw_data.serit_sapmasi)
            self.kesme_hizi_buffer.append(raw_data.serit_kesme_hizi)
            self.inme_hizi_buffer.append(raw_data.serit_inme_hizi)

            # Update statistics
            self._samples_processed += 1
            self._last_update_time = datetime.now()

            return True

        except Exception as e:
            logger.error(f"Error adding data point: {e}", exc_info=True)
            return False

    def get_model_input(self) -> Optional[pd.DataFrame]:
        """
        Get averaged feature values as model input.

        CRITICAL: Feature order MUST match training data:
        ['akim_input', 'sapma_input', 'kesme_hizi', 'inme_hizi']

        Returns:
            pandas DataFrame with single row of averaged features,
            or None if buffers not filled

        Example:
            >>> df = preprocessor.get_model_input()
            >>> df.columns.tolist()
            ['akim_input', 'sapma_input', 'kesme_hizi', 'inme_hizi']
        """
        # Check if buffers have sufficient data
        min_samples = min(
            len(self.akim_buffer),
            len(self.sapma_buffer),
            len(self.kesme_hizi_buffer),
            len(self.inme_hizi_buffer)
        )

        if min_samples == 0:
            logger.warning("Buffers empty, cannot generate model input")
            return None

        try:
            # Calculate averages from each buffer
            akim_avg = np.mean(list(self.akim_buffer))
            sapma_avg = np.mean(list(self.sapma_buffer))
            kesme_avg = np.mean(list(self.kesme_hizi_buffer))
            inme_avg = np.mean(list(self.inme_hizi_buffer))

            # Create DataFrame with EXACT feature order from training
            input_df = pd.DataFrame({
                'akim_input': [akim_avg],
                'sapma_input': [sapma_avg],
                'kesme_hizi': [kesme_avg],
                'inme_hizi': [inme_avg]
            })

            logger.debug(
                f"Model input prepared: "
                f"akim={akim_avg:.2f}, "
                f"sapma={sapma_avg:.3f}, "
                f"kesme={kesme_avg:.1f}, "
                f"inme={inme_avg:.1f}"
            )

            return input_df

        except Exception as e:
            logger.error(f"Error generating model input: {e}", exc_info=True)
            return None

    def get_averaged_speeds(self) -> Tuple[float, float]:
        """
        Get averaged speed values from buffers.

        This matches old codebase behavior where speed calculations
        use averaged values, not raw current values.

        Returns:
            Tuple of (avg_kesme_hizi, avg_inme_hizi), or (0.0, 0.0) if buffers empty
        """
        if len(self.kesme_hizi_buffer) == 0 or len(self.inme_hizi_buffer) == 0:
            return (0.0, 0.0)

        avg_kesme = np.mean(list(self.kesme_hizi_buffer))
        avg_inme = np.mean(list(self.inme_hizi_buffer))

        return (avg_kesme, avg_inme)

    def reset_buffers(self):
        """
        Clear all buffers (called when cutting stops).
        """
        self.akim_buffer.clear()
        self.sapma_buffer.clear()
        self.kesme_hizi_buffer.clear()
        self.inme_hizi_buffer.clear()
        self.torque_buffer.clear()

        logger.debug("Preprocessor buffers reset")

    def get_buffer_status(self) -> Dict:
        """
        Get buffer fill status for monitoring.

        Returns:
            Dictionary with buffer lengths and statistics
        """
        return {
            'akim_buffer_len': len(self.akim_buffer),
            'sapma_buffer_len': len(self.sapma_buffer),
            'kesme_buffer_len': len(self.kesme_hizi_buffer),
            'inme_buffer_len': len(self.inme_hizi_buffer),
            'torque_buffer_len': len(self.torque_buffer),
            'samples_processed': self._samples_processed,
            'last_update': self._last_update_time.isoformat() if self._last_update_time else None
        }

    def is_ready(self) -> bool:
        """
        Check if preprocessor has any data for prediction.

        Returns:
            True if all buffers have at least 1 sample (like old project behavior)
        """
        # Match old project behavior: proceed with even 1 sample
        return (
            len(self.akim_buffer) >= 1 and
            len(self.sapma_buffer) >= 1 and
            len(self.kesme_hizi_buffer) >= 1 and
            len(self.inme_hizi_buffer) >= 1
        )
