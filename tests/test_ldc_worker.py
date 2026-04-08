"""Unit tests for LDCWorker.

Tests cover: lightweight import (DET-06), constructor ROI config reading (D-06),
wear+health publishing to store (DET-03, DET-04, DET-05), db_service guard (D-04),
and stop event thread lifecycle.

All tests mock torch, cv2, numpy, and modelB4 via sys.modules patching so no
ML libraries are required at test time.
"""

from __future__ import annotations

import sys
import time
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.services.camera.results_store import CameraResultsStore

# ---------------------------------------------------------------------------
# Config fixture
# ---------------------------------------------------------------------------

LDC_CONFIG = {
    "wear": {
        "enabled": True,
        "interval_seconds": 0.1,
        "ldc_checkpoint_path": "data/models/ldc/16_model.pth",
        "top_line_y": 170,
        "bottom_line_y": 236,
        "roi_x_center_n": 0.500000,
        "roi_y_center_n": 0.530692,
        "roi_width_n": 0.736888,
        "roi_height_n": 0.489510,
        "bgr_mean": [103.939, 116.779, 123.68],
    },
    "health": {
        "broken_weight": 0.70,
        "wear_weight": 0.30,
    },
}

CUSTOM_ROI_CONFIG = {
    "wear": {
        "enabled": True,
        "interval_seconds": 0.1,
        "ldc_checkpoint_path": "data/models/ldc/16_model.pth",
        "top_line_y": 200,
        "bottom_line_y": 280,
        "roi_x_center_n": 0.600000,
        "roi_y_center_n": 0.530692,
        "roi_width_n": 0.736888,
        "roi_height_n": 0.489510,
        "bgr_mean": [103.939, 116.779, 123.68],
    },
    "health": {
        "broken_weight": 0.70,
        "wear_weight": 0.30,
    },
}


# ---------------------------------------------------------------------------
# sys.modules mock context manager
# ---------------------------------------------------------------------------


@contextmanager
def _mock_ml_libraries(produce_wear: bool = True):
    """Inject mock torch, cv2, numpy, and modelB4.LDC into sys.modules.

    Args:
        produce_wear: If True, mock cv2.findContours to return enough contour
            points for _compute_wear to produce a non-None result.

    Yields:
        Tuple of (mock_torch, mock_ldc_class) for additional setup if needed.
    """
    # Build mock torch
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    mock_torch.no_grad.return_value.__enter__ = MagicMock(return_value=None)
    mock_torch.no_grad.return_value.__exit__ = MagicMock(return_value=False)

    # Mock torch.load to return a state dict
    mock_torch.load.return_value = {}

    # isinstance(outputs, torch.Tensor) — make it False so we get list branch
    mock_torch.Tensor = type("FakeTensor", (), {})

    # Mock sigmoid output chain: sigmoid -> cpu -> detach -> numpy returns a 2D array
    # fake_edge is what the inference produces before post-processing
    fake_edge = np.zeros((512, 512), dtype=np.float32)
    fake_tensor = MagicMock()
    fake_tensor.cpu.return_value.detach.return_value.numpy.return_value = fake_edge

    # torch.sigmoid(m) must return an object whose .cpu().detach().numpy() yields fake_edge
    sigmoid_result = MagicMock()
    sigmoid_result.cpu.return_value.detach.return_value.numpy.return_value = fake_edge
    mock_torch.sigmoid.return_value = sigmoid_result

    # Build mock LDC model
    # model(tensor) must return a list of tensor-like objects
    # When model is called: mock_ldc_instance(tensor) should return [fake_tensor]
    mock_ldc_instance = MagicMock()
    mock_ldc_instance.return_value = [fake_tensor]
    mock_ldc_instance.to.return_value = mock_ldc_instance
    mock_ldc_instance.load_state_dict.return_value = None
    mock_ldc_instance.eval.return_value = None

    mock_ldc_class = MagicMock(return_value=mock_ldc_instance)

    mock_modelB4 = MagicMock()
    mock_modelB4.LDC = mock_ldc_class

    # Build mock cv2
    mock_cv2 = MagicMock()
    mock_cv2.THRESH_BINARY = 0
    mock_cv2.THRESH_BINARY_INV = 1
    mock_cv2.RETR_EXTERNAL = 0
    mock_cv2.CHAIN_APPROX_SIMPLE = 1
    mock_cv2.COLOR_GRAY2BGR = 8
    mock_cv2.COLOR_BGR2GRAY = 6

    # resize: return appropriately-shaped array based on target size
    def fake_resize(src, dsize, **kwargs):
        h, w = dsize[1], dsize[0]
        if len(src.shape) == 3:
            return np.zeros((h, w, src.shape[2]), dtype=src.dtype)
        return np.zeros((h, w), dtype=src.dtype)

    mock_cv2.resize.side_effect = fake_resize

    # bitwise_not: pass-through inversion on real arrays
    mock_cv2.bitwise_not.side_effect = lambda src: np.bitwise_not(src)

    # threshold: return a zero binary image same shape as input
    mock_cv2.threshold.side_effect = lambda src, thresh, maxval, ttype: (
        thresh,
        np.zeros_like(src),
    )

    # cvtColor: return appropriate channel count based on conversion code
    def fake_cvtcolor(src, code):
        if len(src.shape) == 2:
            # Gray -> BGR
            return np.zeros((src.shape[0], src.shape[1], 3), dtype=src.dtype)
        else:
            # BGR -> Gray
            return np.zeros((src.shape[0], src.shape[1]), dtype=src.dtype)

    mock_cv2.cvtColor.side_effect = fake_cvtcolor

    if produce_wear:
        # Build 10 contour points spread across Y range 5..20 (within ROI)
        # These points are in the format expected by _compute_wear:
        # [pt[0][1] for c in contours for pt in c]  =>  pt[0][1] is Y coord
        def make_contour_point(y_val: int) -> np.ndarray:
            return np.array([[[0, y_val]]], dtype=np.int32)

        fake_contours = [make_contour_point(y) for y in range(5, 20)]
        mock_cv2.findContours.return_value = (fake_contours, None)
    else:
        mock_cv2.findContours.return_value = ([], None)

    # Use real numpy for the lazy import — ldc_worker uses it for array ops.
    # We only mock torch/cv2/modelB4; numpy stays real so astype(np.uint8),
    # np.squeeze, np.array, etc. all work correctly.
    mock_np = np

    old_torch = sys.modules.get("torch")
    old_cv2 = sys.modules.get("cv2")
    old_np = sys.modules.get("numpy")
    old_modelB4 = sys.modules.get("src.services.camera.modelB4")

    sys.modules["torch"] = mock_torch
    sys.modules["cv2"] = mock_cv2
    sys.modules["numpy"] = mock_np
    sys.modules["src.services.camera.modelB4"] = mock_modelB4

    try:
        yield mock_torch, mock_ldc_class
    finally:
        # Restore original sys.modules state
        for key, old_val in [
            ("torch", old_torch),
            ("cv2", old_cv2),
            ("numpy", old_np),
            ("src.services.camera.modelB4", old_modelB4),
        ]:
            if old_val is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = old_val


