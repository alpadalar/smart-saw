---
id: T02
parent: S20
milestone: M001
provides:
  - CameraService class — config-driven capture engine with daemon capture thread, JPEG encoder pool, and recording to disk
key_files:
  - src/services/camera/camera_service.py
  - src/services/camera/__init__.py
key_decisions:
  - None new — T01 decisions (JPEG bytes in store, raw numpy via get_current_frame, opencv-headless) carried forward
patterns_established:
  - Async start/stop with internal OS threads — matches existing service pattern while using threaded capture
  - put_nowait() with queue.Full catch — capture thread never stalls, frames drop under backpressure
  - None sentinels for clean daemon thread shutdown
observability_surfaces:
  - logger.info on camera open success with actual resolution/FPS
  - logger.info on recording start/stop with path and frame count
  - logger.info every 100 frames during recording
  - logger.warning on frame queue full (drop)
  - logger.error on camera open failure with device_id
  - CameraResultsStore.snapshot() exposes is_recording, frame_count, fps_actual, latest_frame, recording_path
  - CameraService.is_running property
duration: 15m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T02: Build CameraService with capture and JPEG encoder threads

**Ported old CameraModule patterns into clean config-driven CameraService with daemon capture thread, JPEG encoder pool, and CameraResultsStore as the sole integration boundary.**

## What Happened

Created `camera_service.py` with the full capture pipeline:
- Constructor extracts config (device_id, resolution, fps, jpeg_quality, recordings_path), initializes state, no I/O
- `async start()` opens platform-aware VideoCapture (CAP_DSHOW on Windows), logs actual negotiated resolution/FPS, spawns 1 capture daemon + N save daemons (min(4, cpu_count))
- `async stop()` signals stop_event, flushes recording, sends None sentinels, joins all threads with timeout, releases cap
- `_capture_loop()` reads frames continuously, stores raw numpy under frame_lock, JPEG-encodes and pushes bytes to results_store, enqueues for disk save when recording with put_nowait/Full catch
- `_save_worker()` drains queue, writes JPEG files, exits on None sentinel
- `start_recording()/stop_recording()` manage timestamped directories and queue drain
- `get_current_frame()` returns raw numpy for S21 detection workers

Updated `__init__.py` to export both CameraResultsStore and CameraService.

## Verification

All checks passed:
- `from src.services.camera.camera_service import CameraService` — import OK
- `from src.services.camera import CameraResultsStore, CameraService` — exports OK
- Instantiation with invalid device_id=99 — OK, no crash
- `asyncio.run(cs.start())` with device_id=99 — returns False, logs `Camera open failed — device_id=99 not available`
- CameraResultsStore thread-safe store — OK (update, get, snapshot copy isolation)
- `cv2.__version__` = 4.11.0
- `grep opencv-python-headless requirements.txt` — matched
- Fresh store `snapshot()` returns `{}` — OK
- Application startup with `camera.enabled: false` — zero-import guard preserved (lifecycle doesn't import camera modules)

Slice-level verification: **all 8 checks pass**. This is the final task of S20.

## Diagnostics

- `CameraResultsStore.snapshot()` returns `{'latest_frame': bytes, 'frame_count': int, 'is_recording': bool, 'recording_path': str|None, 'fps_actual': float}` when running
- `CameraService.is_running` — True when capture pipeline is active
- Camera open failure logged with device_id for quick diagnosis
- Frame drops logged as warnings — grep for "Frame queue full"
- Recording progress logged every 100 frames

## Deviations

None

## Known Issues

None

## Files Created/Modified

- `src/services/camera/camera_service.py` — New: CameraService class with full capture pipeline
- `src/services/camera/__init__.py` — Updated: exports both CameraResultsStore and CameraService
