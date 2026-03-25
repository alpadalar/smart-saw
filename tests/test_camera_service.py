"""Unit tests for CameraService.

All tests mock cv2.VideoCapture so no physical camera hardware is required.
Tests cover: constructor (no I/O), start/stop lifecycle, cap property application,
auto-discovery, recording directory format, JPEG file writing, and frame accessor.
"""

import asyncio
import os
import re
import threading
import time
from unittest.mock import MagicMock, PropertyMock, call, patch

import numpy as np
import pytest

from src.services.camera.camera_service import CameraService
from src.services.camera.results_store import CameraResultsStore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_CONFIG = {
    "device_id": 0,
    "resolution": {"width": 1280, "height": 720},
    "fps": 30,
    "jpeg_quality": 85,
    "recordings_path": "",  # overridden in recording tests via tmp_path
}


@pytest.fixture()
def store() -> CameraResultsStore:
    return CameraResultsStore()


@pytest.fixture()
def config(tmp_path) -> dict:
    cfg = dict(TEST_CONFIG)
    cfg["recordings_path"] = str(tmp_path)
    return cfg


def _make_mock_cap(opened: bool = True) -> MagicMock:
    """Return a MagicMock VideoCapture that is already opened or not."""
    cap = MagicMock()
    cap.isOpened.return_value = opened
    cap.get.return_value = 0.0
    return cap


# ---------------------------------------------------------------------------
# Task 1 tests: constructor / basic lifecycle
# ---------------------------------------------------------------------------


def test_constructor_no_io(store):
    """CameraService(config, store) does not call VideoCapture on construction."""
    with patch("src.services.camera.camera_service.cv2") as mock_cv2:
        svc = CameraService(TEST_CONFIG, store)
        mock_cv2.VideoCapture.assert_not_called()


def test_start_returns_false_on_no_device(store, config):
    """start() returns False (never raises) when the camera device cannot be opened."""
    mock_cap = _make_mock_cap(opened=False)
    with patch("src.services.camera.camera_service.cv2") as mock_cv2:
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
        mock_cv2.CAP_PROP_FPS = 5
        mock_cv2.CAP_PROP_BUFFERSIZE = 8
        mock_cv2.CAP_DSHOW = 700
        svc = CameraService(config, store)
        result = asyncio.run(svc.start())
    assert result is False


def test_cap_props_applied(store, config):
    """start() calls cap.set() with CAP_PROP_FRAME_WIDTH=1280, HEIGHT=720, FPS=30, BUFFERSIZE=1."""
    mock_cap = _make_mock_cap(opened=True)
    # Simulate a successful read so the capture loop doesn't spin hot
    stop_event = threading.Event()

    def fake_read():
        if stop_event.is_set():
            return False, None
        return True, np.zeros((720, 1280, 3), dtype=np.uint8)

    mock_cap.read.side_effect = lambda: fake_read()

    with patch("src.services.camera.camera_service.cv2") as mock_cv2:
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
        mock_cv2.CAP_PROP_FPS = 5
        mock_cv2.CAP_PROP_BUFFERSIZE = 8
        mock_cv2.CAP_DSHOW = 700
        mock_cv2.IMWRITE_JPEG_QUALITY = 1
        mock_cv2.imencode.return_value = (True, MagicMock(tobytes=lambda: b"jpeg"))
        svc = CameraService(config, store)
        result = asyncio.run(svc.start())

    assert result is True
    set_calls = mock_cap.set.call_args_list
    # Verify the four required props were set
    props_set = {c[0][0]: c[0][1] for c in set_calls}
    assert props_set.get(3) == 1280   # CAP_PROP_FRAME_WIDTH
    assert props_set.get(4) == 720    # CAP_PROP_FRAME_HEIGHT
    assert props_set.get(5) == 30     # CAP_PROP_FPS
    assert props_set.get(8) == 1      # CAP_PROP_BUFFERSIZE

    stop_event.set()
    asyncio.run(svc.stop())


def test_recording_dir_format(store, config, tmp_path):
    """start_recording() creates a directory matching YYYYMMDD-HHMMSS under recordings_path."""
    mock_cap = _make_mock_cap(opened=True)
    mock_cap.read.return_value = (False, None)

    with patch("src.services.camera.camera_service.cv2") as mock_cv2:
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
        mock_cv2.CAP_PROP_FPS = 5
        mock_cv2.CAP_PROP_BUFFERSIZE = 8
        mock_cv2.CAP_DSHOW = 700
        mock_cv2.imencode.return_value = (True, MagicMock(tobytes=lambda: b"jpeg"))
        svc = CameraService(config, store)
        asyncio.run(svc.start())
        result = svc.start_recording()

    assert result is True
    dirs = list(tmp_path.iterdir())
    assert len(dirs) == 1
    dir_name = dirs[0].name
    assert re.fullmatch(r"\d{8}-\d{6}", dir_name), f"Unexpected dir name: {dir_name}"

    asyncio.run(svc.stop())


