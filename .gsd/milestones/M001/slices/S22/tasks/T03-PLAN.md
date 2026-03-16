---
estimated_steps: 6
estimated_files: 1
---

# T03: Wire camera services into lifecycle start/stop

**Slice:** S22 — Lifecycle & DB Integration
**Milestone:** M001

## Description

Camera services (CameraResultsStore, CameraService, DetectionWorker, LDCWorker) exist as standalone classes but aren't part of the application lifecycle. This task wires them into `_init_camera()` for startup and `stop()` for shutdown, following the established patterns from `_init_mqtt()`.

All camera module imports must be lazy (inside the `camera.enabled` config guard) to preserve the zero-import guard — no cv2/torch at lifecycle module level.

## Steps

1. **Add camera attributes to `__init__`** in `ApplicationLifecycle.__init__()` (around line 88, after existing service containers):
   ```python
   # Camera services (optional, config-driven)
   self.camera_results_store = None
   self.camera_service = None
   self.detection_worker = None
   self.ldc_worker = None
   ```
   No type annotations with camera types — that would require importing them at module level.

2. **Expand `_init_camera()`** — After the existing db init code (which creates `self.db_services['camera']`), add camera service creation. All imports inside the method, inside the `if not camera_config.get('enabled', False)` guard:
   ```python
   # Lazy imports — camera modules import cv2/torch at runtime
   from src.services.camera.results_store import CameraResultsStore
   from src.services.camera.camera_service import CameraService
   
   camera_db_service = self.db_services.get('camera')
   
   # Results store (in-memory, thread-safe)
   self.camera_results_store = CameraResultsStore()
   
   # Camera capture service
   self.camera_service = CameraService(camera_config, self.camera_results_store)
   await self.camera_service.start()
   logger.info("  Camera capture service started")
   
   # Detection worker (optional)
   det_config = camera_config.get('detection', {})
   if det_config.get('enabled', False):
       from src.services.camera.detection_worker import DetectionWorker
       self.detection_worker = DetectionWorker(
           camera_config, self.camera_results_store,
           self.camera_service, db_service=camera_db_service,
       )
       self.detection_worker.start()  # Thread.start(), not await
       logger.info("  Detection worker started")
   
   # LDC wear worker (optional)
   wear_config = camera_config.get('wear', {})
   if wear_config.get('enabled', False):
       from src.services.camera.ldc_worker import LDCWorker
       self.ldc_worker = LDCWorker(
           camera_config, self.camera_results_store,
           self.camera_service, db_service=camera_db_service,
       )
       self.ldc_worker.start()  # Thread.start(), not await
       logger.info("  LDC wear worker started")
   ```

3. **Add camera stop to `stop()`** — Insert between step 0 (GUI thread join) and step 1 (data pipeline stop). This ensures camera threads stop before SQLite flush at step 5:
   ```python
   # 0.5. Stop camera threads (before data pipeline and SQLite flush)
   if self.detection_worker:
       logger.info("Stopping detection worker...")
       self.detection_worker.stop()
       self.detection_worker.join(timeout=timeout)
   if self.ldc_worker:
       logger.info("Stopping LDC worker...")
       self.ldc_worker.stop()
       self.ldc_worker.join(timeout=timeout)
   if self.camera_service:
       logger.info("Stopping camera service...")
       await self.camera_service.stop()
   ```
   Critical ordering: workers stop first (they may queue final DB writes), then camera service stops (no more frames), then later SQLite flush drains the queue.

4. **Verify CameraService has async stop**: Check that CameraService has `async def stop()` or `def stop()`. If it's synchronous, call `self.camera_service.stop()` without `await`. (From S20 code: CameraService.start() is `async def start()` but stop may be sync — check and adjust.)

5. **Verify no module-level camera imports**: Confirm lifecycle.py has no new imports of camera modules at the top of the file. All camera imports must be inside `_init_camera()`.

6. **Syntax check**: `python -m py_compile src/core/lifecycle.py`

## Must-Haves

- [ ] Camera attributes (camera_results_store, camera_service, detection_worker, ldc_worker) initialized to None in __init__
- [ ] `_init_camera()` creates and starts all camera objects with lazy imports
- [ ] DetectionWorker only instantiated when `detection.enabled=true`
- [ ] LDCWorker only instantiated when `wear.enabled=true`
- [ ] Workers receive `db_service=self.db_services.get('camera')` 
- [ ] `stop()` stops camera threads before SQLite flush (step 5)
- [ ] No module-level camera imports in lifecycle.py

## Verification

- `python -m py_compile src/core/lifecycle.py` — syntax OK
- Grep for `CameraResultsStore\|CameraService\|DetectionWorker\|LDCWorker` in _init_camera — all four present
- Grep for `detection_worker.stop\|ldc_worker.stop\|camera_service.stop` in stop() — all present
- Verify camera stop appears before `for db_name, db_service in self.db_services` (SQLite flush) in stop()
- Verify no `from src.services.camera` imports at module level in lifecycle.py (only inside _init_camera)

## Observability Impact

- Signals added/changed: logger.info on each camera service start/stop in lifecycle; existing worker-level debug logs continue
- How a future agent inspects this: grep lifecycle logs for "Camera capture service started", "Detection worker started", "LDC wear worker started"; check `self.camera_results_store` is not None after startup
- Failure state exposed: camera init wrapped in try/except with logger.warning — lifecycle continues without camera if init fails

## Inputs

- `src/core/lifecycle.py` — current lifecycle with `_init_camera()` creating only camera.db, no camera service objects
- T02 output: DetectionWorker and LDCWorker now accept `db_service=None` parameter
- S20: CameraService class with `async def start()` and `stop()` methods
- S20: CameraResultsStore class (no deps, thread-safe)

## Expected Output

- `src/core/lifecycle.py` — lifecycle creates, starts, and stops camera services in correct order with lazy imports; camera threads stop before SQLite flush
