"""Camera capture service with threaded frame capture, JPEG encoding, auto-discovery, and retry.

CameraService manages the full capture pipeline:
- Discovers camera device via auto-discovery (scans device IDs from config hint — D-05)
- Opens a platform-aware VideoCapture device (CAP_DSHOW on Windows, default backend elsewhere)
- Runs a daemon capture thread that reads frames, tracks fps_actual, and pushes JPEG bytes
  to CameraResultsStore for downstream consumers (GUI, IoT, detection workers)
- Runs N daemon save-worker threads that drain a frame queue and write JPEG files to disk
  during recording sessions
- Retries for 30 seconds on capture loss before stopping the thread (D-06)

All shared camera state is exposed through CameraResultsStore — no direct cross-thread field
access outside this module. Constructor does no I/O; call start() to open the device.
"""

from __future__ import annotations

import logging
import os
import queue
import sys
import threading
import time
from collections import deque
from datetime import datetime
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np

if TYPE_CHECKING:
    from src.services.camera.results_store import CameraResultsStore

logger = logging.getLogger(__name__)

_DISCOVERY_RANGE = 4  # Number of device IDs to scan (0-3)
_RETRY_DURATION = 30.0  # Seconds to retry on capture loss (D-06)
_FPS_WINDOW_SIZE = 30  # Frames for moving average FPS calculation
_FRAME_QUEUE_SIZE = 100  # Max queued frames for save workers


