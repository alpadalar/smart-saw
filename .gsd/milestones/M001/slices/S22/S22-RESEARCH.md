# S22: Lifecycle & DB Integration — Research

**Date:** 2026-03-16

## Summary

S22 wires the camera subsystem (CameraService, DetectionWorker, LDCWorker) into the application lifecycle and adds DB writes for detection/wear results. All components already exist as standalone classes from S20/S21 — this slice is pure integration, following established lifecycle and SQLiteService patterns already used for MQTT, Modbus, and other services.

The work breaks into three natural seams: (1) expand `_init_camera()` in lifecycle to instantiate and start camera services + workers, (2) add DB write calls into DetectionWorker and LDCWorker so results flow to camera.db via `SQLiteService.write_async()`, and (3) add camera stop to the shutdown sequence. A minor cleanup: fix the `__init__.py` unconditional cv2 import that would break the zero-import guard if anyone imports the camera package directly.

## Recommendation

Follow the existing lifecycle pattern exactly — `_init_mqtt()` is the template. Expand `_init_camera()` to lazy-import CameraResultsStore, CameraService, DetectionWorker, and LDCWorker; instantiate them with the camera config and camera db_service; call `start()` / `.start()` (thread start). Add a `_stop_camera()` helper in the stop sequence between GUI thread join and data pipeline stop — camera threads must stop before SQLite flush so all queued writes complete. Pass `db_service` (the camera SQLiteService) into workers so they can call `write_async()` directly — no orchestration layer needed.

## Implementation Landscape

### Key Files

- `src/core/lifecycle.py` — **MODIFY**: Expand `_init_camera()` (line 364) to instantiate and start CameraResultsStore, CameraService, DetectionWorker, LDCWorker. Add camera service attributes to `__init__`. Add camera stop step in `stop()` between step 0 (GUI join) and step 1 (data pipeline stop). Camera threads must stop before step 5 (SQLite flush).
- `src/services/camera/detection_worker.py` — **MODIFY**: Accept optional `db_service` parameter. After each detection cycle, call `db_service.write_async()` to insert broken_tooth and crack events into `detection_events` table. Only write when `broken_count > 0` or `crack_count > 0` to avoid flooding the DB with empty events.
- `src/services/camera/ldc_worker.py` — **MODIFY**: Accept optional `db_service` parameter. After each wear measurement, call `db_service.write_async()` to insert into `wear_history` table with wear_percentage and health_score.
- `src/services/camera/__init__.py` — **MODIFY**: Remove unconditional `from src.services.camera.camera_service import CameraService` (triggers `import cv2`). Make imports lazy or remove them — lifecycle imports from submodules directly.
- `src/services/database/schemas.py` — No changes needed. `SCHEMA_CAMERA_DB` already defines `detection_events` and `wear_history` tables with all needed columns.
- `config/config.yaml` — No changes needed. Camera config section already has all needed fields.

### Existing Patterns to Follow

**Lifecycle init pattern** (from `_init_mqtt()` at line 323):
- Check config guard (`if not config.get('enabled', False): return`)
- Lazy import inside the guard
- Instantiate service with config
- Call `await service.start()` or `service.start()` for threads
- Store reference on `self` for shutdown

**Lifecycle stop pattern** (from `stop()` at line 144):
- Check `if self.service: await self.service.stop()`
- Order: GUI → camera threads → data pipeline → IoT → Modbus → PostgreSQL → SQLite flush
- Camera threads must stop before SQLite flush so queued writes complete

**DB write pattern** (from `data_processor.py` and anomaly manager):
- `db_service.write_async(sql, params)` — non-blocking queue insertion
- SQL uses `INSERT INTO table (...) VALUES (?, ?, ...)` with positional params tuple
- Thread-safe — write_async uses `Queue.put_nowait()` internally

### Build Order

1. **Fix `__init__.py` zero-import guard** — Remove unconditional cv2-triggering imports. Quick, no dependencies.
2. **Add `db_service` parameter to DetectionWorker and LDCWorker** — Thread DB writes into existing detection/wear cycles. Independent of lifecycle changes.
3. **Expand `_init_camera()` in lifecycle** — Wire everything together: instantiate store, camera_service, workers with db_service; start threads. Add attributes to `__init__`. Add camera stop to `stop()`.

### Verification Approach

1. **Zero-import guard**: `python -c "from src.services.camera.results_store import CameraResultsStore; print('OK')"` should work without cv2/torch installed. `python -c "import src.services.camera"` should NOT trigger cv2 import (currently does — fix confirms).
2. **Worker DB writes**: Verify DetectionWorker and LDCWorker constructors accept `db_service` parameter. Verify `write_async` calls use correct SQL matching `detection_events` and `wear_history` schemas.
3. **Lifecycle integration**: Verify `_init_camera()` creates all four objects (store, camera_service, detection_worker, ldc_worker) and starts them. Verify `stop()` stops camera threads before SQLite flush. Verify lifecycle attributes exist for camera services.
4. **Schema match**: Confirm INSERT SQL column lists match `SCHEMA_CAMERA_DB` table definitions exactly.
5. **Syntax check**: `python -m py_compile src/core/lifecycle.py && python -m py_compile src/services/camera/detection_worker.py && python -m py_compile src/services/camera/ldc_worker.py`

## Constraints

- Camera imports must remain lazy (inside `_init_camera()` config guard) — no `import cv2` or `import torch` at module level in lifecycle.
- Workers are `threading.Thread` subclasses — `start()` is synchronous (not `await`). Only CameraService has `async def start()`.
- Camera threads must stop before SQLite flush in shutdown sequence — otherwise queued writes are lost.
- `db_service` parameter must be optional (default None) in workers to preserve backward compatibility with existing tests and instantiation patterns.
- `__init__.py` fix must not break any existing imports — lifecycle imports from submodules directly, not from `__init__.py`.

## Common Pitfalls

- **Stopping camera after SQLite flush** — If camera threads stop after `db_service.stop()`, any pending `write_async()` calls will silently fail because the queue is already drained. Stop camera threads first, then flush SQLite.
- **Passing wrong db_service** — Workers must receive `self.db_services['camera']`, not any other db_service. The `detection_events` and `wear_history` tables only exist in camera.db.
- **Thread.start() vs await** — DetectionWorker and LDCWorker use `threading.Thread.start()` (synchronous), not `await start()`. CameraService uses `await start()` because it contains `async def start()`.
- **Forgetting to check detection.enabled / wear.enabled** — Workers already check `self._enabled` in their config, but lifecycle should also check before instantiating to avoid creating threads that immediately exit.
