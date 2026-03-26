"""
VisionService — recording orchestration daemon thread.

Polls CameraResultsStore for testere_durumu at a configurable interval.
On CUTTING(3) → non-CUTTING transition, triggers start_recording() on
CameraService. After recording_duration seconds, calls stop_recording().

Follows the same daemon thread pattern as DetectionWorker and LDCWorker:
- daemon=True, name="vision-service"
- threading.Event() for stop signaling
- Exception isolation: polling errors are logged, thread continues
- No asyncio event loop involvement — pure threading
"""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.camera.camera_service import CameraService
    from src.services.camera.results_store import CameraResultsStore

logger = logging.getLogger(__name__)


class VisionService(threading.Thread):
    """Daemon thread that orchestrates recording triggers based on testere_durumu.

    Polls CameraResultsStore for testere_durumu at ``polling_interval`` Hz.
    Detects CUTTING(3) → non-CUTTING transitions and calls
    CameraService.start_recording(). Stops recording after ``recording_duration``
    seconds via CameraService.stop_recording().

    Constructor does no heavy work — safe to instantiate without camera hardware.
    """

    def __init__(
        self,
        config: dict,
        results_store: "CameraResultsStore",
        camera_service: "CameraService",
    ) -> None:
        """Initialise VisionService.

        Args:
            config: Full camera config dict. Reads ``vision.polling_interval``
                (default 0.5s) and ``vision.recording_duration`` (default 10s).
            results_store: Shared CameraResultsStore where testere_durumu and
                traceability fields are published by DataProcessingPipeline.
            camera_service: CameraService instance to call start/stop recording.
        """
        super().__init__(daemon=True, name="vision-service")

        vision_cfg = config.get("vision", {})
        self._polling_interval: float = float(
            vision_cfg.get("polling_interval", 0.5)
        )
        self._recording_duration: float = float(
            vision_cfg.get("recording_duration", 10.0)
        )

        self._results_store = results_store
        self._camera_service = camera_service

        self._stop_event = threading.Event()
        self._prev_testere_durumu: int = 0
        self._is_recording: bool = False
        self._recording_start_time: float = 0.0

    # -- lifecycle ----------------------------------------------------------

    def run(self) -> None:
        """Main polling loop.

        Runs until stop() is called. All exceptions are caught and logged so
        the thread never dies due to a transient error (D-07).
        """
        logger.info(
            "VisionService started — polling_interval=%.2fs, recording_duration=%.1fs",
            self._polling_interval,
            self._recording_duration,
        )

        while not self._stop_event.is_set():
            self._poll_once()
            self._stop_event.wait(self._polling_interval)

        logger.info("VisionService stopped")

    def stop(self) -> None:
        """Signal the thread to exit after the current poll cycle."""
        self._stop_event.set()

    # -- internal -----------------------------------------------------------

    def _poll_once(self) -> None:
        """Execute one poll cycle.

        Reads testere_durumu from store, detects transition, triggers recording.
        All exceptions are caught so the thread survives transient errors (D-07).
        """
        try:
            curr = self._results_store.get("testere_durumu", 0)

            # Detect CUTTING(3) -> non-CUTTING transition (per D-03)
            if self._prev_testere_durumu == 3 and curr != 3 and not self._is_recording:
                if self._camera_service.start_recording():
                    self._is_recording = True
                    self._recording_start_time = time.monotonic()
                    logger.info(
                        "VisionService: recording started on cutting-end transition "
                        "(prev=%d, curr=%d)",
                        self._prev_testere_durumu,
                        curr,
                    )

            # Stop recording after duration elapsed (per D-03, recording_duration)
            if self._is_recording:
                elapsed = time.monotonic() - self._recording_start_time
                if elapsed >= self._recording_duration:
                    self._camera_service.stop_recording()
                    self._is_recording = False
                    logger.info(
                        "VisionService: recording stopped after %.1fs", elapsed
                    )

            self._prev_testere_durumu = curr

        except Exception:
            logger.warning(
                "VisionService polling error — continuing", exc_info=True
            )
