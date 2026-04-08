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

        # Wear ROI parameters (D-06: migrated from module-level constants to config)
        self._top_line_y: int = int(wear_cfg.get("top_line_y", 170))
        self._bottom_line_y: int = int(wear_cfg.get("bottom_line_y", 236))
        self._roi_x_center_n: float = float(wear_cfg.get("roi_x_center_n", 0.500000))
        self._roi_y_center_n: float = float(wear_cfg.get("roi_y_center_n", 0.530692))
        self._roi_width_n: float = float(wear_cfg.get("roi_width_n", 0.736888))
        self._roi_height_n: float = float(wear_cfg.get("roi_height_n", 0.489510))
        self._bgr_mean: list = wear_cfg.get("bgr_mean", [103.939, 116.779, 123.68])

        # Health calculator weights (from camera.health config)
        health_cfg = config.get("health", {})
        self._broken_weight: float = float(health_cfg.get("broken_weight", 0.7))
        self._wear_weight: float = float(health_cfg.get("wear_weight", 0.3))

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

        health_calc = HealthCalculator(
            broken_weight=self._broken_weight,
            wear_weight=self._wear_weight,
        )
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
            wear_percentage, edge_pixel_count = self._compute_wear(edge_bgr, np, cv2)

            # -- save edge image if recording is active (per D-06) --
            image_path = None
            recording_path = self._results_store.get("recording_path")
            if recording_path and edge_bgr is not None:
                ldc_dir = os.path.join(recording_path, "ldc")
                try:
                    os.makedirs(ldc_dir, exist_ok=True)
                    ts_img = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    ldc_path = os.path.join(ldc_dir, f"ldc_{ts_img}.jpg")
                    cv2.imwrite(ldc_path, edge_bgr)
                    image_path = ldc_path
                except Exception:
                    logger.debug("Failed to save LDC edge image — path=%s", ldc_dir)

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
                # Read traceability fields from CameraResultsStore (per D-05)
                kesim_id = self._results_store.get("kesim_id")
                makine_id = self._results_store.get("makine_id")
                serit_id = self._results_store.get("serit_id")
                malzeme_cinsi = self._results_store.get("malzeme_cinsi")

                ok = self._db_service.write_async(
                    "INSERT INTO wear_history "
                    "(timestamp, wear_percentage, health_score, edge_pixel_count, "
                    "image_path, kesim_id, makine_id, serit_id, malzeme_cinsi) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (now, wear_percentage, health_score, edge_pixel_count,
                     image_path, kesim_id, makine_id, serit_id, malzeme_cinsi),
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

    def _run_ldc_inference(self, model, frame, device, torch, np, cv2):
        """Run LDC forward pass and return edge BGR image.

        Preprocessing matches old VisionService._run_ldc_on_image:
        resize 512x512, subtract BGR mean, CHW float32, sigmoid → normalize
        → uint8 → bitwise_not → resize → binarize.

        Args:
            model: Loaded LDC model instance.
            frame: Input BGR frame as numpy array.
            device: Torch device string ("cpu" or "cuda").
            torch: The torch module (lazy import).
            np: The numpy module (lazy import).
            cv2: The cv2 module (lazy import).

        Returns:
            Edge detection result as BGR numpy array.
        """
        h, w = frame.shape[:2]

        # Preprocess
        resized = cv2.resize(frame, (512, 512))
        img = resized.astype(np.float32)
        img -= np.array(self._bgr_mean, dtype=np.float32)
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

    def _compute_wear(self, edge_bgr, np, cv2) -> tuple:
        """Compute saw blade wear percentage from LDC edge image.

        Returns (wear_percentage, edge_pixel_count) or (None, None) if
        insufficient contour data. Matches old VisionService._compute_wear logic.

        Args:
            edge_bgr: LDC edge detection result as BGR numpy array.
            np: The numpy module (lazy import).
            cv2: The cv2 module (lazy import).

        Returns:
            Tuple of (wear_percentage, edge_pixel_count) where wear_percentage is
            a float in [0, 100] and edge_pixel_count is an int, or (None, None)
            if contour data is insufficient.
        """
        if edge_bgr is None:
            return None, None

        image_height, image_width = edge_bgr.shape[:2]

        # Calculate ROI pixel coordinates from normalized bbox
        x_center = int(self._roi_x_center_n * image_width)
        box_w = int(self._roi_width_n * image_width)

        x1 = int(x_center - box_w / 2)
        x2 = int(x_center + box_w / 2)
        y1 = self._top_line_y
        y2 = self._bottom_line_y

        # Clamp to image bounds
        x1 = max(0, min(x1, image_width - 1))
        x2 = max(0, min(x2, image_width))
        y1 = max(0, min(y1, image_height - 1))
        y2 = max(0, min(y2, image_height))

        if y2 <= y1 or x2 <= x1:
            return None, None

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
            return None, None

        # Collect Y coordinates from all contour points
        ys = [pt[0][1] for c in contours for pt in c]
        edge_pixel_count = len(ys)
        if edge_pixel_count < 5:
            return None, None

        ys = np.array(ys, dtype=np.int32)

        # Top 10% of Y values (smallest = highest in image)
        k = max(5, int(0.10 * ys.size))
        k = min(k, 50)
        smallest = np.partition(ys, k)[:k]
        min_y = int(np.mean(smallest))

        wear_y = min_y + y1
        band_h = max(1, self._bottom_line_y - self._top_line_y)
        percent = ((wear_y - self._top_line_y) / band_h) * 100.0
        percent = float(np.clip(percent, 0.0, 100.0))

        return percent, edge_pixel_count
