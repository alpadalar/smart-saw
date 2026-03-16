---
id: S20
parent: M001
milestone: M001
provides:
  - CameraResultsStore — thread-safe Lock-guarded key-value store as integration boundary for all camera data consumers
  - CameraService — config-driven capture engine with daemon capture thread, JPEG encoder pool, and timestamped recording
  - opencv-python-headless dependency declared and installed
  - S19 foundation merged (camera config, DB schema, lifecycle stub, camera scaffold, numpy uncap)
requires:
  - slice: S19
    provides: camera config section in config.yaml, SCHEMA_CAMERA_DB in schemas.py, _init_camera() stub in lifecycle.py, camera __init__.py scaffold, numpy uncap
affects:
  - S21
  - S22
  - S23
  - S24
key_files:
  - src/services/camera/results_store.py
  - src/services/camera/camera_service.py
  - src/services/camera/__init__.py
  - requirements.txt
key_decisions:
  - CameraResultsStore uses threading.Lock (not RLock) — simple, sufficient for single-level lock acquisition
  - snapshot() returns shallow copy via dict() — cheap for expected key count (~5 standard keys)
  - opencv-python-headless chosen over opencv-python to avoid Qt5/Qt6 conflict with PySide6
  - CameraResultsStore stores latest_frame as JPEG bytes (compact for GUI/IoT); raw numpy via get_current_frame() for detection
  - put_nowait() with queue.Full catch — capture thread never stalls, frames drop under backpressure
  - None sentinels for clean daemon thread shutdown
  - Platform-aware VideoCapture backend (CAP_DSHOW on Windows)
patterns_established:
  - Thread-safe store pattern — Lock-guarded dict with update/get/snapshot API as integration boundary between threads
  - Async start/stop with internal OS threads — matches existing service pattern while using threaded capture
  - put_nowait() drop-on-full for bounded queue backpressure
observability_surfaces:
  - CameraResultsStore.snapshot() — returns full state dict (latest_frame, frame_count, is_recording, recording_path, fps_actual)
  - CameraService.is_running property
  - logger.info on camera open success with actual resolution/FPS
  - logger.info on recording start/stop with path and frame count
  - logger.info every 100 frames during recording
  - logger.warning on frame queue full (drop)
  - logger.error on camera open failure with device_id
drill_down_paths:
  - .gsd/milestones/M001/slices/S20/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S20/tasks/T02-SUMMARY.md
duration: 30m
verification_result: passed
completed_at: 2026-03-16
---

# S20: Camera Capture

**OpenCV capture engine with threaded JPEG encoding, recording to disk, and CameraResultsStore as the thread-safe integration boundary for all downstream consumers.**

## What Happened

Cherry-picked S19 foundation commits into the worktree branch — camera config section in `config.yaml`, `SCHEMA_CAMERA_DB` in `schemas.py`, `_init_camera()` stub in `lifecycle.py`, camera `__init__.py` scaffold, and numpy uncap. No conflicts.

Built `CameraResultsStore` as the sole integration boundary between camera threads and all consumers (GUI, IoT, detection, DB). Simple Lock-guarded dict with `update()`, `update_batch()`, `get()`, and `snapshot()` (returns shallow copy — consumers never hold a reference to internal state).

Built `CameraService` as a config-driven capture engine:
- Constructor extracts config (device_id, resolution, fps, jpeg_quality, recordings_path), does no I/O
- `async start()` opens platform-aware VideoCapture, logs actual negotiated resolution/FPS, spawns 1 capture daemon thread + N save daemon threads (min(4, cpu_count))
- Capture thread reads frames continuously, stores raw numpy under frame_lock for `get_current_frame()` (S21 detection), JPEG-encodes and pushes bytes to results_store for GUI/IoT
- When recording, enqueues frames for disk save with `put_nowait()` / `queue.Full` catch — capture never stalls
- `start_recording()` creates timestamped directories (`YYYYMMDD-HHMMSS/frame_NNNNNN.jpg`)
- `async stop()` signals stop_event, sends None sentinels, joins threads with timeout, releases camera
- Graceful handling when camera not connected — logs error, returns False, no crash