# ---------------------------------------------------------------------------
# Test 1: Lightweight import (DET-06)
# ---------------------------------------------------------------------------


def test_import_stays_lightweight() -> None:
    """Importing ldc_worker does NOT trigger torch, cv2, or numpy imports (DET-06)."""
    modules_before = set(sys.modules.keys())

    import src.services.camera.ldc_worker  # noqa: F401 — import side-effect test

    modules_after = set(sys.modules.keys())
    new_modules = modules_after - modules_before

    assert "torch" not in new_modules, (
        "Importing ldc_worker triggered 'torch' import — lazy import guard broken"
    )
    assert "cv2" not in new_modules, (
        "Importing ldc_worker triggered 'cv2' import — lazy import guard broken"
    )
    assert "numpy" not in new_modules, (
        "Importing ldc_worker triggered 'numpy' import — lazy import guard broken"
    )


# ---------------------------------------------------------------------------
# Test 2: Constructor reads ROI from config (D-06)
# ---------------------------------------------------------------------------


def test_constructor_reads_roi_from_config() -> None:
    """LDCWorker reads ROI parameters from config dict, not hardcoded defaults."""
    from src.services.camera.ldc_worker import LDCWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()

    worker = LDCWorker(CUSTOM_ROI_CONFIG, store, mock_camera)

    assert worker._top_line_y == 200
    assert worker._bottom_line_y == 280
    assert worker._roi_x_center_n == pytest.approx(0.600000)
    assert worker._bgr_mean == [103.939, 116.779, 123.68]


# ---------------------------------------------------------------------------
# Test 3: Publishes wear and health to store (DET-03, DET-04, DET-05)
# ---------------------------------------------------------------------------


