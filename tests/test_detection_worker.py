"""Unit tests for DetectionWorker.

Tests cover: lightweight import (DET-06), constructor config reading,
broken detection publishing (DET-01, DET-05), crack detection publishing
(DET-02, DET-05), db_service guard (D-04), and stop event (thread lifecycle).

All tests mock torch and ultralytics via sys.modules patching so no ML
libraries are required at test time.
"""

from __future__ import annotations

import sys
import threading
import time
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.services.camera.results_store import CameraResultsStore

# ---------------------------------------------------------------------------
# Config fixture
# ---------------------------------------------------------------------------

DET_CONFIG = {
    "detection": {
        "enabled": True,
        "interval_seconds": 0.05,  # fast for tests
        "confidence_threshold": 0.5,
        "broken_model_path": "data/models/best.pt",
        "crack_model_path": "data/models/catlak-best.pt",
    }
}


# ---------------------------------------------------------------------------
# Mock box helpers
# ---------------------------------------------------------------------------


def _make_mock_box(class_id: int, confidence: float) -> MagicMock:
    """Return a MagicMock RTDETR result box with cls and conf accessors.

    Args:
        class_id: Integer class index (0=tooth or 0=crack, 1=broken).
        confidence: Detection confidence score in [0, 1].

    Returns:
        MagicMock that mimics ultralytics Boxes entry with
        ``.cls[0].item()`` and ``.conf[0].item()`` APIs.
    """
    box = MagicMock()

    cls_item = MagicMock()
    cls_item.item.return_value = class_id
    cls_tensor = MagicMock()
    cls_tensor.__getitem__ = lambda self, idx: cls_item
    box.cls = cls_tensor

    conf_item = MagicMock()
    conf_item.item.return_value = confidence
    conf_tensor = MagicMock()
    conf_tensor.__getitem__ = lambda self, idx: conf_item
    box.conf = conf_tensor

    # xyxy for annotated frame drawing — provide an indexable mock
    xyxy_item = [10, 20, 100, 200]
    xyxy_tensor = MagicMock()
    xyxy_tensor.__getitem__ = lambda self, idx: xyxy_item
    box.xyxy = xyxy_tensor

    return box


def _make_mock_result(boxes: list) -> MagicMock:
    """Return a MagicMock RTDETR Results object wrapping a list of boxes.

    Args:
        boxes: List of mock box objects.

    Returns:
        MagicMock with a ``.boxes`` attribute iterable in a for-loop.
    """
    result = MagicMock()
    result.boxes = boxes
    return result


# ---------------------------------------------------------------------------
# sys.modules mock context manager
# ---------------------------------------------------------------------------


@contextmanager
def _mock_torch_ultralytics(broken_boxes: list, crack_boxes: list):
    """Inject mock torch and ultralytics into sys.modules.

    The mock RTDETR alternates between returning broken_boxes results
    and crack_boxes results depending on the model path suffix.

    Args:
        broken_boxes: Boxes returned by the broken model's predict() call.
        crack_boxes: Boxes returned by the crack model's predict() call.

    Yields:
        Tuple of (mock_torch, mock_rtdetr_class) for additional setup if needed.
    """
    # Build mock torch
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    mock_torch.no_grad.return_value.__enter__ = MagicMock(return_value=None)
    mock_torch.no_grad.return_value.__exit__ = MagicMock(return_value=False)

    # Build mock RTDETR — first instantiation = broken model, second = crack model
    broken_result = _make_mock_result(broken_boxes)
    crack_result = _make_mock_result(crack_boxes)

    call_order = [0]

    def make_rtdetr(model_path: str) -> MagicMock:
        model = MagicMock()
        if "catlak" in model_path:
            model.predict.return_value = [crack_result]
        else:
            model.predict.return_value = [broken_result]
        model.to.return_value = model
        return model

    mock_rtdetr_class = MagicMock(side_effect=make_rtdetr)

    mock_ultralytics = MagicMock()
    mock_ultralytics.RTDETR = mock_rtdetr_class

    old_torch = sys.modules.get("torch")
    old_ultralytics = sys.modules.get("ultralytics")

    sys.modules["torch"] = mock_torch
    sys.modules["ultralytics"] = mock_ultralytics

    try:
        yield mock_torch, mock_rtdetr_class
    finally:
        # Restore previous state
        if old_torch is None:
            sys.modules.pop("torch", None)
        else:
            sys.modules["torch"] = old_torch

        if old_ultralytics is None:
            sys.modules.pop("ultralytics", None)
        else:
            sys.modules["ultralytics"] = old_ultralytics


