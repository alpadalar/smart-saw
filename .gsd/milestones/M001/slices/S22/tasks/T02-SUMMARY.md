---
id: T02
parent: S22
milestone: M001
provides:
  - DetectionWorker and LDCWorker accept optional db_service and persist detection/wear events to camera.db
key_files:
  - src/services/camera/detection_worker.py
  - src/services/camera/ldc_worker.py
key_decisions:
  - Log warning and drop event (no retry) when write_async returns False — keeps detection loop latency stable
patterns_established:
  - Optional db_service kwarg pattern for camera workers — backward compatible, writes only when provided
  - Traceability columns (kesim_id, makine_id, serit_id, malzeme_cinsi) are NULL placeholders for S23/S24
observability_surfaces:
  - logger.warning on DB write failure (grep "DB write failed" in logs)
  - detection_events and wear_history tables in camera.db
duration: 10m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T02: Add db_service to workers with DB writes

**Added optional `db_service` parameter to DetectionWorker and LDCWorker; workers now persist broken_tooth/crack events and wear measurements to camera.db when db_service is provided.**

## What Happened

Added `db_service=None` keyword argument to both worker constructors, stored as `self._db_service`. In DetectionWorker's main loop, after `results_store.update_batch()`, broken_tooth and crack events are written to `detection_events` via `write_async` when respective counts > 0. In LDCWorker's main loop, wear measurements are written to `wear_history` when `wear_percentage is not None`. Both workers check `write_async` return value and emit `logger.warning` on failure. All traceability columns are NULL — S23/S24 will populate them.

## Verification

- `python -m py_compile src/services/camera/detection_worker.py` — syntax OK
- `python -m py_compile src/services/camera/ldc_worker.py` — syntax OK
- `python -c "from src.services.camera.detection_worker import DetectionWorker; print('OK')"` — import OK
- `python -c "from src.services.camera.ldc_worker import LDCWorker; print('OK')"` — import OK
- `python -c "import src.services.camera; print('OK')"` — camera package import still inert (T01 guard preserved)
- INSERT column lists match schema: 9 non-auto columns, 9 `?` placeholders in each statement
- `db_service=None` in both constructors — backward compatible, no writes when None
- `logger.warning` on write failure present in both workers

### Slice-level checks status (intermediate — T03 remaining)

| Check | Status |
|-------|--------|
| `import src.services.camera` no cv2 | ✅ pass |
| DetectionWorker import | ✅ pass |
| LDCWorker import | ✅ pass |
| `__init__.py` syntax | ✅ pass |
| `detection_worker.py` syntax | ✅ pass |
| `ldc_worker.py` syntax | ✅ pass |
| `lifecycle.py` syntax | ⏳ T03 |
| DetectionWorker accepts `db_service=None` | ✅ pass |
| LDCWorker accepts `db_service=None` | ✅ pass |
| `_init_camera()` references all camera objects | ⏳ T03 |
| `stop()` stops camera before SQLite flush | ⏳ T03 |
| INSERT SQL matches detection_events schema | ✅ pass |
| INSERT SQL matches wear_history schema | ✅ pass |
| logger.warning on write_async failure | ✅ pass |

## Diagnostics

- Grep logs for `"DB write failed"` to detect write-queue saturation at runtime
- Query `SELECT * FROM detection_events ORDER BY id DESC LIMIT 10` in camera.db to confirm detection writes
- Query `SELECT * FROM wear_history ORDER BY id DESC LIMIT 10` in camera.db to confirm wear writes
- When `db_service` is None, no DB writes occur — confirmed by absence of `self._db_service` attribute usage in flow

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/services/camera/detection_worker.py` — added `db_service=None` param, `self._db_service` storage, INSERT INTO detection_events for broken_tooth/crack events, warning on write failure
- `src/services/camera/ldc_worker.py` — added `db_service=None` param, `self._db_service` storage, INSERT INTO wear_history for wear measurements, warning on write failure