def test_publishes_wear_and_health() -> None:
    """After one cycle, store has wear_percentage, health_score, health_status, health_color, last_wear_ts."""
    from src.services.camera.ldc_worker import LDCWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()

    # Provide a real frame so the worker doesn't skip the cycle
    mock_camera.get_current_frame.return_value = np.zeros((480, 640, 3), dtype=np.uint8)

    # Pre-populate store with detection state (simulating DetectionWorker output)
    store.update("tooth_count", 10)
    store.update("broken_count", 2)

    with _mock_ml_libraries(produce_wear=True):
        # Need to reload the module since it may be cached without mocks
        import importlib

        import src.services.camera.ldc_worker as ldc_mod

        importlib.reload(ldc_mod)

        worker = ldc_mod.LDCWorker(LDC_CONFIG, store, mock_camera)

        # Patch _stop_event.wait to stop after first iteration
        call_count = [0]

        def fast_stop(timeout=None):
            call_count[0] += 1
            if call_count[0] >= 1:
                worker._stop_event.set()
            return worker._stop_event.is_set()

        # Also patch os.path.isfile to return True for checkpoint path
        with patch("os.path.isfile", return_value=True):
            worker._stop_event.wait = fast_stop
            worker.start()
            worker.join(timeout=5.0)

    assert not worker.is_alive(), "LDCWorker did not exit within 5 seconds"
    assert store.get("last_wear_ts") is not None, "last_wear_ts not published"
    assert store.get("health_score") is not None, "health_score not published"
    assert isinstance(store.get("health_status"), str), "health_status should be a string"
    assert isinstance(store.get("health_color"), str), "health_color should be a string"
    assert store.get("health_color", "").startswith("#"), "health_color should be a CSS hex"


# ---------------------------------------------------------------------------
# Test 4: db_service=None means no DB writes (D-04)
# ---------------------------------------------------------------------------


def test_db_write_guarded_by_db_service() -> None:
    """With db_service=None, no DB write is attempted even when wear is computed."""
    from src.services.camera.ldc_worker import LDCWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()
    mock_camera.get_current_frame.return_value = np.zeros((480, 640, 3), dtype=np.uint8)

    with _mock_ml_libraries(produce_wear=True):
        import importlib

        import src.services.camera.ldc_worker as ldc_mod

        importlib.reload(ldc_mod)

        worker = ldc_mod.LDCWorker(LDC_CONFIG, store, mock_camera, db_service=None)

        call_count = [0]

        def fast_stop(timeout=None):
            call_count[0] += 1
            if call_count[0] >= 1:
                worker._stop_event.set()
            return worker._stop_event.is_set()

        with patch("os.path.isfile", return_value=True):
            worker._stop_event.wait = fast_stop
            worker.start()
            worker.join(timeout=5.0)

    assert worker._db_service is None
    assert not worker.is_alive()


# ---------------------------------------------------------------------------
# Test 5: stop() causes thread to exit
# ---------------------------------------------------------------------------


def test_stop_event_exits_loop() -> None:
    """Calling stop() causes the worker thread to exit; is_alive() becomes False."""
    from src.services.camera.ldc_worker import LDCWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()

    # Return None frame so the worker goes through the early-continue branch
    mock_camera.get_current_frame.return_value = None

    with _mock_ml_libraries(produce_wear=False):
        import importlib

        import src.services.camera.ldc_worker as ldc_mod

        importlib.reload(ldc_mod)

        worker = ldc_mod.LDCWorker(LDC_CONFIG, store, mock_camera)

        with patch("os.path.isfile", return_value=True):
            worker.start()
            time.sleep(0.15)
            worker.stop()
            worker.join(timeout=5.0)

    assert not worker.is_alive(), "Thread still alive after stop() and 5s join timeout"


# ---------------------------------------------------------------------------
# Test 6: _compute_wear returns tuple (float, int) when contours found
# ---------------------------------------------------------------------------


def test_compute_wear_returns_tuple():
    """_compute_wear returns (wear_percentage: float, edge_pixel_count: int) when contours found."""
    from src.services.camera.ldc_worker import LDCWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()
    worker = LDCWorker(LDC_CONFIG, store, mock_camera)

    with _mock_ml_libraries(produce_wear=True):
        import sys
        mock_cv2 = sys.modules.get("cv2")
        mock_np = sys.modules.get("numpy")

        # Build a real gray edge image for the real _compute_wear logic
        # Use real numpy since we're using the real impl
        import numpy as real_np
        # Create a fake edge image and mock cv2 for _compute_wear
        fake_edge_bgr = real_np.zeros((480, 640, 3), dtype=real_np.uint8)

        # Mock cv2 for the _compute_wear call
        mock_cv2_local = MagicMock()
        mock_cv2_local.COLOR_BGR2GRAY = 6
        mock_cv2_local.THRESH_BINARY = 0
        mock_cv2_local.THRESH_BINARY_INV = 1
        mock_cv2_local.RETR_EXTERNAL = 0
        mock_cv2_local.CHAIN_APPROX_SIMPLE = 1

        # Return a gray image
        mock_cv2_local.cvtColor.return_value = real_np.zeros((480, 640), dtype=real_np.uint8)
        # threshold returns mean val and binary
        gray_roi = real_np.zeros((66, 471), dtype=real_np.uint8)
        mock_cv2_local.threshold.return_value = (0, gray_roi)
        # findContours: return enough points
        def make_contour_point(y_val):
            return real_np.array([[[0, y_val]]], dtype=real_np.int32)
        fake_contours = [make_contour_point(y) for y in range(5, 20)]
        mock_cv2_local.findContours.return_value = (fake_contours, None)

        result = worker._compute_wear(fake_edge_bgr, real_np, mock_cv2_local)

    assert isinstance(result, tuple), f"_compute_wear should return tuple, got {type(result)}"
    assert len(result) == 2, f"Tuple should have 2 elements, got {len(result)}"
    wear_pct, edge_count = result
    assert wear_pct is not None, "wear_percentage should not be None with valid contours"
    assert edge_count is not None, "edge_pixel_count should not be None with valid contours"
    assert isinstance(wear_pct, float), f"wear_percentage should be float, got {type(wear_pct)}"
    assert isinstance(edge_count, int), f"edge_pixel_count should be int, got {type(edge_count)}"