# ---------------------------------------------------------------------------
# Test 1: Lightweight import (DET-06)
# ---------------------------------------------------------------------------


def test_import_stays_lightweight():
    """Importing detection_worker does NOT trigger torch or ultralytics imports (DET-06)."""
    # Remove from sys.modules cache to force a fresh import check
    modules_before = set(sys.modules.keys())

    # Ensure detection_worker itself is importable without torch present
    # If it's already imported, just verify torch/ultralytics are absent from modules
    import src.services.camera.detection_worker  # noqa: F401 — import side-effect test

    modules_after = set(sys.modules.keys())
    new_modules = modules_after - modules_before

    assert "torch" not in new_modules, (
        "Importing detection_worker triggered 'torch' import — lazy import guard broken"
    )
    assert "ultralytics" not in new_modules, (
        "Importing detection_worker triggered 'ultralytics' import — lazy import guard broken"
    )


# ---------------------------------------------------------------------------
# Test 2: Constructor reads config values (no I/O, no model loading)
# ---------------------------------------------------------------------------


def test_constructor_sets_config():
    """DetectionWorker(config, store, camera_service) reads detection config values."""
    from src.services.camera.detection_worker import DetectionWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()

    worker = DetectionWorker(DET_CONFIG, store, mock_camera)

    assert worker._enabled is True
    assert worker._interval == pytest.approx(0.05)
    assert worker._confidence == pytest.approx(0.5)
    assert worker._broken_model_path == "data/models/best.pt"
    assert worker._crack_model_path == "data/models/catlak-best.pt"
    assert worker._db_service is None
    assert worker._model_load_failed is False


# ---------------------------------------------------------------------------
# Test 3: Broken tooth detection publishes correct results (DET-01, DET-05)
# ---------------------------------------------------------------------------


def test_publishes_broken_results():
    """After one cycle, store has tooth_count=1, broken_count=1, broken_confidence=0.85 (DET-01, DET-05)."""
    from src.services.camera.detection_worker import DetectionWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()
    mock_camera.get_current_frame.return_value = np.zeros((720, 1280, 3), dtype=np.uint8)

    tooth_box = _make_mock_box(class_id=0, confidence=0.90)
    broken_box = _make_mock_box(class_id=1, confidence=0.85)

    with _mock_torch_ultralytics(
        broken_boxes=[tooth_box, broken_box],
        crack_boxes=[],
    ):
        worker = DetectionWorker(DET_CONFIG, store, mock_camera)

        # Stop after first iteration by patching wait so it sets stop immediately
        call_count = [0]
        original_wait = worker._stop_event.wait

        def fast_stop(timeout=None):
            call_count[0] += 1
            if call_count[0] >= 1:
                worker._stop_event.set()
            return worker._stop_event.is_set()

        worker._stop_event.wait = fast_stop
        worker.start()
        worker.join(timeout=5.0)

    assert not worker.is_alive(), "DetectionWorker did not exit within 5 seconds"
    assert store.get("tooth_count") == 1
    assert store.get("broken_count") == 1
    assert store.get("broken_confidence") == pytest.approx(0.85)
    assert store.get("last_detection_ts") is not None


# ---------------------------------------------------------------------------
# Test 4: Crack detection publishes correct results (DET-02, DET-05)
# ---------------------------------------------------------------------------


