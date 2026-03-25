"""
RT-DETR broken-tooth and crack detection worker.

Runs as a daemon thread. Loads two RT-DETR models (broken tooth + crack)
inside ``run()`` so that ``import detection_worker`` never triggers heavy
ML library imports. Results are published to CameraResultsStore.

Class mapping:
    Broken model — class 0: tooth (healthy), class 1: broken
    Crack model  — class 0: crack
"""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.services.camera.camera_service import CameraService
    from src.services.camera.results_store import CameraResultsStore

logger = logging.getLogger(__name__)


class DetectionWorker(threading.Thread):
    """Daemon thread that runs sequential broken + crack inference on live frames.

    Constructor does no heavy work — model loading happens inside ``run()``.
    """

    def __init__(
        self,
        config: dict,
        results_store: CameraResultsStore,
        camera_service: CameraService,
        db_service=None,
    ) -> None:
        """Initialise the detection worker thread.

        Args:
            config: Camera config dict containing ``detection`` sub-section with
                keys: enabled, interval_seconds, confidence_threshold,
                broken_model_path, crack_model_path.
            results_store: Shared store where detection results are published.
            camera_service: Source of live frames via ``get_current_frame()``.
            db_service: Optional SQLiteService instance for persisting detection
                events to ``camera.db``. Defaults to None (no DB writes).
        """
        super().__init__(daemon=True, name="detection-worker")

        det_cfg = config.get("detection", {})
        self._enabled: bool = det_cfg.get("enabled", False)
        self._interval: float = float(det_cfg.get("interval_seconds", 2.0))
        self._confidence: float = float(det_cfg.get("confidence_threshold", 0.5))
        self._broken_model_path: str = det_cfg.get(
            "broken_model_path", "data/models/best.pt"
        )
        self._crack_model_path: str = det_cfg.get(
            "crack_model_path", "data/models/catlak-best.pt"
        )

        self._results_store = results_store
        self._camera_service = camera_service
        self._db_service = db_service

        self._stop_event = threading.Event()
        self._model_load_failed: bool = False

    # -- lifecycle ---------------------------------------------------------

    def run(self) -> None:  # noqa: C901
        """Load models and enter detection loop.

        torch and ultralytics are imported here — not at module level — so
        importing this module stays lightweight.
        """
        import torch
        from ultralytics import RTDETR

        device = "cuda" if torch.cuda.is_available() else "cpu"

        # --- load broken-tooth model ---
        try:
            broken_model = RTDETR(self._broken_model_path)
            broken_model.to(device)
            logger.info(
                "Broken detection model loaded — path=%s, device=%s",
                self._broken_model_path,
                device,
            )
        except Exception:
            logger.error(
                "Failed to load broken detection model — path=%s",
                self._broken_model_path,
                exc_info=True,
            )
            self._model_load_failed = True
            return

        if self._stop_event.is_set():
            return

        # --- load crack model ---
        try:
            crack_model = RTDETR(self._crack_model_path)
            crack_model.to(device)
            logger.info(
                "Crack detection model loaded — path=%s, device=%s",
                self._crack_model_path,
                device,
            )
        except Exception:
            logger.error(
                "Failed to load crack detection model — path=%s",
                self._crack_model_path,
                exc_info=True,
            )
            self._model_load_failed = True
            return

        if self._stop_event.is_set():
            return

        logger.info(
            "DetectionWorker ready — device=%s, interval=%.1fs, confidence=%.2f",
            device,
            self._interval,
            self._confidence,
        )

        # --- main loop ---
        while not self._stop_event.is_set():
            frame = self._camera_service.get_current_frame()
            if frame is None:
                self._stop_event.wait(self._interval)
                continue

            # Copy frame so we don't hold camera_service's frame_lock during inference
            frame = frame.copy()

            # -- broken detection --
            tooth_count = 0
            broken_count = 0
            broken_confidence = 0.0

            with torch.no_grad():
                broken_results = broken_model.predict(
                    source=frame,
                    device=device,
                    conf=self._confidence,
                    imgsz=960,
                    verbose=False,
                )

            for result in broken_results:
                for box in result.boxes:
                    class_id = int(box.cls[0].item())
                    conf = box.conf[0].item()
                    if class_id == 0:
                        tooth_count += 1
                    elif class_id == 1:
                        broken_count += 1
                        if conf > broken_confidence:
                            broken_confidence = conf

            # -- crack detection --
            crack_count = 0
            crack_confidence = 0.0

            with torch.no_grad():
                crack_results = crack_model.predict(
                    source=frame,
                    device=device,
                    conf=self._confidence,
                    imgsz=960,
                    verbose=False,
                )

            for result in crack_results:
                for box in result.boxes:
                    class_id = int(box.cls[0].item())
                    conf = box.conf[0].item()
                    if class_id == 0:
                        crack_count += 1
                        if conf > crack_confidence:
                            crack_confidence = conf

            # -- save annotated frame if recording --
            self._save_annotated_frame(
                frame, broken_results, crack_results
            )

            # -- publish results --
            now = datetime.now().isoformat()
            self._results_store.update_batch(
                {
                    "broken_count": broken_count,
                    "broken_confidence": broken_confidence,
                    "tooth_count": tooth_count,
                    "crack_count": crack_count,
                    "crack_confidence": crack_confidence,
                    "last_detection_ts": now,
                }
            )

            # -- persist to camera.db --
            if self._db_service:
                if broken_count > 0:
                    ok = self._db_service.write_async(
                        "INSERT INTO detection_events "
                        "(timestamp, event_type, confidence, count, image_path, "
                        "kesim_id, makine_id, serit_id, malzeme_cinsi) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (now, "broken_tooth", broken_confidence, broken_count,
                         None, None, None, None, None),
                    )
                    if not ok:
                        logger.warning("DB write failed — broken_tooth event dropped")
                if crack_count > 0:
                    ok = self._db_service.write_async(
                        "INSERT INTO detection_events "
                        "(timestamp, event_type, confidence, count, image_path, "
                        "kesim_id, makine_id, serit_id, malzeme_cinsi) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (now, "crack", crack_confidence, crack_count,
                         None, None, None, None, None),
                    )
                    if not ok:
                        logger.warning("DB write failed — crack event dropped")

            logger.debug(
                "Detection cycle — broken=%d, tooth=%d, crack=%d",
                broken_count,
                tooth_count,
                crack_count,
            )

            self._stop_event.wait(self._interval)

    def stop(self) -> None:
        """Signal the worker to exit after the current cycle."""
        self._stop_event.set()

    @property
    def model_load_failed(self) -> bool:
        """True if either model failed to load during ``run()``."""
        return self._model_load_failed

    # -- internal ----------------------------------------------------------

    def _save_annotated_frame(
        self, frame: Any, broken_results: list, crack_results: list
    ) -> None:
        """Optionally save annotated frame to a ``detected/`` subdirectory.

        Only writes when a recording is active (recording_path is set in the
        results store). Silently skips on any error — this is best-effort.
        """
        import cv2

        recording_path = self._results_store.get("recording_path")
        if not recording_path:
            return

        detected_dir = os.path.join(recording_path, "detected")
        try:
            os.makedirs(detected_dir, exist_ok=True)
        except OSError:
            return

        # Draw bounding boxes on a copy
        annotated = frame.copy()

        for result in broken_results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                class_id = int(box.cls[0].item())
                conf = box.conf[0].item()
                if class_id == 1:  # broken
                    color = (0, 0, 255)  # red
                    label = f"broken ({conf:.2f})"
                else:
                    color = (0, 255, 0)  # green
                    label = f"tooth ({conf:.2f})"
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    annotated,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2,
                )

        for result in crack_results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0].item()
                label = f"crack ({conf:.2f})"
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 0, 0), 2)  # blue
                cv2.putText(
                    annotated,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 0, 0),
                    2,
                )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out_path = os.path.join(detected_dir, f"det_{ts}.jpg")
        try:
            cv2.imwrite(out_path, annotated)
        except Exception:
            logger.debug("Failed to save annotated frame — path=%s", out_path)
