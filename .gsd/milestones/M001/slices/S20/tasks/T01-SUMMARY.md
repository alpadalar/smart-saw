---
id: T01
parent: S20
milestone: M001
provides:
  - CameraResultsStore class — thread-safe key-value store for camera pipeline state
  - S19 foundation artifacts merged (camera config, DB schema, lifecycle stub, camera scaffold, numpy uncap)
  - opencv-python-headless dependency declared and installed
key_files:
  - src/services/camera/results_store.py
  - src/services/camera/__init__.py
  - requirements.txt
key_decisions:
  - CameraResultsStore uses threading.Lock (not RLock) — simple, sufficient for single-level lock acquisition
  - snapshot() returns shallow copy via dict() — cheap for expected key count (~5 standard keys)
  - opencv-python-headless chosen over opencv-python to avoid Qt5/Qt6 conflict with PySide6
patterns_established:
  - Thread-safe store pattern: Lock-guarded dict with update/get/snapshot API as the integration boundary between threads
observability_surfaces:
  - CameraResultsStore.snapshot() — returns full state dict for diagnostic inspection
duration: 15m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Merge S19 foundation and build CameraResultsStore

**Cherry-picked S19 foundation (camera config, DB schema, lifecycle stub, numpy uncap) and built CameraResultsStore as the thread-safe integration boundary for all camera data consumers.**

## What Happened

Cherry-picked commits `8dfbdb0` and `2131ac2` cleanly into the worktree branch — no conflicts. These brought in: camera config section in `config/config.yaml`, `SCHEMA_CAMERA_DB` in `schemas.py`, `_init_camera()` in `lifecycle.py`, `src/services/camera/__init__.py` scaffold, and numpy uncap to `>=1.24.0`.

Added `opencv-python-headless>=4.11.0` to requirements.txt (headless variant avoids Qt conflict with PySide6). Already installed at 4.11.0.

Created `CameraResultsStore` in `src/services/camera/results_store.py` — a Lock-guarded dict with `update()`, `update_batch()`, `get()`, and `snapshot()`. `snapshot()` returns a shallow copy so consumers never hold a reference to internal state. Updated `__init__.py` to export it.

## Verification

All task-level checks passed:
- ✅ `CameraResultsStore` import, update, get, snapshot (copy semantics verified)
- ✅ `update_batch()` and `get()` with defaults
- ✅ `import cv2` → 4.11.0
- ✅ `opencv-python-headless` in requirements.txt
- ✅ `SCHEMA_CAMERA_DB` in schemas.py
- ✅ `_init_camera` in lifecycle.py
- ✅ `camera:` in config.yaml
- ✅ Fresh store `snapshot()` returns `{}`

Slice-level checks (partial — T02 not yet built):
- ✅ CameraResultsStore thread-safe store works, snapshot returns copy
- ✅ opencv-python-headless installed, `import cv2` succeeds
- ✅ `opencv-python-headless` in requirements.txt
- ⬜ CameraService import (T02)
- ⬜ `__init__.py` exports both classes (T02)
- ⬜ CameraService instantiation (T02)
- ⬜ Application startup with `camera.enabled: false` (T02)

## Diagnostics

- `CameraResultsStore.snapshot()` returns full state dict — call from any thread to inspect camera pipeline state
- Fresh store returns `{}` — useful baseline to confirm store is empty before service starts

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/services/camera/results_store.py` — New: CameraResultsStore class with thread-safe Lock-guarded dict
- `src/services/camera/__init__.py` — Updated: exports CameraResultsStore
- `requirements.txt` — Added opencv-python-headless>=4.11.0
- `config/config.yaml` — Camera config section (from S19 cherry-pick)
- `src/services/database/schemas.py` — SCHEMA_CAMERA_DB (from S19 cherry-pick)
- `src/core/lifecycle.py` — _init_camera() stub (from S19 cherry-pick)
- `src/anomaly/base.py` — np.ptp() replacement (from S19 cherry-pick)