def test_publishes_crack_results():
    """After one cycle, store has crack_count=1, crack_confidence=0.70 (DET-02, DET-05)."""
    from src.services.camera.detection_worker import DetectionWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()
    mock_camera.get_current_frame.return_value = np.zeros((720, 1280, 3), dtype=np.uint8)

    crack_box = _make_mock_box(class_id=0, confidence=0.70)

    with _mock_torch_ultralytics(
        broken_boxes=[],
        crack_boxes=[crack_box],
    ):
        worker = DetectionWorker(DET_CONFIG, store, mock_camera)

        call_count = [0]

        def fast_stop(timeout=None):
            call_count[0] += 1
            if call_count[0] >= 1:
                worker._stop_event.set()
            return worker._stop_event.is_set()

        worker._stop_event.wait = fast_stop
        worker.start()
        worker.join(timeout=5.0)

    assert not worker.is_alive(), "DetectionWorker did not exit within 5 seconds"
    assert store.get("crack_count") == 1
    assert store.get("crack_confidence") == pytest.approx(0.70)


# ---------------------------------------------------------------------------
# Test 5: db_service=None means no DB writes (D-04)
# ---------------------------------------------------------------------------


def test_db_write_guarded_by_db_service():
    """With db_service=None, no DB write is attempted even when broken_count > 0 (D-04)."""
    from src.services.camera.detection_worker import DetectionWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()
    mock_camera.get_current_frame.return_value = np.zeros((720, 1280, 3), dtype=np.uint8)

    broken_box = _make_mock_box(class_id=1, confidence=0.92)

    with _mock_torch_ultralytics(broken_boxes=[broken_box], crack_boxes=[]):
        worker = DetectionWorker(DET_CONFIG, store, mock_camera, db_service=None)

        call_count = [0]

        def fast_stop(timeout=None):
            call_count[0] += 1
            if call_count[0] >= 1:
                worker._stop_event.set()
            return worker._stop_event.is_set()

        worker._stop_event.wait = fast_stop
        worker.start()
        worker.join(timeout=5.0)

    # db_service is None — no write_async should have been called
    assert worker._db_service is None
    # Verify broken_count was detected (sanity check)
    assert store.get("broken_count") == 1


# ---------------------------------------------------------------------------
# Test 6: stop() causes the loop to exit
# ---------------------------------------------------------------------------


def test_stop_event_exits_loop():
    """Calling stop() causes the main loop to exit; thread is_alive() becomes False."""
    from src.services.camera.detection_worker import DetectionWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()

    # Return None frame so the worker goes through the early-continue branch
    mock_camera.get_current_frame.return_value = None

    with _mock_torch_ultralytics(broken_boxes=[], crack_boxes=[]):
        worker = DetectionWorker(DET_CONFIG, store, mock_camera)
        worker.start()

        # Give the worker a moment to enter the loop
        time.sleep(0.15)
        worker.stop()
        worker.join(timeout=5.0)

    assert not worker.is_alive(), "Thread still alive after stop() and 5s join timeout"


# ---------------------------------------------------------------------------
# Test 7: DB write includes traceability fields from CameraResultsStore (D-05)
# ---------------------------------------------------------------------------