Added `opencv-python-headless>=4.11.0` to requirements.txt (headless variant avoids Qt conflict with PySide6). Updated `__init__.py` to export both CameraResultsStore and CameraService.

## Verification

All 9 slice-level checks passed:
- ✅ CameraResultsStore thread-safe store works, snapshot returns independent copy
- ✅ CameraService import succeeds (cv2 installed)
- ✅ cv2 version 4.11.0
- ✅ `opencv-python-headless` in requirements.txt
- ✅ `__init__.py` exports both CameraResultsStore and CameraService
- ✅ CameraService instantiation with config dict (no camera needed)
- ✅ Graceful failure with non-existent camera (device_id=99) — returns False, logs error, no crash
- ✅ Fresh store snapshot() returns `{}`
- ✅ Zero-import guard preserved — no top-level camera imports in lifecycle.py

## Requirements Advanced

- CAM-03 — OpenCV capture implemented with configurable resolution and FPS from config dict
- CAM-04 — Multi-thread JPEG encoder pool writes frames to disk during recording
- CAM-05 — Timestamped recording directory structure (`YYYYMMDD-HHMMSS/frame_NNNNNN.jpg`)
- DET-05 — CameraResultsStore built as thread-safe integration boundary for all camera data consumers

## Requirements Validated

- none — capture engine built but cannot be validated without a real camera; S22 lifecycle wiring needed for end-to-end

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

None.

## Known Limitations

- No real camera test possible in dev environment — only contract verification (import, instantiation, graceful failure)
- CameraService not wired into lifecycle yet — requires S22
- No detection logic — requires S21
- `_capture_loop` frame counter uses simple increment without thread protection for `_frame_count` — acceptable because only the single capture thread writes to it

## Follow-ups

- none — all remaining work is planned in S21-S24

## Files Created/Modified

- `src/services/camera/results_store.py` — New: CameraResultsStore class with thread-safe Lock-guarded dict
- `src/services/camera/camera_service.py` — New: CameraService class with full capture pipeline (capture thread, save worker pool, recording management)
- `src/services/camera/__init__.py` — Updated: exports CameraResultsStore and CameraService
- `requirements.txt` — Added opencv-python-headless>=4.11.0
- `config/config.yaml` — Camera config section (from S19 cherry-pick)
- `src/services/database/schemas.py` — SCHEMA_CAMERA_DB (from S19 cherry-pick)
- `src/core/lifecycle.py` — _init_camera() stub (from S19 cherry-pick)
- `src/anomaly/base.py` — np.ptp() replacement (from S19 cherry-pick)

## Forward Intelligence

### What the next slice should know
- `CameraResultsStore` is the only way to share camera state across threads — detection workers (S21) should write their results here too
- `CameraService.get_current_frame()` returns raw numpy array — this is the feed point for RT-DETR and LDC detection workers
- `latest_frame` in the store is JPEG bytes, not numpy — GUI can use directly, detection workers must use `get_current_frame()`
- Standard store keys when running: `latest_frame`, `frame_count`, `is_recording`, `recording_path`, `fps_actual`
- S21 should add keys like `broken_count`, `crack_count`, `wear_percentage`, `health_score` to the same store

### What's fragile
- `__init__.py` imports both CameraResultsStore and CameraService unconditionally — if the zero-import guard in lifecycle is ever removed, cv2 will be loaded even when camera is disabled. S22 must preserve the conditional import pattern in lifecycle.

### Authoritative diagnostics
- `CameraResultsStore.snapshot()` — returns all current camera state in one call, trustworthy because it's Lock-guarded and returns a copy
- `CameraService.is_running` — single boolean for quick alive check
- Grep for "Camera open failed" or "Frame queue full" in logs for failure diagnosis

### What assumptions changed
- No assumptions changed — S19 foundation cherry-picked cleanly, all planned interfaces implemented as designed
