---
estimated_steps: 5
estimated_files: 2
---

# T02: Build CameraService with capture and JPEG encoder threads

**Slice:** S20 — Camera Capture
**Milestone:** M001

## Description

Port the capture loop and JPEG encoder worker pool from the old `CameraModule` (`/media/workspace/eskiimas/smart-saw/src/core/camera.py`, 425 lines) into a clean, config-driven `CameraService`. The old code uses scattered `data_lock` + `current_frame` state — this implementation uses `CameraResultsStore` (from T01) as the single integration boundary. The service has `async start()/stop()` to match existing service patterns but internally spawns/joins OS threads for capture and encoding.

**Key reference patterns from old CameraModule:**
- `_initialize_camera()`: `cv2.VideoCapture(device_id)` with `cv2.CAP_DSHOW` on Windows, sets resolution/FPS/buffer_size=1
- `_start_capture_thread()`: daemon thread, `cap.read()` loop, stores frame, puts `(count, frame.copy(), output_dir)` into `frame_queue` via `put_nowait()`, catches Full
- `_save_frames()`: worker thread, gets from queue, `cv2.imwrite()` with JPEG quality
- `close()`: sets stop_event, sends None sentinels to encoder threads, joins with timeout, releases cap

## Steps

1. **Create `src/services/camera/camera_service.py`.** Use `from __future__ import annotations` to defer type evaluation. Import `cv2` inside the file (this is within `src/services/camera/` — import guard only applies outside this package). Class `CameraService`:

   **Constructor** `__init__(self, config: dict, results_store: CameraResultsStore)`:
   - Store `self._config = config`, `self._results_store = results_store`
   - Extract config values: `device_id`, `resolution` (width/height), `fps`, `jpeg_quality`, `recordings_path`
   - `self._cap: cv2.VideoCapture | None = None`
   - `self._stop_event = threading.Event()`
   - `self._frame_queue: queue.Queue = queue.Queue(maxsize=100)`
   - `self._capture_thread: threading.Thread | None = None`
   - `self._save_threads: list[threading.Thread] = []`
   - `self._current_frame: np.ndarray | None = None` (raw numpy, protected by `self._frame_lock = threading.Lock()`)
   - `self._is_running = False`
   - `self._is_recording = False`
   - `self._frame_count = 0`
   - `self._recording_dir: str | None = None`
   - `self._num_save_threads = min(4, os.cpu_count() or 2)`

   **`async start(self) -> bool`**:
   - Return False if already running
   - Open camera: platform-aware (`cv2.CAP_DSHOW` on `sys.platform.startswith('win')`, default otherwise)
   - Set resolution, FPS, buffer_size=1
   - If `not cap.isOpened()`: log error with device_id, return False
   - Log actual resolution/FPS from cap properties
   - Spawn capture daemon thread (`self._capture_loop`)
   - Spawn N save daemon threads (`self._save_worker`)
   - Set `self._is_running = True`
   - Update results_store: `update_batch({'is_recording': False, 'frame_count': 0, 'fps_actual': 0.0})`
   - Return True

   **`async stop(self) -> None`**:
   - If not running, return
   - Set `self._stop_event`
   - If recording, call `stop_recording()`
   - Send None sentinels to queue (one per save thread)
   - Join save threads with timeout=2.0
   - Join capture thread with timeout=2.0
   - Release VideoCapture
   - Set `self._is_running = False`
   - Log "Camera service stopped"

   **`_capture_loop(self)`** (runs in daemon thread):
   - While not `_stop_event.is_set()`:
     - `ret, frame = self._cap.read()`
     - If not ret: `time.sleep(0.01)`, continue
     - Under `_frame_lock`: `self._current_frame = frame`
     - JPEG encode: `ok, jpeg_buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality])`
     - If ok: `self._results_store.update('latest_frame', jpeg_buf.tobytes())`
     - If `self._is_recording` and `self._recording_dir`:
       - `self._frame_count += 1`
       - Try `self._frame_queue.put_nowait((self._frame_count, frame.copy(), self._recording_dir))`
       - Catch `queue.Full`: `logger.warning("Frame queue full, dropping frame")`
       - `self._results_store.update('frame_count', self._frame_count)`
       - If `self._frame_count % 100 == 0`: log progress

   **`_save_worker(self)`** (runs in daemon thread):
   - While True:
     - `item = self._frame_queue.get()`
     - If item is None: `self._frame_queue.task_done()`, break
     - Unpack `(count, frame, output_dir)`
     - `path = os.path.join(output_dir, f"frame_{count:06d}.jpg")`
     - `cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality])`
     - `self._frame_queue.task_done()`
     - Wrap in try/except, log errors

   **`start_recording(self) -> bool`**:
   - If not running or already recording: return False
   - Create timestamped dir: `os.path.join(self._recordings_path, datetime.now().strftime("%Y%m%d-%H%M%S"))`
   - `os.makedirs(dir, exist_ok=True)`
   - Set `self._is_recording = True`, `self._frame_count = 0`, `self._recording_dir = dir`
   - `self._results_store.update_batch({'is_recording': True, 'frame_count': 0, 'recording_path': dir})`
   - Log "Recording started"
   - Return True

   **`stop_recording(self) -> bool`**:
   - If not recording: return False
   - Set `self._is_recording = False`
   - `self._frame_queue.join()` (wait for remaining frames to flush)
   - `self._results_store.update_batch({'is_recording': False, 'recording_path': None})`
   - Log "Recording stopped"
   - Return True

   **`get_current_frame(self) -> np.ndarray | None`**:
   - Under `_frame_lock`: return `self._current_frame` (for S21 detection workers to read)

   **Property `is_running -> bool`**: return `self._is_running`

