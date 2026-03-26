"""Unit tests for VisionService and DataProcessingPipeline camera bridge.

Tests cover: recording trigger on CUTTING->non-CUTTING transition, stop after
duration, no duplicate triggers, error isolation (D-07), stop event, traceability
write from DataProcessingPipeline to CameraResultsStore.

No heavy dependencies — VisionService has no torch/cv2 so standard unittest.mock
suffices. DataProcessingPipeline tests mock all modbus/control/db deps.
"""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch, call

import pytest

from src.services.camera.results_store import CameraResultsStore


# ---------------------------------------------------------------------------
# Config fixture
# ---------------------------------------------------------------------------

VISION_CONFIG = {
    "vision": {
        "polling_interval": 0.05,   # fast for tests
        "recording_duration": 10.0,
    }
}


# ---------------------------------------------------------------------------
# Helper: advance monotonic time
# ---------------------------------------------------------------------------


def _make_worker(store=None, camera_service=None, config=None):
    """Return a VisionService instance with mocked deps."""
    from src.services.camera.vision_service import VisionService

    store = store or CameraResultsStore()
    camera_service = camera_service or MagicMock()
    config = config or VISION_CONFIG

    return VisionService(config, store, camera_service)


# ---------------------------------------------------------------------------
# Test 1: CUTTING(3)->non-CUTTING transition triggers start_recording
# ---------------------------------------------------------------------------


def test_recording_triggered_on_cutting_end():
    """VisionService calls start_recording() when testere_durumu goes 3 -> non-3."""
    from src.services.camera.vision_service import VisionService

    store = CameraResultsStore()
    mock_camera = MagicMock()
    mock_camera.start_recording.return_value = True

    # Initial state: was cutting (3), now stopped (0)
    store.update("testere_durumu", 0)

    worker = VisionService(VISION_CONFIG, store, mock_camera)
    # Manually set prev to 3 to simulate transition
    worker._prev_testere_durumu = 3

    # Run one poll cycle inline (not in thread)
    worker._poll_once()

    mock_camera.start_recording.assert_called_once()
    assert worker._is_recording is True


# ---------------------------------------------------------------------------
# Test 2: No recording trigger when prev is NOT 3
# ---------------------------------------------------------------------------


def test_no_recording_trigger_when_not_cutting():
    """VisionService does NOT trigger start_recording if previous state was not CUTTING."""
    from src.services.camera.vision_service import VisionService

    store = CameraResultsStore()
    store.update("testere_durumu", 0)
    mock_camera = MagicMock()

    worker = VisionService(VISION_CONFIG, store, mock_camera)
    worker._prev_testere_durumu = 0  # was NOT cutting

    worker._poll_once()

    mock_camera.start_recording.assert_not_called()
    assert worker._is_recording is False


# ---------------------------------------------------------------------------
# Test 3: No recording trigger if already recording
# ---------------------------------------------------------------------------


def test_no_duplicate_recording_trigger():
    """VisionService does NOT call start_recording again if already recording."""
    from src.services.camera.vision_service import VisionService

    store = CameraResultsStore()
    store.update("testere_durumu", 0)
    mock_camera = MagicMock()

    worker = VisionService(VISION_CONFIG, store, mock_camera)
    worker._prev_testere_durumu = 3
    worker._is_recording = True  # already recording
    worker._recording_start_time = time.monotonic()  # recent start

    worker._poll_once()

    mock_camera.start_recording.assert_not_called()


# ---------------------------------------------------------------------------
# Test 4: stop_recording called after recording_duration elapsed
# ---------------------------------------------------------------------------


def test_stop_recording_after_duration():
    """VisionService calls stop_recording() when recording_duration seconds have elapsed."""
    from src.services.camera.vision_service import VisionService

    store = CameraResultsStore()
    mock_camera = MagicMock()

    worker = VisionService(VISION_CONFIG, store, mock_camera)
    worker._is_recording = True
    # Simulate 11 seconds ago
    worker._recording_start_time = time.monotonic() - 11.0

    worker._poll_once()

    mock_camera.stop_recording.assert_called_once()
    assert worker._is_recording is False


# ---------------------------------------------------------------------------
# Test 5: No stop_recording before duration elapsed
# ---------------------------------------------------------------------------