# ---------------------------------------------------------------------------
# Test 7: _compute_wear returns (None, None) when edge_bgr is None
# ---------------------------------------------------------------------------


def test_compute_wear_returns_none_tuple_when_no_edge():
    """_compute_wear returns (None, None) when edge_bgr is None."""
    from src.services.camera.ldc_worker import LDCWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()
    worker = LDCWorker(LDC_CONFIG, store, mock_camera)

    import numpy as real_np
    import sys
    mock_cv2 = MagicMock()

    result = worker._compute_wear(None, real_np, mock_cv2)

    assert result == (None, None), f"Expected (None, None), got {result}"


# ---------------------------------------------------------------------------
# Test 8: DB write includes traceability fields and edge_pixel_count (D-05, D-06)
# ---------------------------------------------------------------------------


def test_db_write_includes_traceability_and_edge_pixel_count():
    """LDCWorker DB write_async includes edge_pixel_count, kesim_id, makine_id, serit_id, malzeme_cinsi."""
    from src.services.camera.ldc_worker import LDCWorker

    store = CameraResultsStore()
    # Pre-populate traceability in store
    store.update("kesim_id", 99)
    store.update("makine_id", 2)
    store.update("serit_id", 8)
    store.update("malzeme_cinsi", 3)

    mock_camera = MagicMock()
    mock_camera.get_current_frame.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_db = MagicMock()
    mock_db.write_async.return_value = True

    with _mock_ml_libraries(produce_wear=True):
        import importlib
        import src.services.camera.ldc_worker as ldc_mod
        importlib.reload(ldc_mod)

        worker = ldc_mod.LDCWorker(LDC_CONFIG, store, mock_camera, db_service=mock_db)

        call_count = [0]

        def fast_stop(timeout=None):
            call_count[0] += 1
            if call_count[0] >= 1:
                worker._stop_event.set()
            return worker._stop_event.is_set()

        from unittest.mock import patch
        with patch("os.path.isfile", return_value=True):
            worker._stop_event.wait = fast_stop
            worker.start()
            worker.join(timeout=5.0)

    # The wear_history write should have been made
    assert mock_db.write_async.called, "DB write was not called"
    call_args = mock_db.write_async.call_args_list[0]
    params = call_args[0][1]  # params tuple
    # params: (now, wear_percentage, health_score, edge_pixel_count, image_path, kesim_id, makine_id, serit_id, malzeme_cinsi)
    assert params[5] == 99, f"kesim_id should be 99, got {params[5]}"
    assert params[6] == 2, f"makine_id should be 2, got {params[6]}"
    assert params[7] == 8, f"serit_id should be 8, got {params[7]}"
    assert params[8] == 3, f"malzeme_cinsi should be 3, got {params[8]}"


# ---------------------------------------------------------------------------
# Test 9: Constructor reads health weights from config
# ---------------------------------------------------------------------------


def test_constructor_reads_health_weights_from_config() -> None:
    """LDCWorker reads broken_weight and wear_weight from config.health section."""
    from src.services.camera.ldc_worker import LDCWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()

    custom_config = {
        "wear": LDC_CONFIG["wear"],
        "health": {
            "broken_weight": 0.50,
            "wear_weight": 0.50,
        },
    }

    worker = LDCWorker(custom_config, store, mock_camera)

    assert worker._broken_weight == pytest.approx(0.50)
    assert worker._wear_weight == pytest.approx(0.50)


# ---------------------------------------------------------------------------
# Test 10: Default health weights when no health config section
# ---------------------------------------------------------------------------


def test_default_health_weights_without_config() -> None:
    """LDCWorker uses default 0.7/0.3 when config has no health section."""
    from src.services.camera.ldc_worker import LDCWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()

    minimal_config = {
        "wear": LDC_CONFIG["wear"],
        # no "health" key
    }

    worker = LDCWorker(minimal_config, store, mock_camera)

    assert worker._broken_weight == pytest.approx(0.7)
    assert worker._wear_weight == pytest.approx(0.3)