2. **Update `src/services/camera/__init__.py`** to export both classes:
   ```python
   from src.services.camera.results_store import CameraResultsStore
   from src.services.camera.camera_service import CameraService

   __all__ = ['CameraResultsStore', 'CameraService']
   ```

3. **Verify imports.** Run: `python -c "from src.services.camera.camera_service import CameraService; print('import OK')"`

4. **Verify instantiation without camera.** Run: `python -c "from src.services.camera.camera_service import CameraService; from src.services.camera.results_store import CameraResultsStore; s = CameraResultsStore(); cs = CameraService({'device_id': 99, 'resolution': {'width': 640, 'height': 480}, 'fps': 30, 'jpeg_quality': 85, 'recordings_path': '/tmp/test_rec'}, s); print('instantiation OK')"`

5. **Verify graceful failure.** Run: `python -c "import asyncio; from src.services.camera.camera_service import CameraService; from src.services.camera.results_store import CameraResultsStore; s = CameraResultsStore(); cs = CameraService({'device_id': 99, 'resolution': {'width': 640, 'height': 480}, 'fps': 30, 'jpeg_quality': 85, 'recordings_path': '/tmp/test_rec'}, s); result = asyncio.run(cs.start()); print(f'start returned: {result}'); assert result == False; print('graceful failure OK')"` — must not crash, must return False, must log error.

## Must-Haves

- [ ] CameraService class with `async start()`, `async stop()`, `start_recording()`, `stop_recording()`, `get_current_frame()`, `is_running`
- [ ] Capture thread is daemon, reads frames in tight loop, stores JPEG bytes in results_store
- [ ] Save workers are daemon threads, consume from queue, write JPEG to disk
- [ ] `put_nowait()` with `queue.Full` catch — never stall capture
- [ ] None sentinels for clean worker shutdown
- [ ] Platform-aware VideoCapture backend (DSHOW on Windows)
- [ ] Graceful failure when camera device doesn't exist (log, return False, no crash)
- [ ] `__init__.py` exports both `CameraResultsStore` and `CameraService`
- [ ] `from __future__ import annotations` in camera_service.py

## Observability Impact

- Signals added/changed: logger.info on camera open success (with actual resolution/FPS), recording start/stop, frame milestone (every 100 frames); logger.warning on frame drops; logger.error on camera open failure with device_id
- How a future agent inspects this: `CameraResultsStore.snapshot()` returns `{'latest_frame': ..., 'frame_count': N, 'is_recording': bool, 'recording_path': str, 'fps_actual': float}`; `CameraService.is_running` property
- Failure state exposed: camera open failure logged with device_id; frame drops logged; stop logs final state

## Verification

- `python -c "from src.services.camera.camera_service import CameraService; print('import OK')"` succeeds
- `python -c "from src.services.camera import CameraResultsStore, CameraService; print('exports OK')"` succeeds
- Instantiation with invalid device_id succeeds without crash
- `asyncio.run(cs.start())` returns False when camera not connected, logs error
- Application startup with `camera.enabled: false` still works (camera modules not imported by lifecycle)

## Inputs

- `src/services/camera/results_store.py` — CameraResultsStore from T01 (thread-safe dict with update/get/snapshot)
- `requirements.txt` — opencv-python-headless installed from T01
- Old project reference at `/media/workspace/eskiimas/smart-saw/src/core/camera.py` — 425 lines, direct port source for capture/encode patterns
- Config schema from `config/config.yaml` camera section: device_id, resolution, fps, jpeg_quality, recordings_path

## Expected Output

- `src/services/camera/camera_service.py` — New file: CameraService class with capture thread + JPEG encoder pool
- `src/services/camera/__init__.py` — Updated to export both CameraResultsStore and CameraService