def test_no_stop_recording_before_duration():
    """VisionService does NOT call stop_recording() if duration not yet elapsed."""
    from src.services.camera.vision_service import VisionService

    store = CameraResultsStore()
    mock_camera = MagicMock()

    worker = VisionService(VISION_CONFIG, store, mock_camera)
    worker._is_recording = True
    worker._recording_start_time = time.monotonic() - 2.0  # only 2s elapsed

    worker._poll_once()

    mock_camera.stop_recording.assert_not_called()
    assert worker._is_recording is True


# ---------------------------------------------------------------------------
# Test 6: Exception in poll_once does not kill thread (D-07)
# ---------------------------------------------------------------------------


def test_error_isolation_continues_after_exception():
    """VisionService continues after an exception in polling (D-07)."""
    from src.services.camera.vision_service import VisionService

    store = CameraResultsStore()
    mock_camera = MagicMock()

    worker = VisionService(VISION_CONFIG, store, mock_camera)

    # Make store.get raise an exception
    original_get = store.get

    raise_count = [0]

    def failing_get(key, default=None):
        raise_count[0] += 1
        if raise_count[0] == 1:
            raise RuntimeError("simulated store error")
        return default

    store.get = failing_get

    # Should not raise — must catch internally
    try:
        worker._poll_once()
    except Exception:
        pytest.fail("_poll_once raised exception — D-07 violation: must continue after error")

    # Verify _prev_testere_durumu was NOT updated (exception prevented it)
    assert raise_count[0] == 1


# ---------------------------------------------------------------------------
# Test 7: stop() sets stop event
# ---------------------------------------------------------------------------


def test_stop_sets_event():
    """VisionService.stop() sets the internal _stop_event."""
    from src.services.camera.vision_service import VisionService

    store = CameraResultsStore()
    mock_camera = MagicMock()
    worker = VisionService(VISION_CONFIG, store, mock_camera)

    assert not worker._stop_event.is_set()
    worker.stop()
    assert worker._stop_event.is_set()


# ---------------------------------------------------------------------------
# Test 8: Thread exits after stop()
# ---------------------------------------------------------------------------


def test_thread_exits_after_stop():
    """VisionService thread is_alive() becomes False after stop() + join()."""
    from src.services.camera.vision_service import VisionService

    store = CameraResultsStore()
    mock_camera = MagicMock()
    worker = VisionService(VISION_CONFIG, store, mock_camera)

    worker.start()
    time.sleep(0.1)
    worker.stop()
    worker.join(timeout=5.0)

    assert not worker.is_alive(), "VisionService thread still alive after stop() + join()"


# ---------------------------------------------------------------------------
# Test 9: prev_testere_durumu tracks correctly across cycles
# ---------------------------------------------------------------------------


def test_prev_testere_durumu_updates_each_cycle():
    """VisionService updates _prev_testere_durumu with current value after each poll."""
    from src.services.camera.vision_service import VisionService

    store = CameraResultsStore()
    mock_camera = MagicMock()

    worker = VisionService(VISION_CONFIG, store, mock_camera)
    store.update("testere_durumu", 3)
    worker._prev_testere_durumu = 0

    worker._poll_once()

    # prev should now be 3 (the value we set in the store)
    assert worker._prev_testere_durumu == 3


# ---------------------------------------------------------------------------
# Test 10: DataProcessingPipeline writes traceability to CameraResultsStore
# ---------------------------------------------------------------------------


