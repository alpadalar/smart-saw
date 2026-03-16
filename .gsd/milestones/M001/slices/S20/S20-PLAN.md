# S20: Camera Capture

**Goal:** OpenCV capture thread runs in background, JPEG frames written to recordings directory, with CameraResultsStore as the thread-safe integration boundary for all downstream consumers (GUI, IoT, detection).
**Demo:** `CameraService` can be instantiated with config, `start()` opens the camera and begins capturing frames, `start_recording()` writes JPEG frames to `data/recordings/YYYYMMDD-HHMMSS/frame_NNNNNN.jpg`, and `CameraResultsStore` exposes `latest_frame`, `frame_count`, `fps_actual`, `is_recording` to any consumer thread. When no camera is connected, service logs the error and does not crash.

## Must-Haves

- CameraResultsStore is thread-safe (Lock-guarded), with `update()`, `update_batch()`, `get()`, `snapshot()` returning a copy
- CameraService reads all config from dict (device_id, resolution, fps, jpeg_quality, recordings_path)
- Capture runs in a daemon thread, JPEG encoding/saving runs in N daemon worker threads
- Frame pipeline uses `queue.Queue(maxsize=100)` with `put_nowait()` drop-on-full semantics
- `start_recording()` creates timestamped directory, `stop_recording()` drains queue
- `async start()` / `async stop()` interface matches existing service pattern (spawns threads internally)
- `get_current_frame()` returns raw numpy array for detection workers (S21)
- `latest_frame` in store is JPEG bytes (compact, GUI-ready)
- Graceful handling when camera not connected (`cap.isOpened() == False`)
- `opencv-python-headless` added to requirements.txt (not `opencv-python` — Qt conflict)
- No detection logic (S21), no lifecycle wiring (S22), no imports outside `src/services/camera/`
- S19 foundation commits merged into worktree (camera config, DB schema, lifecycle stub, camera scaffold)

## Proof Level

- This slice proves: contract
- Real runtime required: no (no camera in dev — verify import, instantiation, graceful failure)
- Human/UAT required: no

## Verification

- `python -c "from src.services.camera.results_store import CameraResultsStore; s = CameraResultsStore(); s.update('k', 1); assert s.get('k') == 1; d = s.snapshot(); assert d == {'k': 1}; s.update('k', 2); assert d['k'] == 1; print('OK')"` — thread-safe store works, snapshot returns copy
- `python -c "from src.services.camera.camera_service import CameraService; print('import OK')"` — cv2 installed, import succeeds
- `python -c "import cv2; print(cv2.__version__)"` — opencv-python-headless installed
- `grep 'opencv-python-headless' requirements.txt` — dependency declared
- `python -c "from src.services.camera import CameraResultsStore, CameraService; print('exports OK')"` — `__init__.py` exports both
- `python -c "from src.services.camera.camera_service import CameraService; from src.services.camera.results_store import CameraResultsStore; s = CameraResultsStore(); cs = CameraService({'device_id': 99, 'resolution': {'width': 640, 'height': 480}, 'fps': 30, 'jpeg_quality': 85, 'recordings_path': '/tmp/test_rec'}, s); print('instantiation OK')"` — CameraService instantiates without opening camera
- Application startup with `camera.enabled: false` still works (zero-import guard preserved)

## Observability / Diagnostics

- Runtime signals: logger.info on camera init success/failure, recording start/stop, frame count milestones (every 100 frames); logger.warning on frame drop (queue full); logger.error on camera open failure
- Inspection surfaces: `CameraResultsStore.snapshot()` returns current state dict; `CameraService.is_running` property
- Failure visibility: camera open failure logged with device_id; frame drops logged with queue size context
- Redaction constraints: none

## Integration Closure

- Upstream surfaces consumed: S19's `config/config.yaml` camera section, `src/services/camera/__init__.py` scaffold, `_init_camera()` in lifecycle.py, `SCHEMA_CAMERA_DB` in schemas.py, numpy uncap in requirements.txt
- New wiring introduced in this slice: none (modules exist but are not imported by lifecycle — that's S22)
- What remains before the milestone is truly usable end-to-end: S21 (detection pipeline), S22 (lifecycle wiring + DB writes), S23 (IoT integration), S24 (GUI)

## Tasks

- [ ] **T01: Merge S19 foundation and build CameraResultsStore** `est:45m`
  - Why: S19's two commits (`8dfbdb0`, `2131ac2`) are on a diverged branch — the worktree HEAD lacks camera config, DB schema, lifecycle stub, camera scaffold, and numpy uncap. CameraResultsStore is the sole integration boundary for all camera data consumers and must exist before CameraService.
  - Files: `src/services/camera/results_store.py` (new), `src/services/camera/__init__.py`, `requirements.txt`
  - Do: Cherry-pick S19 commits into worktree branch. Add `opencv-python-headless>=4.11.0` to requirements.txt. Build CameraResultsStore with threading.Lock, internal `_data` dict, `update(key, value)`, `update_batch(dict)`, `get(key, default=None)`, `snapshot() -> dict` (returns copy). Install opencv-python-headless. Verify store works.
  - Verify: `python -c "from src.services.camera.results_store import CameraResultsStore; ..."` passes; `import cv2` works; `grep opencv-python-headless requirements.txt` matches
  - Done when: CameraResultsStore importable and tested, S19 artifacts present in worktree, cv2 importable

- [ ] **T02: Build CameraService with capture and JPEG encoder threads** `est:1h`
  - Why: This is the core capture engine. Ports the old CameraModule pattern into a clean config-driven service with CameraResultsStore as the data boundary.
  - Files: `src/services/camera/camera_service.py` (new), `src/services/camera/__init__.py`
  - Do: Build CameraService class: constructor takes `config: dict` + `results_store: CameraResultsStore`. `async start()` opens VideoCapture, spawns capture daemon thread + N encoder daemon threads. `async stop()` sets stop_event, sends None sentinels, joins threads, releases cap. `start_recording() -> bool` creates timestamped dir. `stop_recording() -> bool` drains queue. `get_current_frame() -> Optional[np.ndarray]`. Capture thread stores JPEG-encoded `latest_frame` bytes in results_store, keeps raw frame for `get_current_frame()`. Queue uses `put_nowait()` with `Full` catch. Platform-aware backend (DSHOW on Windows). Update `__init__.py` to export both classes.
  - Verify: Import succeeds, instantiation works, graceful failure with non-existent camera device
  - Done when: CameraService importable, exports in `__init__.py`, handles missing camera gracefully

## Files Likely Touched

- `src/services/camera/results_store.py` (new)
- `src/services/camera/camera_service.py` (new)
- `src/services/camera/__init__.py` (update exports)
- `requirements.txt` (add opencv-python-headless)
- `config/config.yaml` (from S19 merge)
- `src/core/lifecycle.py` (from S19 merge)
- `src/services/database/schemas.py` (from S19 merge)
