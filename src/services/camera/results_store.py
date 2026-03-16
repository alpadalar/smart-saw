"""
Thread-safe results store for camera data.

CameraResultsStore is the sole integration boundary between camera capture
threads and all downstream consumers (GUI, IoT, detection, DB). All access
to shared camera state goes through this store.

Standard keys:
    latest_frame  (bytes)      — Most recent JPEG-encoded frame
    frame_count   (int)        — Total frames captured since start
    is_recording  (bool)       — Whether recording is active
    recording_path (str|None)  — Current recording directory path
    fps_actual    (float)      — Measured capture FPS
"""

import threading
from typing import Any


class CameraResultsStore:
    """Thread-safe key-value store for camera pipeline state.

    All methods acquire the internal lock before touching ``_data``.
    ``snapshot()`` returns a shallow copy so callers never hold a
    reference into the live dict.
    """

    def __init__(self) -> None:
        self._data: dict = {}
        self._lock = threading.Lock()

    # -- mutators ----------------------------------------------------------

    def update(self, key: str, value: Any) -> None:
        """Set a single key."""
        with self._lock:
            self._data[key] = value

    def update_batch(self, data: dict) -> None:
        """Merge *data* into the store atomically."""
        with self._lock:
            self._data.update(data)

    # -- accessors ---------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return value for *key*, or *default* if absent."""
        with self._lock:
            return self._data.get(key, default)

    def snapshot(self) -> dict:
        """Return a shallow copy of the entire store.

        The returned dict is independent of internal state — mutations
        to the store after this call do not affect the snapshot, and
        vice-versa.
        """
        with self._lock:
            return dict(self._data)
