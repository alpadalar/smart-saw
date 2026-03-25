"""Thread-safe results store for camera pipeline state.

CameraResultsStore is the sole integration boundary between camera capture
threads and all downstream consumers (GUI, IoT, detection, DB). All shared
camera state flows through this store — no direct cross-thread field access.

Standard keys:
    latest_frame  (bytes | None) — Most recent JPEG-encoded frame bytes
    frame_count   (int)          — Total frames captured since start
    is_recording  (bool)         — Whether recording is currently active
    recording_path (str | None)  — Current recording directory path
    fps_actual    (float)        — Measured capture FPS (moving average)
"""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)


class CameraResultsStore:
    """Thread-safe key-value store for camera pipeline state.

    All methods acquire the internal ``_lock`` before touching ``_data``.
    ``snapshot()`` returns a shallow copy so callers never hold a reference
    into the live dict — mutations to the snapshot do not affect the store,
    and mutations to the store after snapshot() do not affect older snapshots.

    Usage::

        store = CameraResultsStore()
        store.update("latest_frame", jpeg_bytes)
        frame = store.get("latest_frame")
        snap = store.snapshot()
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._lock = threading.Lock()

    # -- mutators ----------------------------------------------------------

    def update(self, key: str, value: Any) -> None:
        """Set a single key atomically.

        Args:
            key: The key to set.
            value: The value to store under ``key``.
        """
        with self._lock:
            self._data[key] = value

    def update_batch(self, data: dict[str, Any]) -> None:
        """Merge multiple key-value pairs atomically.

        All pairs in ``data`` are applied inside a single lock acquisition,
        so readers either see all the updates or none of them.

        Args:
            data: Dict of key-value pairs to merge into the store.
        """
        with self._lock:
            self._data.update(data)

    # -- accessors ---------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return value for key, or default if absent.

        Args:
            key: The key to look up.
            default: Value returned when ``key`` is not present. Defaults to None.

        Returns:
            The stored value, or ``default`` if the key does not exist.
        """
        with self._lock:
            return self._data.get(key, default)

    def snapshot(self) -> dict[str, Any]:
        """Return a shallow copy of the entire store.

        The returned dict is fully independent of internal state — mutations
        to the store after this call do not affect the snapshot, and mutations
        to the snapshot do not affect the store.

        Returns:
            A shallow copy of all current key-value pairs.
        """
        with self._lock:
            return dict(self._data)