def test_recording_writes_jpegs(store, config, tmp_path):
    """start_recording() + capture loop writes frame_000001.jpg to recording dir."""
    # Produce one real numpy frame
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    frames_produced = [0]
    capture_started = threading.Event()
    stop_capture = threading.Event()

    def fake_read():
        capture_started.set()
        if stop_capture.is_set():
            return False, None
        frames_produced[0] += 1
        return True, frame.copy()

    mock_cap = _make_mock_cap(opened=True)
    mock_cap.read.side_effect = lambda: fake_read()

    # Use real cv2.imencode for JPEG encoding (numpy available)
    import cv2 as real_cv2

    with patch("src.services.camera.camera_service.cv2") as mock_cv2:
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.CAP_PROP_FRAME_WIDTH = real_cv2.CAP_PROP_FRAME_WIDTH
        mock_cv2.CAP_PROP_FRAME_HEIGHT = real_cv2.CAP_PROP_FRAME_HEIGHT
        mock_cv2.CAP_PROP_FPS = real_cv2.CAP_PROP_FPS
        mock_cv2.CAP_PROP_BUFFERSIZE = real_cv2.CAP_PROP_BUFFERSIZE
        mock_cv2.CAP_DSHOW = getattr(real_cv2, "CAP_DSHOW", 700)
        mock_cv2.IMWRITE_JPEG_QUALITY = real_cv2.IMWRITE_JPEG_QUALITY
        mock_cv2.imencode.side_effect = real_cv2.imencode
        mock_cv2.imwrite.side_effect = real_cv2.imwrite

        svc = CameraService(config, store)
        asyncio.run(svc.start())

        # Wait for capture loop to be running
        assert capture_started.wait(timeout=2.0), "Capture loop never started"

        svc.start_recording()
        # Let at least a few frames be captured
        time.sleep(0.2)
        svc.stop_recording()
        stop_capture.set()
        asyncio.run(svc.stop())

    dirs = list(tmp_path.iterdir())
    assert len(dirs) == 1
    recording_dir = dirs[0]
    jpegs = sorted(recording_dir.glob("frame_*.jpg"))
    assert len(jpegs) >= 1, "No JPEG files written to recording directory"
    assert jpegs[0].name == "frame_000001.jpg"


def test_start_recording_stop_recording_lifecycle(store, config):
    """start_recording() sets is_recording=True in store; stop_recording() sets it False."""
    mock_cap = _make_mock_cap(opened=True)
    mock_cap.read.return_value = (False, None)

    with patch("src.services.camera.camera_service.cv2") as mock_cv2:
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
        mock_cv2.CAP_PROP_FPS = 5
        mock_cv2.CAP_PROP_BUFFERSIZE = 8
        mock_cv2.CAP_DSHOW = 700
        mock_cv2.imencode.return_value = (True, MagicMock(tobytes=lambda: b"jpeg"))
        svc = CameraService(config, store)
        asyncio.run(svc.start())
        svc.start_recording()
        assert store.get("is_recording") is True
        svc.stop_recording()
        assert store.get("is_recording") is False

    asyncio.run(svc.stop())


def test_get_current_frame_returns_none_before_start(store):
    """get_current_frame() returns None before start() is called."""
    svc = CameraService(TEST_CONFIG, store)
    assert svc.get_current_frame() is None


def test_auto_discovery_tries_multiple_devices(store, config):
    """Auto-discovery: first device fails (isOpened=False), second succeeds."""
    call_count = [0]

    def make_cap(*args, **kwargs):
        call_count[0] += 1
        cap = _make_mock_cap(opened=(call_count[0] > 1))  # first fails, rest succeed
        cap.read.return_value = (False, None)
        return cap

    with patch("src.services.camera.camera_service.cv2") as mock_cv2:
        mock_cv2.VideoCapture.side_effect = make_cap
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
        mock_cv2.CAP_PROP_FPS = 5
        mock_cv2.CAP_PROP_BUFFERSIZE = 8
        mock_cv2.CAP_DSHOW = 700
        mock_cv2.imencode.return_value = (True, MagicMock(tobytes=lambda: b"jpeg"))
        svc = CameraService(config, store)
        result = asyncio.run(svc.start())

    assert result is True, "Service should start successfully after discovering second device"
    assert call_count[0] >= 2, "Expected at least 2 VideoCapture attempts"

    asyncio.run(svc.stop())


def test_stop_releases_camera(store, config):
    """After stop(), VideoCapture.release() is called."""
    mock_cap = _make_mock_cap(opened=True)
    mock_cap.read.return_value = (False, None)

    with patch("src.services.camera.camera_service.cv2") as mock_cv2:
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
        mock_cv2.CAP_PROP_FPS = 5
        mock_cv2.CAP_PROP_BUFFERSIZE = 8
        mock_cv2.CAP_DSHOW = 700
        mock_cv2.imencode.return_value = (True, MagicMock(tobytes=lambda: b"jpeg"))
        svc = CameraService(config, store)
        asyncio.run(svc.start())
        asyncio.run(svc.stop())

    mock_cap.release.assert_called()
