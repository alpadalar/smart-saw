---
id: T03
parent: S22
milestone: M001
provides:
  - Camera services (CameraResultsStore, CameraService, DetectionWorker, LDCWorker) wired into application lifecycle start/stop
key_files:
  - src/core/lifecycle.py
key_decisions:
  - Camera stop order: workers first (.stop + .join), then CameraService (await .stop), then later SQLite flush drains queued writes
patterns_established:
  - Lazy camera imports inside _init_camera config guard — no cv2/torch at lifecycle module level
  - Camera attributes initialized to None in __init__ with no type annotations (avoids module-level camera imports)
observability_surfaces:
  - logger.info on each camera service start ("Camera capture service started", "Detection worker started", "LDC wear worker started")
  - logger.info on each camera service stop in shutdown sequence
  - logger.warning("Camera initialization failed: ...") if _init_camera fails — lifecycle continues without camera
duration: 10m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T03: Wire camera services into lifecycle start/stop

**Wired CameraResultsStore, CameraService, DetectionWorker, and LDCWorker into lifecycle `_init_camera()` startup and `stop()` shutdown with lazy imports and correct stop ordering.**

## What Happened

Expanded `_init_camera()` from camera-db-only to full camera service creation:
1. Added four camera attributes (`camera_results_store`, `camera_service`, `detection_worker`, `ldc_worker`) initialized to None in `__init__`.
2. After the existing camera.db init, lazy-imports create CameraResultsStore, CameraService, and conditionally DetectionWorker/LDCWorker. Workers receive `db_service=self.db_services.get('camera')` from T02.
3. Added camera stop block in `stop()` between GUI join (step 0) and data pipeline stop (step 1). Workers stop first (`.stop()` + `.join(timeout)`), then CameraService (`await .stop()`), ensuring queued DB writes drain during later SQLite flush.

All camera module imports stay inside `_init_camera()` — lifecycle.py has zero module-level camera imports.

## Verification

- `python -m py_compile src/core/lifecycle.py` — PASS
- Grep for all four camera classes in `_init_camera` — all present (lines 413, 414, 419, 422, 429, 430, 440, 441)
- Grep for `detection_worker.stop`, `ldc_worker.stop`, `camera_service.stop` in `stop()` — all present (lines 184, 188, 192)
- Camera stop appears before `for db_name, db_service in self.db_services` (SQLite flush) — PASS
- No module-level `from src.services.camera` imports — PASS
- Slice-level checks:
  - `import src.services.camera` — OK (no cv2 triggered)
  - `py_compile` on `__init__.py`, `detection_worker.py`, `ldc_worker.py`, `lifecycle.py` — all PASS
  - `_init_camera()` references all four camera classes — PASS
  - `stop()` stops camera before SQLite flush — PASS

## Diagnostics

- Grep lifecycle logs for "Camera capture service started", "Detection worker started", "LDC wear worker started" to confirm startup
- Grep for "Stopping detection worker...", "Stopping LDC worker...", "Stopping camera service..." to confirm shutdown sequence
- If camera init fails, "Camera initialization failed:" warning appears and lifecycle continues without camera
- `self.camera_results_store is not None` after startup confirms camera services are active

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/core/lifecycle.py` — Added camera attributes to __init__, expanded _init_camera() with lazy imports and service creation, added camera stop block in stop()
