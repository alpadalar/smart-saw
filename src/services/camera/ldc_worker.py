"""
LDC edge detection and wear measurement worker.

Runs as a daemon thread. Loads the LDC model (modelB4 architecture +
BIPED checkpoint) inside ``run()`` so that ``import ldc_worker`` never
triggers heavy ML library imports. After each inference cycle, computes
saw blade wear percentage via contour analysis and recalculates overall
health using HealthCalculator. Results are published to CameraResultsStore.
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.camera.camera_service import CameraService
    from src.services.camera.results_store import CameraResultsStore

logger = logging.getLogger(__name__)

# Wear ROI constants (matching old VisionService)
TOP_LINE_Y = 170
BOTTOM_LINE_Y = 236

# Normalized bounding box for ROI extraction
_ROI_X_CENTER_N = 0.500000
_ROI_Y_CENTER_N = 0.530692
_ROI_WIDTH_N = 0.736888
_ROI_HEIGHT_N = 0.489510

# BGR mean for LDC preprocessing
_BGR_MEAN = [103.939, 116.779, 123.68]


class LDCWorker(threading.Thread):
    """Daemon thread that runs LDC edge detection and wear measurement.

    Constructor does no heavy work — model loading happens inside ``run()``.
    """

    def __init__(
        self,
        config: dict,
        results_store: CameraResultsStore,
        camera_service: CameraService,
        db_service=None,
    ) -> None:
        super().__init__(daemon=True, name="ldc-worker")

        wear_cfg = config.get("wear", {})
        self._enabled: bool = wear_cfg.get("enabled", False)
        self._interval: float = float(wear_cfg.get("interval_seconds", 5.0))
        self._checkpoint_path: str = wear_cfg.get(
            "ldc_checkpoint_path", "data/models/ldc/16_model.pth"
        )

        self._results_store = results_store
        self._camera_service = camera_service
        self._db_service = db_service

        self._stop_event = threading.Event()
        self._model_load_failed: bool = False

    # -- lifecycle ---------------------------------------------------------

    def run(self) -> None:  # noqa: C901
        """Load LDC model and enter wear-measurement loop.

        torch, cv2, and numpy are imported here — not at module level — so
        importing this module stays lightweight.
        """
        import numpy as np
        import torch

        import cv2

        from src.services.camera.health_calculator import HealthCalculator
        from src.services.camera.modelB4 import LDC

        health_calc = HealthCalculator()
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # --- load LDC model ---
        model = LDC().to(device)

        if not os.path.isfile(self._checkpoint_path):
            logger.error(
                "LDC checkpoint not found — path=%s", self._checkpoint_path
            )
            self._model_load_failed = True
            return

        try:
            state = torch.load(self._checkpoint_path, map_location=device)
            model.load_state_dict(state)
            model.eval()
            logger.info(
                "LDC model loaded — checkpoint=%s, device=%s",
                self._checkpoint_path,
                device,
            )
        except Exception:
            logger.error(
                "Failed to load LDC checkpoint — path=%s",
                self._checkpoint_path,
                exc_info=True,
            )
            self._model_load_failed = True
            return

        if self._stop_event.is_set():
            return

        # --- main loop ---
        while not self._stop_event.is_set():
            frame = self._camera_service.get_current_frame()
            if frame is None:
                self._stop_event.wait(self._interval)
                continue

            frame = frame.copy()

            # -- LDC inference --
            edge_bgr = self._run_ldc_inference(
                model, frame, device, torch, np, cv2
            )

            # -- wear calculation --
            wear_percentage = self._compute_wear(edge_bgr, np, cv2)

            # -- publish results and recalculate health --
            now = datetime.now().isoformat()
            updates: dict = {"last_wear_ts": now}

            if wear_percentage is not None:
                updates["wear_percentage"] = wear_percentage

            # Read current detection state for health calc
            tooth_count = self._results_store.get("tooth_count", 0)
            broken_count = self._results_store.get("broken_count", 0)
            effective_wear = (
                wear_percentage if wear_percentage is not None else 0.0
            )

            health_score = health_calc.calculate_saw_health(
                tooth_count, broken_count, effective_wear
            )
            health_status = health_calc.get_health_status(health_score)
            health_color = health_calc.get_health_color(health_score)

            updates["health_score"] = health_score
            updates["health_status"] = health_status
            updates["health_color"] = health_color

            self._results_store.update_batch(updates)

            # -- persist to camera.db --
            if self._db_service and wear_percentage is not None:
                ok = self._db_service.write_async(
                    "INSERT INTO wear_history "
                    "(timestamp, wear_percentage, health_score, edge_pixel_count, "
                    "image_path, kesim_id, makine_id, serit_id, malzeme_cinsi) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (now, wear_percentage, health_score, None,
                     None, None, None, None, None),
                )
                if not ok:
                    logger.warning("DB write failed — wear_history event dropped")

            logger.debug(
                "Wear cycle — wear=%.2f%%, health=%.2f%%",
                wear_percentage if wear_percentage is not None else -1.0,
                health_score,
            )

            self._stop_event.wait(self._interval)

    def stop(self) -> None:
        """Signal the worker to exit after the current cycle."""
        self._stop_event.set()

    @property
    def model_load_failed(self) -> bool:
        """True if the LDC model failed to load during ``run()``."""
        return self._model_load_failed

    # -- internal ----------------------------------------------------------

    @staticmethod
    def _run_ldc_inference(model, frame, device, torch, np, cv2):
        """Run LDC forward pass and return edge BGR image.

        Preprocessing matches old VisionService._run_ldc_on_image:
        resize 512x512, subtract BGR mean, CHW float32, sigmoid → normalize
        → uint8 → bitwise_not → resize → binarize.
        """
        h, w = frame.shape[:2]

        # Preprocess
        resized = cv2.resize(frame, (512, 512))
        img = resized.astype(np.float32)
        img -= np.array(_BGR_MEAN, dtype=np.float32)
        img = img.transpose(2, 0, 1)
        tensor = torch.from_numpy(img).unsqueeze(0).to(device)

        # Forward pass
        with torch.no_grad():
            outputs = model(tensor)

            if isinstance(outputs, torch.Tensor):
                maps = [outputs]
            else:
                maps = list(outputs)

            # Process each map: sigmoid → normalize → uint8 → invert → resize
            preds_uint8 = []
            for m in maps:
                m = torch.sigmoid(m).cpu().detach().numpy()
                m = np.squeeze(m)
                m = (m - m.min()) / (m.max() - m.min() + 1e-8)
                m = (m * 255.0).astype(np.uint8)
                m = cv2.bitwise_not(m)
                m = cv2.resize(m, (w, h))
                preds_uint8.append(m)

            # Use fused output (last element) for sharpest edges
            fused = preds_uint8[-1]

        # Binarize: invert → threshold at 180 → invert back
        edge_gray = fused
        inv = cv2.bitwise_not(edge_gray)
        _, binary = cv2.threshold(inv, 180, 255, cv2.THRESH_BINARY)
        edge_gray = cv2.bitwise_not(binary)

        edge_bgr = cv2.cvtColor(edge_gray, cv2.COLOR_GRAY2BGR)
        return edge_bgr

    @staticmethod
    def _compute_wear(edge_bgr, np, cv2):
        """Compute saw blade wear percentage from LDC edge image.

        Returns wear percentage (0-100) or None if insufficient contour data.
        Matches old VisionService._compute_wear logic.
        """
        if edge_bgr is None:
            return None

        image_height, image_width = edge_bgr.shape[:2]

        # Calculate ROI pixel coordinates from normalized bbox
        x_center = int(_ROI_X_CENTER_N * image_width)
        box_w = int(_ROI_WIDTH_N * image_width)

        x1 = int(x_center - box_w / 2)
        x2 = int(x_center + box_w / 2)
        y1 = TOP_LINE_Y
        y2 = BOTTOM_LINE_Y

        # Clamp to image bounds
        x1 = max(0, min(x1, image_width - 1))
        x2 = max(0, min(x2, image_width))
        y1 = max(0, min(y1, image_height - 1))
        y2 = max(0, min(y2, image_height))

        if y2 <= y1 or x2 <= x1:
            return None

        roi = edge_bgr[y1:y2, x1:x2]
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Adaptive threshold: if mean < 90 use THRESH_BINARY at 180,
        # else THRESH_BINARY_INV at 128
        mean_val = float(gray_roi.mean())
        if mean_val < 90:
            _, binary_roi = cv2.threshold(
                gray_roi, 180, 255, cv2.THRESH_BINARY
            )
        else:
            _, binary_roi = cv2.threshold(
                gray_roi, 128, 255, cv2.THRESH_BINARY_INV
            )

        contours, _ = cv2.findContours(
            binary_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None

        # Collect Y coordinates from all contour points
        ys = [pt[0][1] for c in contours for pt in c]
        if len(ys) < 5:
            return None

        ys = np.array(ys, dtype=np.int32)

        # Top 10% of Y values (smallest = highest in image)
        k = max(5, int(0.10 * ys.size))
        k = min(k, 50)
        smallest = np.partition(ys, k)[:k]
        min_y = int(np.mean(smallest))

        wear_y = min_y + y1
        band_h = max(1, BOTTOM_LINE_Y - TOP_LINE_Y)
        percent = ((wear_y - TOP_LINE_Y) / band_h) * 100.0
        percent = float(np.clip(percent, 0.0, 100.0))

        return percent
