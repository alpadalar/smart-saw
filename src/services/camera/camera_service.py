"""
Camera capture service with threaded frame capture and JPEG encoding.

CameraService manages the full capture pipeline:
- Opens a platform-aware VideoCapture device
- Runs a daemon capture thread that reads frames and pushes JPEG bytes
  into CameraResultsStore for downstream consumers
- Runs N daemon save-worker threads that drain a frame queue and write
  JPEG files to disk during recording

All shared camera state is exposed through CameraResultsStore —
no direct cross-thread field access outside this module.
"""

from __future__ import annotations

import logging
import os
import queue
import sys
import threading
import time
from datetime import datetime
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    from src.services.camera.results_store import CameraResultsStore

logger = logging.getLogger(__name__)


class CameraService:
    """Config-driven camera capture with threaded JPEG encoding.

    Constructor does no I/O — call ``start()`` to open the device.
    """

    def __init__(self, config: dict, results_store: CameraResultsStore) -> None:
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
        self._frame_queue: queue.Queue = queue.Queue(maxsize=100)
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

    # -- lifecycle ---------------------------------------------------------

    async def start(self) -> bool:
        """Open camera and spawn capture + save threads.

        Returns False (no crash) if the device cannot be opened.
        """
        if self._is_running:
            return False

        # Platform-aware backend
        if sys.platform.startswith("win"):
            cap = cv2.VideoCapture(self._device_id, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(self._device_id)

        if not cap.isOpened():
            logger.error(
                "Camera open failed — device_id=%s not available", self._device_id
            )
            cap.release()
            return False

        # Apply requested settings
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        cap.set(cv2.CAP_PROP_FPS, self._fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Log actual negotiated values
        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
        logger.info(
            "Camera opened — device_id=%s, resolution=%dx%d, fps=%d",
            self._device_id,
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
            {"is_recording": False, "frame_count": 0, "fps_actual": 0.0}
        )
        return True

    async def stop(self) -> None:
        """Signal threads and release camera device."""
        if not self._is_running:
            return

        self._stop_event.set()

        # Stop recording first (flushes queue)
        if self._is_recording:
            self.stop_recording()

        # Send None sentinels so save workers exit cleanly
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

        # Release camera
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

        self._is_running = False
        logger.info("Camera service stopped")

    # -- capture thread ----------------------------------------------------

    def _capture_loop(self) -> None:
        """Read frames continuously and push JPEG bytes to results store.

        Runs in a daemon thread. When recording, also enqueues raw frames
        for the save-worker pool.
        """
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]

        while not self._stop_event.is_set():
            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            # Store raw frame for in-process consumers (e.g. detection)
            with self._frame_lock:
                self._current_frame = frame

            # JPEG encode and push to results store for GUI / IoT consumers
            ok, jpeg_buf = cv2.imencode(".jpg", frame, encode_params)
            if ok:
                self._results_store.update("latest_frame", jpeg_buf.tobytes())

            # Enqueue for disk save when recording
            if self._is_recording and self._recording_dir:
                self._frame_count += 1
                try:
                    self._frame_queue.put_nowait(
                        (self._frame_count, frame.copy(), self._recording_dir)
                    )
                except queue.Full:
                    logger.warning("Frame queue full, dropping frame")
                self._results_store.update("frame_count", self._frame_count)
                if self._frame_count % 100 == 0:
                    logger.info(
                        "Recording progress — frame_count=%d", self._frame_count
                    )

    # -- save workers ------------------------------------------------------

    def _save_worker(self) -> None:
        """Drain frame queue and write JPEG files to disk.

        Runs in a daemon thread. Exits when it receives a None sentinel.
        """
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]

        while True:
            item = self._frame_queue.get()
            if item is None:
                self._frame_queue.task_done()
                break
            try:
                count, frame, output_dir = item
                path = os.path.join(output_dir, f"frame_{count:06d}.jpg")
                cv2.imwrite(path, frame, encode_params)
            except Exception:
                logger.error("Save worker error", exc_info=True)
            finally:
                self._frame_queue.task_done()

    # -- recording ---------------------------------------------------------

    def start_recording(self) -> bool:
        """Begin writing captured frames to a timestamped directory."""
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
        """Stop recording and flush remaining frames to disk."""
        if not self._is_recording:
            return False

        self._is_recording = False

        # Wait for queued frames to be written
        self._frame_queue.join()

        self._results_store.update_batch(
            {"is_recording": False, "recording_path": None}
        )
        logger.info("Recording stopped — total_frames=%d", self._frame_count)
        return True

    # -- accessors ---------------------------------------------------------

    def get_current_frame(self) -> np.ndarray | None:
        """Return the latest raw frame (numpy array) for detection workers."""
        with self._frame_lock:
            return self._current_frame

    @property
    def is_running(self) -> bool:
        """Whether the capture pipeline is active."""
        return self._is_running