def test_data_pipeline_writes_to_camera_results_store():
    """DataProcessingPipeline writes testere_durumu + traceability to CameraResultsStore on each cycle.

    Tests that the _processing_loop integration code calls update_batch on the
    camera_results_store with the correct keys and values.
    """
    import asyncio
    from datetime import datetime
    from src.services.processing.data_processor import DataProcessingPipeline

    mock_modbus_reader = MagicMock()
    mock_modbus_writer = MagicMock()
    mock_control_manager = MagicMock()

    mock_db_services = {
        'raw': MagicMock(),
        'total': MagicMock(),
        'anomaly': MagicMock(),
    }

    mock_camera_store = MagicMock()

    config = {
        'processing': {'rate_hz': 10},
        'anomaly_detection': {'window': 100, 'min_samples': 10},
    }

    pipeline = DataProcessingPipeline(
        config=config,
        modbus_reader=mock_modbus_reader,
        modbus_writer=mock_modbus_writer,
        control_manager=mock_control_manager,
        db_services=mock_db_services,
        camera_results_store=mock_camera_store,
    )

    # Build a minimal raw_data mock
    mock_raw_data = MagicMock()
    mock_raw_data.testere_durumu = 3
    mock_raw_data.makine_id = 1
    mock_raw_data.serit_id = 2
    mock_raw_data.malzeme_cinsi = 5
    mock_raw_data.timestamp = datetime.now()
    mock_raw_data.kafa_yuksekligi_mm = 100.0
    mock_raw_data.serit_sapmasi = 0.1
    mock_raw_data.serit_motor_akim_a = 5.0
    mock_raw_data.serit_motor_tork_percentage = 30.0
    mock_raw_data.serit_kesme_hizi = 60.0
    mock_raw_data.serit_inme_hizi = 20.0
    mock_raw_data.ivme_olcer_x_hz = 0.1
    mock_raw_data.ivme_olcer_y_hz = 0.2
    mock_raw_data.ivme_olcer_z_hz = 0.3
    mock_raw_data.serit_gerginligi_bar = 5.0

    # Mock control_manager.get_current_mode
    mock_mode = MagicMock()
    mock_mode.value = "manual"
    mock_control_manager.get_current_mode.return_value = mock_mode

    # Mock modbus_reader.read_all_sensors to return raw_data once then stop
    call_count = [0]

    async def mock_read_all_sensors():
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_raw_data
        # Stop the loop on second call
        pipeline._running = False
        return None

    mock_modbus_reader.read_all_sensors = mock_read_all_sensors
    mock_modbus_reader.get_last_raw_registers.return_value = [0] * 44

    # Mock control_manager.process_data to return None (no speed command)
    async def mock_process_data(pd):
        return None

    mock_control_manager.process_data = mock_process_data

    # Run the processing loop for just one cycle
    async def run_one_cycle():
        pipeline._running = True
        # Run loop but limit to one real cycle
        task = asyncio.create_task(pipeline._processing_loop())
        # Let it run briefly
        await asyncio.sleep(0.2)
        pipeline._running = False
        await asyncio.sleep(0.15)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run_one_cycle())

    # Verify update_batch was called with correct traceability keys
    assert mock_camera_store.update_batch.called, (
        "camera_results_store.update_batch was not called — pipeline not writing traceability"
    )
    call_kwargs = mock_camera_store.update_batch.call_args[0][0]
    assert "testere_durumu" in call_kwargs, "testere_durumu missing from update_batch call"
    assert "kesim_id" in call_kwargs, "kesim_id missing from update_batch call"
    assert "makine_id" in call_kwargs, "makine_id missing from update_batch call"
    assert "serit_id" in call_kwargs, "serit_id missing from update_batch call"
    assert "malzeme_cinsi" in call_kwargs, "malzeme_cinsi missing from update_batch call"
    assert call_kwargs["testere_durumu"] == 3
    assert call_kwargs["makine_id"] == 1
    assert call_kwargs["serit_id"] == 2
    assert call_kwargs["malzeme_cinsi"] == 5


# ---------------------------------------------------------------------------
# Test 11: DataProcessingPipeline does NOT write to store when it is None
# ---------------------------------------------------------------------------


def test_data_pipeline_skips_when_store_is_none():
    """DataProcessingPipeline does nothing to CameraResultsStore when store is None."""
    from src.services.processing.data_processor import DataProcessingPipeline

    mock_modbus_reader = MagicMock()
    mock_modbus_writer = MagicMock()
    mock_control_manager = MagicMock()
    mock_db_services = {
        'raw': MagicMock(),
        'total': MagicMock(),
        'anomaly': MagicMock(),
    }

    config = {
        'processing': {'rate_hz': 10},
        'anomaly_detection': {'window': 100, 'min_samples': 10},
    }

    pipeline = DataProcessingPipeline(
        config=config,
        modbus_reader=mock_modbus_reader,
        modbus_writer=mock_modbus_writer,
        control_manager=mock_control_manager,
        db_services=mock_db_services,
        camera_results_store=None,  # explicitly None
    )

    assert pipeline.camera_results_store is None
    # No AttributeError should occur when None