class CameraService:
    """Config-driven camera capture with threaded JPEG encoding, auto-discovery, and retry.

    Constructor does no I/O — call ``start()`` to discover and open the device.

    Lifecycle::

        service = CameraService(config, results_store)
        await service.start()     # Opens device, spawns threads
        service.start_recording() # Begin writing JPEG frames to disk
        service.stop_recording()  # Flush and stop recording
        await service.stop()      # Shut down threads, release device

    Thread model:
        - One daemon capture thread ("camera-capture") reads frames from VideoCapture.
        - N daemon save-worker threads ("camera-save-{i}") drain a Queue and write JPEG files.
        - All shared state crosses thread boundaries only via CameraResultsStore (lock-protected).
        - The asyncio event loop is never accessed from capture/save threads.
    """

    def __init__(self, config: dict[str, Any], results_store: CameraResultsStore) -> None:
        """Initialize CameraService with config and a results store.

        Does no I/O. VideoCapture is opened in start().

        Args:
            config: Camera configuration dict with keys: device_id, resolution.width,
                resolution.height, fps, jpeg_quality, recordings_path.
            results_store: Thread-safe store for publishing camera state to consumers.
        """
        self._config = config
        self._results_store = results_store

        # Config extraction
        self._device_id: int = config.get("device_id", 0)
        resolution = config.get("resolution", {})
        self._width: int = resolution.get("width", 640)
        self._height: int = resolution.get("height", 480)
        self._fps: int = config.get("fps", 30)
        self._jpeg_quality: int = config.get("jpeg_quality", 85)
        self._recordings_path: str = config.get("recordings_path", "data/recordings")

        # Capture state
        self._cap: cv2.VideoCapture | None = None
        self._stop_event = threading.Event()
        self._frame_queue: queue.Queue = queue.Queue(maxsize=_FRAME_QUEUE_SIZE)
        self._capture_thread: threading.Thread | None = None
        self._save_threads: list[threading.Thread] = []
        self._current_frame: np.ndarray | None = None
        self._frame_lock = threading.Lock()
        self._is_running = False

        # Recording state
        self._is_recording = False
        self._frame_count = 0
        self._recording_dir: str | None = None

        # Worker pool size
        self._num_save_threads = min(4, os.cpu_count() or 2)

    # -- auto-discovery ----------------------------------------------------

    def _open_device(self, device_id: int) -> cv2.VideoCapture | None:
        """Attempt to open a single VideoCapture device.

        Uses the DirectShow backend on Windows and the default backend elsewhere
        to avoid symbol conflicts with PySide6.

        Args:
            device_id: OpenCV device index to try.

        Returns:
            An opened VideoCapture, or None if the device is unavailable.
        """
        if sys.platform.startswith("win"):
            cap = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(device_id)

        if not cap.isOpened():
            cap.release()
            return None
        return cap

    def _discover_camera(self) -> cv2.VideoCapture | None:
        """Scan device IDs and return the first openable VideoCapture.

        Starts scanning from the config ``device_id`` hint, wrapping around
        through ``_DISCOVERY_RANGE`` total IDs. Using the config hint as start
        makes the common case (hint is correct) a single-attempt success while
        still recovering from ID shifts in industrial environments.

        Returns:
            An opened VideoCapture, or None if no device was found.
        """
        hint = self._device_id
        for offset in range(_DISCOVERY_RANGE):
            dev_id = (hint + offset) % _DISCOVERY_RANGE
            cap = self._open_device(dev_id)
            if cap is not None:
                if dev_id != hint:
                    logger.info(
                        "Camera auto-discovered at device_id=%d (config hint was %d)",
                        dev_id,
                        hint,
                    )
                return cap
        return None

    # -- lifecycle ---------------------------------------------------------

    async def start(self) -> bool:
        """Open camera device and spawn capture and save threads.

        Discovers the camera via auto-discovery (D-05). Returns False — never
        raises — when no device is found, so lifecycle.py can continue without
        camera services.

        Returns:
            True if the camera was opened and threads started; False otherwise.
        """
        if self._is_running:
            return False

        cap = self._discover_camera()
        if cap is None:
            logger.error(
                "Camera open failed — no device found in range 0-%d (hint=%d)",
                _DISCOVERY_RANGE - 1,
                self._device_id,
            )
            return False

        # Apply requested settings
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        cap.set(cv2.CAP_PROP_FPS, self._fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Log actual negotiated values (may differ from requested — Pitfall 1)
        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        logger.info(
            "Camera opened — device_id=%d, requested=%dx%d@%dfps, actual=%dx%d@%.1ffps",
            self._device_id,
            self._width,
            self._height,
            self._fps,
            actual_w,
            actual_h,
            actual_fps,
        )

        self._cap = cap
        self._stop_event.clear()

        # Spawn capture thread
        self._capture_thread = threading.Thread(
            target=self._capture_loop, daemon=True, name="camera-capture"
        )
        self._capture_thread.start()

        # Spawn save worker pool
        self._save_threads = []
        for i in range(self._num_save_threads):
            t = threading.Thread(
                target=self._save_worker, daemon=True, name=f"camera-save-{i}"
            )
            t.start()
            self._save_threads.append(t)

        self._is_running = True
        self._results_store.update_batch(
            {
                "is_recording": False,
                "frame_count": 0,
                "fps_actual": 0.0,
                "latest_frame": None,
                "recording_path": None,
            }
        )
        return True

    async def stop(self) -> None:
        """Signal threads to stop, flush the frame queue, and release the camera device.

        Safe to call when not running (no-op).
        """
        if not self._is_running:
            return

        self._stop_event.set()

        # Stop recording first (flushes remaining frames via frame_queue.join())
        if self._is_recording:
            self.stop_recording()

        # Send None sentinels so save workers exit their while-True loop cleanly
        for _ in self._save_threads:
            try:
                self._frame_queue.put(None, timeout=1.0)
            except queue.Full:
                pass

        # Join save workers
        for t in self._save_threads:
            t.join(timeout=2.0)
        self._save_threads.clear()

        # Join capture thread
        if self._capture_thread is not None:
            self._capture_thread.join(timeout=2.0)
            self._capture_thread = None

        # Release camera device (Pitfall 6 — always release even on exception)
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                logger.debug("VideoCapture.release() raised (ignoring)", exc_info=True)
            self._cap = None

        self._is_running = False
        logger.info("Camera service stopped")

    # -- capture thread ----------------------------------------------------

    def _capture_loop(self) -> None:
        """Read frames continuously and push JPEG bytes to results store.

        Runs in a daemon thread. Implements 30-second retry on read failure (D-06).
        When recording is active, also enqueues raw frames for the save-worker pool.
        """
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]
        fps_window: deque[float] = deque(maxlen=_FPS_WINDOW_SIZE)
        _retry_deadline: float | None = None

        while not self._stop_event.is_set():
            ret, frame = self._cap.read()

            if not ret:
                # D-06: retry for _RETRY_DURATION seconds before giving up
                if _retry_deadline is None:
                    _retry_deadline = time.monotonic() + _RETRY_DURATION
                    logger.warning(
                        "Camera read failed — retrying for %.0fs before stopping",
                        _RETRY_DURATION,
                    )
                if time.monotonic() > _retry_deadline:
                    logger.error(
                        "Camera read failed for %.0fs — stopping capture thread",
                        _RETRY_DURATION,
                    )
                    break
                time.sleep(0.1)
                continue

            # Successful read — reset retry deadline
            _retry_deadline = None

            # Store raw frame under lock for in-process consumers (e.g. detection workers)
            with self._frame_lock:
                self._current_frame = frame

            # JPEG encode and push to results store for GUI / IoT consumers
            ok, jpeg_buf = cv2.imencode(".jpg", frame, encode_params)
            if ok:
                self._results_store.update("latest_frame", jpeg_buf.tobytes())

            # Track fps_actual with a moving average (Pitfall 1 mitigation)
            fps_window.append(time.monotonic())
            if len(fps_window) >= 2:
                fps = (len(fps_window) - 1) / (fps_window[-1] - fps_window[0])
                # Update store every _FPS_WINDOW_SIZE frames to reduce lock contention
                if len(fps_window) == _FPS_WINDOW_SIZE:
                    self._results_store.update("fps_actual", round(fps, 1))

            # Enqueue for disk save when recording is active
            if self._is_recording and self._recording_dir:
                self._frame_count += 1
                try:
                    self._frame_queue.put_nowait(
                        (self._frame_count, frame.copy(), self._recording_dir)
                    )
                except queue.Full:
                    logger.warning(
                        "Frame queue full — dropping frame %d", self._frame_count
                    )
                self._results_store.update("frame_count", self._frame_count)
                if self._frame_count % 100 == 0:
                    logger.info(
                        "Recording progress — frame_count=%d", self._frame_count
                    )

    # -- save workers ------------------------------------------------------

    def _save_worker(self) -> None:
        """Drain frame queue and write JPEG files to disk.

        Runs in a daemon thread. Exits when it receives a None sentinel.
        Always calls task_done() to prevent frame_queue.join() from hanging
        (Pitfall 2 — sentinel and exception paths both reach finally).
        """
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]

        while True:
            item = self._frame_queue.get()
            if item is None:
                # Sentinel — clean shutdown
                self._frame_queue.task_done()
                break
            try:
                count, frame, output_dir = item
                path = os.path.join(output_dir, f"frame_{count:06d}.jpg")
                cv2.imwrite(path, frame, encode_params)
            except Exception:
                logger.error("Save worker error writing frame to disk", exc_info=True)
            finally:
                self._frame_queue.task_done()

    # -- recording ---------------------------------------------------------

    def start_recording(self) -> bool:
        """Begin writing captured frames to a timestamped directory.

        Creates a new subdirectory under ``recordings_path`` with the current
        timestamp as the name (YYYYMMDD-HHMMSS). Per D-03 and D-04, the caller
        (Phase 22 VisionService) is responsible for deciding when to start.

        Returns:
            True if recording started; False if already running or service not started.
        """
        if not self._is_running or self._is_recording:
            return False

        recording_dir = os.path.join(
            self._recordings_path,
            datetime.now().strftime("%Y%m%d-%H%M%S"),
        )
        os.makedirs(recording_dir, exist_ok=True)

        self._recording_dir = recording_dir
        self._frame_count = 0
        self._is_recording = True

        self._results_store.update_batch(
            {
                "is_recording": True,
                "frame_count": 0,
                "recording_path": recording_dir,
            }
        )
        logger.info("Recording started — path=%s", recording_dir)
        return True

    def stop_recording(self) -> bool:
        """Stop recording and flush remaining frames to disk.

        Calls ``frame_queue.join()`` to wait for save workers to finish writing
        all queued frames before returning. Safe because save workers always call
        ``task_done()`` in their ``finally`` block (Pitfall 2).

        Returns:
            True if recording was stopped; False if recording was not active.
        """
        if not self._is_recording:
            return False

        self._is_recording = False

        # Wait for all queued frames to be written before returning
        self._frame_queue.join()

        self._results_store.update_batch(
            {"is_recording": False, "recording_path": None}
        )
        logger.info("Recording stopped — total_frames=%d", self._frame_count)
        return True

    # -- accessors ---------------------------------------------------------

    def get_current_frame(self) -> np.ndarray | None:
        """Return the latest raw frame (numpy array) for detection workers.

        Returns the stored reference under a lock. Detection workers must
        ``.copy()`` the frame if they need to hold it across a long inference
        call (Pitfall 3).

        Returns:
            The most recent numpy frame, or None if no frame has been captured yet.
        """
        with self._frame_lock:
            return self._current_frame

    @property
    def is_running(self) -> bool:
        """Whether the capture pipeline is active.

        Returns:
            True if start() completed successfully and stop() has not been called.
        """
        return self._is_running
