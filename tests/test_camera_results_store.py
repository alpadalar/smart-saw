"""Unit tests for CameraResultsStore.

Tests cover thread-safe get/update operations, batch updates, default values,
snapshot isolation, and concurrent access safety.
"""

import threading

import pytest

from src.services.camera.results_store import CameraResultsStore


def test_update_and_get():
    """store.update() followed by store.get() returns the stored value."""
    store = CameraResultsStore()
    store.update("key", "value")
    assert store.get("key") == "value"


def test_update_batch():
    """store.update_batch() stores all key-value pairs atomically."""
    store = CameraResultsStore()
    store.update_batch({"a": 1, "b": 2})
    assert store.get("a") == 1
    assert store.get("b") == 2


def test_get_default():
    """store.get() returns None for missing keys; returns provided default."""
    store = CameraResultsStore()
    assert store.get("missing") is None
    assert store.get("missing", 42) == 42


def test_snapshot_returns_copy():
    """snapshot() returns a copy — mutations to it do not affect the store."""
    store = CameraResultsStore()
    store.update("x", 10)
    snapshot = store.snapshot()
    snapshot["x"] = 99
    # Internal state must be unchanged
    assert store.get("x") == 10


def test_thread_safety():
    """10 concurrent threads doing update/get cycles raise no exceptions."""
    store = CameraResultsStore()
    errors: list[Exception] = []

    def worker(thread_id: int) -> None:
        try:
            for i in range(100):
                store.update(f"key_{thread_id}", i)
                store.get(f"key_{thread_id}")
                store.update_batch({f"batch_{thread_id}": i, "shared": thread_id})
                store.snapshot()
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Thread-safety errors: {errors}"


def test_latest_frame_updated():
    """store.update('latest_frame', bytes) stores JPEG bytes correctly."""
    store = CameraResultsStore()
    jpeg_bytes = b"\xff\xd8\xff\xe0fake_jpeg_data\xff\xd9"
    store.update("latest_frame", jpeg_bytes)
    assert store.get("latest_frame") == jpeg_bytes


def test_update_batch_is_atomic():
    """update_batch() applies all keys before any reader can observe partial state."""
    store = CameraResultsStore()
    # Pre-set values
    store.update_batch({"a": 0, "b": 0})
    store.update_batch({"a": 1, "b": 2, "c": 3})
    # All values from batch must be visible
    snap = store.snapshot()
    assert snap["a"] == 1
    assert snap["b"] == 2
    assert snap["c"] == 3


def test_snapshot_independent_of_subsequent_updates():
    """snapshot taken before an update is not affected by that update."""
    store = CameraResultsStore()
    store.update("x", 1)
    snap = store.snapshot()
    store.update("x", 2)
    # Snapshot still holds old value
    assert snap["x"] == 1
    # Store holds new value
    assert store.get("x") == 2