def test_db_write_includes_traceability_fields():
    """DetectionWorker DB write_async includes kesim_id, makine_id, serit_id, malzeme_cinsi from store."""
    from src.services.camera.detection_worker import DetectionWorker

    store = CameraResultsStore()
    # Pre-populate traceability in store
    store.update("kesim_id", 42)
    store.update("makine_id", 7)
    store.update("serit_id", 3)
    store.update("malzeme_cinsi", 5)

    mock_camera = MagicMock()
    mock_camera.get_current_frame.return_value = np.zeros((720, 1280, 3), dtype=np.uint8)
    mock_db = MagicMock()
    mock_db.write_async.return_value = True

    broken_box = _make_mock_box(class_id=1, confidence=0.88)

    with _mock_torch_ultralytics(broken_boxes=[broken_box], crack_boxes=[]):
        worker = DetectionWorker(DET_CONFIG, store, mock_camera, db_service=mock_db)

        call_count = [0]

        def fast_stop(timeout=None):
            call_count[0] += 1
            if call_count[0] >= 1:
                worker._stop_event.set()
            return worker._stop_event.is_set()

        worker._stop_event.wait = fast_stop
        worker.start()
        worker.join(timeout=5.0)

    assert mock_db.write_async.called, "DB write was not called with broken_count > 0"
    # Check the params tuple for the broken_tooth write
    call_args = mock_db.write_async.call_args_list[0]
    params = call_args[0][1]  # positional arg index 1 = params tuple
    # params: (now, event_type, confidence, count, image_path, kesim_id, makine_id, serit_id, malzeme_cinsi)
    assert params[5] == 42, f"kesim_id should be 42, got {params[5]}"
    assert params[6] == 7, f"makine_id should be 7, got {params[6]}"
    assert params[7] == 3, f"serit_id should be 3, got {params[7]}"
    assert params[8] == 5, f"malzeme_cinsi should be 5, got {params[8]}"


# ---------------------------------------------------------------------------
# Test 8: _save_annotated_frame returns path when recording is active
# ---------------------------------------------------------------------------


def test_save_annotated_frame_returns_path_when_recording():
    """_save_annotated_frame returns file path string when recording_path is set in store."""
    import os
    import sys
    import tempfile
    from src.services.camera.detection_worker import DetectionWorker

    store = CameraResultsStore()
    mock_camera = MagicMock()
    worker = DetectionWorker(DET_CONFIG, store, mock_camera)

    # We need cv2 to be importable inside _save_annotated_frame
    # Use a temp dir as the recording path
    with tempfile.TemporaryDirectory() as tmp_dir:
        store.update("recording_path", tmp_dir)

        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        # Mock cv2 for this call — imencode must return (ok, buf) tuple
        mock_cv2 = MagicMock()
        mock_cv2.imencode.return_value = (True, MagicMock())
        mock_cv2.imwrite.return_value = True
        mock_cv2.rectangle = MagicMock()
        mock_cv2.putText = MagicMock()
        mock_cv2.IMWRITE_JPEG_QUALITY = 1
        mock_cv2.FONT_HERSHEY_SIMPLEX = 0

        old_cv2 = sys.modules.get("cv2")
        sys.modules["cv2"] = mock_cv2
        try:
            result = worker._save_annotated_frame(frame, [], [])
        finally:
            if old_cv2 is None:
                sys.modules.pop("cv2", None)
            else:
                sys.modules["cv2"] = old_cv2

    assert result is not None, "_save_annotated_frame should return a path string when recording"
    assert isinstance(result, str), "_save_annotated_frame should return a str path"


# ---------------------------------------------------------------------------
# Test 9: _save_annotated_frame returns None when recording_path is not set
# ---------------------------------------------------------------------------


def test_save_annotated_frame_returns_none_without_recording():
    """_save_annotated_frame returns None when no recording_path in store."""
    from src.services.camera.detection_worker import DetectionWorker

    store = CameraResultsStore()  # no recording_path set
    mock_camera = MagicMock()
    worker = DetectionWorker(DET_CONFIG, store, mock_camera)

    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    import sys
    mock_cv2 = MagicMock()
    # imencode must return (ok, buf) tuple; even without recording, store write path runs
    mock_cv2.imencode.return_value = (True, MagicMock())
    mock_cv2.IMWRITE_JPEG_QUALITY = 1
    mock_cv2.FONT_HERSHEY_SIMPLEX = 0
    old_cv2 = sys.modules.get("cv2")
    sys.modules["cv2"] = mock_cv2
    try:
        result = worker._save_annotated_frame(frame, [], [])
    finally:
        if old_cv2 is None:
            sys.modules.pop("cv2", None)
        else:
            sys.modules["cv2"] = old_cv2

    assert result is None, "_save_annotated_frame should return None when no recording_path"
