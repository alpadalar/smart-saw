---
id: S22
parent: M001
milestone: M001
provides:
  - Camera services (CameraResultsStore, CameraService, DetectionWorker, LDCWorker) start/stop as part of application lifecycle
  - Detection events (broken_tooth, crack) written to camera.db detection_events table
  - Wear measurements written to camera.db wear_history table
  - Zero-import guard preserved — camera package importable without cv2/torch
requires:
  - slice: S19
    provides: SCHEMA_CAMERA_DB with detection_events and wear_history table definitions
  - slice: S20
    provides: CameraResultsStore and CameraService classes
  - slice: S21
    provides: DetectionWorker and LDCWorker classes with model inference
affects:
  - S23
  - S24
key_files:
  - src/services/camera/__init__.py
  - src/services/camera/detection_worker.py
  - src/services/camera/ldc_worker.py
  - src/core/lifecycle.py
key_decisions:
  - Camera shutdown order: workers.stop() → workers.join() → camera_service.stop() → (later) SQLite flush drains queued writes
  - Workers accept optional db_service=None for backward compatibility — no DB writes when None
  - __init__.py stripped of all re-exports to preserve zero-import guard — lifecycle imports from submodules directly
  - Log warning and drop event (no retry) on write_async failure — keeps detection loop latency stable
patterns_established:
  - Camera submodule imports always direct (from src.services.camera.X import Y), never via package-level re-export
  - Optional db_service kwarg pattern for camera workers — backward compatible, writes only when provided
  - Lazy camera imports inside lifecycle _init_camera config guard — no cv2/torch at module level
  - Traceability columns (kesim_id, makine_id, serit_id, malzeme_cinsi) NULL placeholders for S23/S24
observability_surfaces:
  - logger.info on camera service start ("Camera capture service started", "Detection worker started", "LDC wear worker started")
  - logger.info on camera service stop in shutdown sequence
  - logger.warning("Camera initialization failed: ...") if _init_camera fails — lifecycle continues without camera
  - logger.warning("DB write failed — broken_tooth/crack/wear_history event dropped") on write_async failure
  - detection_events and wear_history tables in camera.db
  - CameraResultsStore.snapshot() for live state
drill_down_paths:
  - .gsd/milestones/M001/slices/S22/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S22/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S22/tasks/T03-SUMMARY.md
duration: 25m
verification_result: passed
completed_at: 2026-03-16
---

# S22: Lifecycle & DB Integration

**Camera services wired into application lifecycle start/stop, detection and wear results persisted to camera.db via SQLiteService queue.**

## What Happened

Three tasks assembled the integration layer between camera services (built in S19–S21) and the running application:

1. **Zero-import guard fix (T01):** The camera `__init__.py` had an unconditional `from .camera_service import CameraService` that pulled in cv2 at import time. Stripped all re-exports — the package is now inert on import. Lifecycle and consumers import directly from submodules.

2. **DB persistence in workers (T02):** Added optional `db_service=None` parameter to DetectionWorker and LDCWorker constructors. When provided, DetectionWorker writes broken_tooth and crack events to `detection_events` after each inference cycle (only when count > 0). LDCWorker writes wear measurements to `wear_history` each cycle. INSERT column lists match SCHEMA_CAMERA_DB exactly (9 non-auto columns each). Write failures log a warning and drop the event — no retry, no loop stall.

3. **Lifecycle wiring (T03):** Expanded `_init_camera()` from camera-db-only init to full service creation: CameraResultsStore → CameraService → DetectionWorker (if detection.enabled) → LDCWorker (if wear.enabled). All imports lazy inside the config guard. Workers receive `db_service=self.db_services.get('camera')`. Shutdown stops workers first (.stop + .join), then CameraService, all before SQLite flush at step 5 — ensuring queued DB writes drain.

## Verification

- `import src.services.camera` — no cv2 triggered ✅
- `from ...detection_worker import DetectionWorker` — import OK ✅
- `from ...ldc_worker import LDCWorker` — import OK ✅
- `py_compile` on `__init__.py`, `detection_worker.py`, `ldc_worker.py`, `lifecycle.py` — all pass ✅
- DetectionWorker accepts `db_service=None` kwarg ✅
- LDCWorker accepts `db_service=None` kwarg ✅
- `_init_camera()` references CameraResultsStore, CameraService, DetectionWorker, LDCWorker ✅
- `stop()` stops camera at step 0.5, before SQLite flush at step 5 ✅
- INSERT SQL column lists match detection_events schema (9 columns, 9 placeholders) ✅
- INSERT SQL column lists match wear_history schema (9 columns, 9 placeholders) ✅
- `logger.warning` on write_async failure in both workers ✅
- No module-level camera imports in lifecycle.py ✅

## Requirements Advanced

- CAM-02 — zero-import guard now proven through lifecycle integration (import src.services.camera inert, all camera imports lazy inside config guard)
- CAM-03 — CameraService now starts via lifecycle when camera.enabled=true
- DATA-01 — detection/wear results now written to camera.db via SQLiteService queue
- DATA-03 — camera.db schema created in lifecycle via existing SQLiteService init, services wired to use it

## Requirements Validated

- none (requires real hardware/models for full validation)

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

None. All three tasks executed as planned.

## Known Limitations

- Traceability columns (kesim_id, makine_id, serit_id, malzeme_cinsi) are NULL in all DB writes — population deferred to S23/S24 when IoT and GUI provide context
- No retry on write_async failure — events are dropped to maintain detection loop latency
- Contract-level proof only — no real camera hardware or model files available in dev environment

## Follow-ups

- S23 should populate traceability columns when IoT integration provides kesim context
- S24 GUI may want to query detection_events and wear_history for display — tables are ready

## Files Created/Modified

- `src/services/camera/__init__.py` — removed unconditional cv2-triggering imports, kept docstring with direct import examples
- `src/services/camera/detection_worker.py` — added db_service parameter, INSERT INTO detection_events for broken_tooth/crack events, warning on write failure
- `src/services/camera/ldc_worker.py` — added db_service parameter, INSERT INTO wear_history for wear measurements, warning on write failure
- `src/core/lifecycle.py` — added camera attributes to __init__, expanded _init_camera() with lazy imports and full service creation, added camera stop block at step 0.5 in stop()

## Forward Intelligence

### What the next slice should know
- Camera services are fully wired but traceability columns are NULL — S23 IoT integration should add kesim_id/makine_id/serit_id/malzeme_cinsi to the camera results pipeline or pass them through to workers
- `CameraResultsStore.snapshot()` returns all detection/wear state as a dict — this is the primary surface for both IoT telemetry (S23) and GUI display (S24)
- Camera services only start when `camera.enabled=true` in config — S23/S24 should guard their camera-dependent code the same way

### What's fragile
- INSERT column lists are hardcoded strings matching SCHEMA_CAMERA_DB — if schema changes, both workers need updating
- `_init_camera()` catches all exceptions and logs warning — camera failure is silent unless you grep logs for "Camera initialization failed"

### Authoritative diagnostics
- Grep lifecycle logs for "Camera capture service started" / "Detection worker started" / "LDC wear worker started" to confirm startup
- Grep for "DB write failed" to detect write-queue saturation
- `SELECT count(*) FROM detection_events` and `SELECT count(*) FROM wear_history` in camera.db confirm writes are landing

### What assumptions changed
- No assumptions changed — all upstream surfaces (S19 schema, S20 capture, S21 workers) matched expectations exactly
