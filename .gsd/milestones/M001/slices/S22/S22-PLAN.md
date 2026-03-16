# S22: Lifecycle & DB Integration

**Goal:** Camera services (CameraService, DetectionWorker, LDCWorker) start/stop as part of the application lifecycle, and detection/wear results are written to camera.db via SQLiteService queue.

**Demo:** With `camera.enabled=true`, lifecycle starts camera threads and workers. DetectionWorker inserts broken_tooth/crack events into `detection_events` table when detections occur. LDCWorker inserts wear measurements into `wear_history` table each cycle. On shutdown, camera threads stop before SQLite flush so all queued writes complete.

## Must-Haves

- `__init__.py` does not trigger cv2 import — zero-import guard preserved
- DetectionWorker accepts optional `db_service` and writes to `detection_events` when broken_count > 0 or crack_count > 0
- LDCWorker accepts optional `db_service` and writes to `wear_history` each wear cycle
- INSERT SQL column lists match `SCHEMA_CAMERA_DB` table definitions exactly
- `_init_camera()` instantiates CameraResultsStore, CameraService, DetectionWorker, LDCWorker with camera db_service
- Camera threads start during lifecycle startup and stop during shutdown
- Camera threads stop before SQLite flush (step 5) in shutdown sequence
- All camera imports remain lazy (inside config guard) — no cv2/torch at module level in lifecycle

## Proof Level

- This slice proves: integration
- Real runtime required: no (contract-level — no camera hardware or model files in dev)
- Human/UAT required: no

## Verification

- `python -c "import src.services.camera; print('OK')"` — no cv2 import triggered
- `python -c "from src.services.camera.detection_worker import DetectionWorker; print('OK')"` — import succeeds
- `python -c "from src.services.camera.ldc_worker import LDCWorker; print('OK')"` — import succeeds
- `python -m py_compile src/services/camera/__init__.py` — syntax OK
- `python -m py_compile src/services/camera/detection_worker.py` — syntax OK
- `python -m py_compile src/services/camera/ldc_worker.py` — syntax OK
- `python -m py_compile src/core/lifecycle.py` — syntax OK
- Verify DetectionWorker constructor accepts `db_service=None` kwarg
- Verify LDCWorker constructor accepts `db_service=None` kwarg
- Verify `_init_camera()` references CameraResultsStore, CameraService, DetectionWorker, LDCWorker
- Verify `stop()` stops camera threads before SQLite flush (step 5)
- Verify INSERT SQL in detection_worker matches detection_events schema columns
- Verify INSERT SQL in ldc_worker matches wear_history schema columns
- Verify logger.warning emitted when db_service.write_async returns False (failure path visible in logs)

## Observability / Diagnostics

- Runtime signals: logger.info on camera service start/stop in lifecycle; logger.debug on each DB write in workers; logger.warning on db_service write failure
- Inspection surfaces: `detection_events` and `wear_history` tables in camera.db; `CameraResultsStore.snapshot()` for live state
- Failure visibility: `model_load_failed` property on each worker; logger.warning if db_service.write_async returns False (queue full)
- Redaction constraints: none

## Integration Closure

- Upstream surfaces consumed: `CameraResultsStore` (S20), `CameraService` (S20), `DetectionWorker` (S21), `LDCWorker` (S21), `SCHEMA_CAMERA_DB` (S19), `SQLiteService.write_async()` (existing)
- New wiring introduced in this slice: lifecycle `_init_camera()` creates and starts all camera objects; `stop()` tears them down; workers write to camera.db via db_service
- What remains before the milestone is truly usable end-to-end: S23 (IoT telemetry integration), S24 (Camera GUI page)

## Tasks

- [x] **T01: Fix __init__.py zero-import guard** `est:15m`
  - Why: `__init__.py` unconditionally imports CameraService which imports cv2. This breaks the zero-import guard when `camera.enabled=false`. Must fix before lifecycle wiring since lifecycle imports from submodules directly.
  - Files: `src/services/camera/__init__.py`
  - Do: Remove the unconditional `from src.services.camera.camera_service import CameraService` import. Keep docstring and `__all__` but make it empty or remove it. The package should be importable without triggering cv2/torch. Lifecycle already imports from submodules directly (`from src.services.camera.results_store import CameraResultsStore` etc.).
  - Verify: `python -c "import src.services.camera; print('OK')"` succeeds without cv2; `python -m py_compile src/services/camera/__init__.py` passes
  - Done when: `import src.services.camera` does not trigger cv2 import

- [x] **T02: Add db_service to workers with DB writes** `est:25m`
  - Why: DetectionWorker and LDCWorker need to persist results to camera.db. Adding optional `db_service` parameter and INSERT calls after each detection/wear cycle.
  - Files: `src/services/camera/detection_worker.py`, `src/services/camera/ldc_worker.py`
  - Do: (1) Add optional `db_service=None` parameter to both constructors, store as `self._db_service`. (2) In DetectionWorker's main loop, after publishing to results_store, if `self._db_service` and `broken_count > 0`: call `self._db_service.write_async(INSERT INTO detection_events (...) VALUES (...), params)` with event_type='broken_tooth'. Same for `crack_count > 0` with event_type='crack'. (3) In LDCWorker's main loop, after publishing to results_store, if `self._db_service` and `wear_percentage is not None`: call `self._db_service.write_async(INSERT INTO wear_history (...) VALUES (...), params)`. (4) INSERT column lists must match `detection_events` and `wear_history` schemas exactly. Traceability columns (kesim_id, makine_id, serit_id, malzeme_cinsi) can be NULL for now. (5) Log warning if write_async returns False.
  - Verify: `python -m py_compile src/services/camera/detection_worker.py && python -m py_compile src/services/camera/ldc_worker.py`; verify constructors accept `db_service=None`; verify INSERT SQL column lists match schema
  - Done when: Both workers accept `db_service` kwarg and write detection/wear results to camera.db when db_service is provided

- [ ] **T03: Wire camera services into lifecycle start/stop** `est:25m`
  - Why: Camera services exist as standalone classes but aren't started or stopped by the application. This task wires them into `_init_camera()` and `stop()`.
  - Files: `src/core/lifecycle.py`
  - Do: (1) Add camera service attributes to `__init__`: `self.camera_results_store`, `self.camera_service`, `self.detection_worker`, `self.ldc_worker` — all `Optional`, default None. (2) Expand `_init_camera()`: after existing db init code, lazy-import CameraResultsStore, CameraService, DetectionWorker, LDCWorker inside the config guard. Instantiate CameraResultsStore(). Instantiate CameraService(camera_config, results_store) and call `await camera_service.start()`. Instantiate DetectionWorker(camera_config, results_store, camera_service, db_service=self.db_services.get('camera')) — only if `detection.enabled`. Call `detection_worker.start()` (thread start, not await). Same pattern for LDCWorker with `wear.enabled` check. Store all on self. (3) Add camera stop in `stop()` between step 0 (GUI join) and step 1 (data pipeline stop): stop detection_worker and ldc_worker (`.stop()` then `.join(timeout)`), then stop camera_service (`await .stop()`). Camera threads must stop before step 5 (SQLite flush). (4) All imports inside the guard — no cv2/torch at module level.
  - Verify: `python -m py_compile src/core/lifecycle.py`; verify `_init_camera()` creates all four camera objects; verify `stop()` stops camera before SQLite flush
  - Done when: Lifecycle creates, starts, and stops camera services in correct order with lazy imports

## Files Likely Touched

- `src/services/camera/__init__.py`
- `src/services/camera/detection_worker.py`
- `src/services/camera/ldc_worker.py`
- `src/core/lifecycle.py`
