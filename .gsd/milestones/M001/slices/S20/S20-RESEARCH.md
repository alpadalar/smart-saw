# S20: Camera Capture — Research

**Date:** 2026-03-16

## Summary

S20 builds two new modules: `CameraResultsStore` (thread-safe singleton) and `CameraService` (OpenCV capture + JPEG encoder threads). This is the camera infrastructure layer — all downstream slices (S21 detection, S22 lifecycle, S24 GUI) depend on it. The old project's `CameraModule` in `eskiimas/smart-saw/src/core/camera.py` is the direct reference implementation (425 lines). The port is straightforward: extract capture + encoding into a clean service, add `CameraResultsStore` as the integration boundary, and follow config from S19's `camera:` section in `config.yaml`.

S19 established: numpy cap removed, camera config schema in `config.yaml`, `SCHEMA_CAMERA_DB` in `schemas.py`, `_init_camera()` lifecycle stub, empty `src/services/camera/__init__.py`. S19's code commits (`8dfbdb0`, `2131ac2`) exist but are on a branch not yet merged to the worktree HEAD — the executor will need to either merge them first or build on top of them. The key S19 artifacts: camera config section, DB schema, lifecycle `_init_camera()` method, and the camera module scaffold.

**Important:** `opencv-python-headless` needs to be added to `requirements.txt` in this slice — S19 only removed the numpy cap but did not add camera dependencies.

## Recommendation

Build in two tasks:

1. **CameraResultsStore** — Pure Python, no external deps. Thread-safe dict with `threading.Lock`, `update()`, `update_batch()`, `get()`, `snapshot()` methods. This is the sole integration boundary between camera threads and all consumers (GUI, IoT, DB). Build and unit-test first.

2. **CameraService** — OpenCV capture thread + multi-thread JPEG encoder pool. Port from old `CameraModule` but cleaner: config-driven (no constants module), `threading.Event` for stop signaling, `queue.Queue(maxsize=N)` for frame pipeline, daemon threads. Writes `latest_frame` (JPEG bytes) to `CameraResultsStore`. Creates recording directories as `recordings/YYYYMMDD-HHMMSS/frame_{n:06d}.jpg`.

Do NOT add detection logic (that's S21). Do NOT add lifecycle wiring (that's S22). Do NOT import camera modules in lifecycle (lazy import guard stays as-is from S19).

## Implementation Landscape

### Key Files

- `src/services/camera/__init__.py` — Exists from S19 (empty scaffold). Update exports.
- `src/services/camera/results_store.py` — **NEW**. `CameraResultsStore` class. Thread-safe dict, `threading.Lock`. Keys: `latest_frame` (bytes), `frame_count` (int), `is_recording` (bool), `recording_path` (str|None), `fps_actual` (float). Methods: `update(key, value)`, `update_batch(dict)`, `get(key, default)`, `snapshot() -> dict`.
- `src/services/camera/camera_service.py` — **NEW**. `CameraService` class. Constructor takes `config: dict` and `results_store: CameraResultsStore`. Methods: `async start()`, `async stop()`, `start_recording() -> bool`, `stop_recording() -> bool`, `get_current_frame() -> Optional[np.ndarray]`. Internal: `_capture_thread` (daemon), `_save_threads` (N daemon workers), `_frame_queue` (Queue), `_stop_event` (Event).
- `requirements.txt` — Add `opencv-python-headless>=4.11.0`.
- `config/config.yaml` — Already has camera section from S19. No changes needed.

### Reference Implementation

Old project `eskiimas/smart-saw/src/core/camera.py` (425 lines):
- `_initialize_camera()`: `cv2.VideoCapture(device_id)` with platform-aware backend (DSHOW on Windows), sets resolution/FPS/buffer_size
- `_start_capture_thread()`: daemon thread, `cap.read()` loop, stores `current_frame` under `data_lock`, puts `(count, frame.copy(), output_dir)` tuples into `frame_queue`
- `_save_frames()`: worker thread, gets from queue, `cv2.imwrite()` with JPEG quality param
- `_start_save_threads()`: spawns N save threads (configurable, default 4)
- `start_recording()`: creates timestamped dir, sets `is_recording=True`
- `stop_recording()`: sets `is_recording=False`, waits for queue drain via `frame_queue.join()`
- `close()`: sets stop_event, drains queue with None sentinels, joins threads, releases cap

Key differences from old project:
- Config comes from `config.yaml` dict, not constants module
- `CameraResultsStore` replaces scattered `data_lock` + `current_frame` pattern
- `latest_frame` stored as JPEG bytes (not raw numpy) for efficient GUI display
- No detection logic in CameraService (split to S21)
- `async start()/stop()` interface matches existing service pattern (but spawns threads internally)

### Config Values (from S19)

```yaml
camera:
  enabled: false
  device_id: 0
  resolution: {width: 1280, height: 720}
  fps: 30
  jpeg_quality: 85
  recordings_path: "data/recordings"
```

### Build Order

1. **CameraResultsStore** first — zero external deps, pure threading.Lock + dict. Unit-testable in isolation. Everything else depends on it.
2. **CameraService** second — depends on CameraResultsStore + cv2. Port capture loop and JPEG encoder from old project.
3. **requirements.txt update** — can happen in either task, but logically belongs with CameraService since that's what needs cv2.
4. **`__init__.py` update** — export both classes for downstream slices.

### Verification Approach

- `python -c "from src.services.camera.results_store import CameraResultsStore; s = CameraResultsStore(); s.update('test', 42); assert s.get('test') == 42; print('OK')"` — Store works.
- `python -c "from src.services.camera.camera_service import CameraService"` — Import succeeds (cv2 installed).
- Camera is not connected in dev environment, so hardware-level testing is not possible. Verify: CameraService handles `cap.isOpened() == False` gracefully, logs error, does not crash.
- `python -c "import cv2; print(cv2.__version__)"` — cv2 installed correctly.
- Startup with `camera.enabled: false` must still work with no camera imports (zero-import guard from S19 preserved).
- Thread safety: CameraResultsStore `snapshot()` returns a copy (not a reference to internal dict).

## Constraints

- `opencv-python-headless` only — NOT `opencv-python` (Qt5/Qt6 conflict with PySide6).
- All camera code must be import-guarded — no `import cv2` at module level in any file outside `src/services/camera/`.
- `camera_service.py` must use `from __future__ import annotations` to defer type annotation evaluation.
- CameraService's `async start()/stop()` methods match existing service interface but internally spawn/join threads — no asyncio calls inside capture loop.
- Frame queue maxsize should be bounded (old project uses 100; recommend keeping similar or config-driven).
- JPEG encoder thread count should come from config or default to `min(4, os.cpu_count() or 2)`.

## Common Pitfalls

- **BGR vs RGB at the boundary** — OpenCV captures BGR. Store `latest_frame` as JPEG bytes (BGR → imencode, no conversion needed for disk or display). Detection models (S21) will handle their own conversion when they read frames. Don't convert to RGB in CameraService — let consumers decide.
- **cap.read() blocking** — Must run in dedicated thread, never in asyncio. Old project does this correctly; port the pattern.
- **Queue.put() blocking when full** — Use `put_nowait()` and catch `queue.Full` to drop frames (old project pattern). Recording should never stall capture.
- **Thread cleanup on stop** — Send None sentinels to encoder threads, join with timeout, release VideoCapture. Old project's `close()` method is the template.
- **JPEG bytes in store vs numpy in store** — Store JPEG bytes for `latest_frame` (compact, GUI-ready). Keep raw numpy frame available via `get_current_frame()` method for detection workers (S21) that need numpy arrays.
