"""
ML model loading and caching (thread-safe).
"""

import threading
import logging
from pathlib import Path
from typing import Optional
import joblib

logger = logging.getLogger(__name__)


class MLModelLoader:
    """Thread-safe ML model loader."""

    def __init__(self, model_path: Path):
        """
        Initialize model loader.

        Args:
            model_path: Path to joblib model file
        """
        self.model_path = model_path
        self._model = None
        self._lock = threading.RLock()

    def load(self):
        """
        Load and cache ML model.

        Returns:
            Loaded model instance

        Raises:
            FileNotFoundError: If model file doesn't exist
            Exception: If model loading fails
        """
        with self._lock:
            if self._model is None:
                if not self.model_path.exists():
                    raise FileNotFoundError(
                        f"ML model not found: {self.model_path}\n"
                        f"Please copy model file to: {self.model_path}"
                    )

                try:
                    self._model = joblib.load(self.model_path)
                    logger.info(f"ML model loaded: {self.model_path}")
                except Exception as e:
                    logger.error(f"Failed to load ML model: {e}", exc_info=True)
                    raise

            return self._model

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        with self._lock:
            return self._model is not None
