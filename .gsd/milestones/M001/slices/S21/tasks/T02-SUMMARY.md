---
id: T02
parent: S21
milestone: M001
provides:
  - DetectionWorker daemon thread with dual RT-DETR inference (broken+crack) publishing to CameraResultsStore
key_files:
  - src/services/camera/detection_worker.py
key_decisions:
  - cv2 imported inside _save_annotated_frame() to keep module-level imports lightweight
  - Annotated frames saved with microsecond timestamps to avoid collisions at high detection rates
patterns_established:
  - Heavy ML imports (torch, ultralytics, cv2) inside run() or helper methods only — never at module level
  - TYPE_CHECKING guard for CameraService and CameraResultsStore references
  - _stop_event checked between model loads and used as sleep in main loop
observability_surfaces:
  - logger.info on model load success (path + device) and failure (path + exception)
  - logger.debug each detection cycle (broken_count, tooth_count, crack_count)
  - model_load_failed property for external health checks
  - CameraResultsStore keys: broken_count, broken_confidence, tooth_count, crack_count, crack_confidence, last_detection_ts
duration: 15m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T02: Build DetectionWorker for RT-DETR broken and crack detection

**Dual RT-DETR detection worker thread with lazy model loading and result publishing to CameraResultsStore**

## What Happened

Built `DetectionWorker(threading.Thread)` following the reference implementations from the old project's `broken_detect.py` and `crack_detect.py`. Key differences from old code: models load inside `run()` instead of at module level, results go to the thread-safe `CameraResultsStore` instead of JSON files, and both models run sequentially on the same frame in one thread instead of using separate global-state modules.

Constructor extracts detection config (interval, confidence, model paths) and stores references to results_store and camera_service. No I/O in constructor. `run()` imports torch/ultralytics, loads both RTDETR models with try/except (sets `_model_load_failed` on failure), then enters the detection loop. Each cycle: get frame → copy → broken inference → parse classes (0=tooth, 1=broken) → crack inference → parse classes (0=crack) → optionally save annotated frame → publish batch to store → wait interval.

Annotated frame saving is best-effort — only writes when recording is active, silently skips on errors.

## Verification

Task-level:
- `python3 -c "from src.services.camera.detection_worker import DetectionWorker; print('import OK')"` — ✅ passed
- `python3 -c "...DetectionWorker(...); assert w.daemon; assert w.name=='detection-worker'; assert not w.model_load_failed; print('instantiation OK')"` — ✅ passed
- `python3 -c "from src.services.camera import CameraResultsStore; print('zero-import preserved')"` — ✅ passed

Slice-level (T02-relevant subset):
- `health_calculator OK` — ✅
- `detection_worker OK` — ✅
- `zero-import OK` — ✅
- `detection instantiation OK` — ✅
- `requirements OK` — ✅
- `config OK` — ✅

Not yet passing (expected — T03 not started):
- `ldc_worker OK` — ❌ (module doesn't exist yet)
- `ldc instantiation OK` — ❌ (module doesn't exist yet)
- `status/color OK` — ❌ (pre-existing T01 threshold mismatch: 55.0 → 'Orta' not 'İyi')

## Diagnostics

- Import check: `python3 -c "from src.services.camera.detection_worker import DetectionWorker; print('OK')"`
- Instantiation: `DetectionWorker({'detection': {...}}, store, camera_service)` — no models or camera needed
- Runtime: `CameraResultsStore.snapshot()` → check `broken_count`, `crack_count`, `last_detection_ts`
- Failure: `worker.model_load_failed` → True if model files missing; error logged with path

## Deviations

- Added `_save_annotated_frame()` helper method that imports cv2 inside itself rather than at module level — plan said "save annotated frame" but didn't specify import strategy. Kept consistent with the lazy-import pattern.

## Known Issues

- Slice verification `h.get_health_status(55.0)=='İyi'` fails — returns 'Orta'. This is a T01 issue (threshold definition vs test expectation mismatch), not caused by T02.

## Files Created/Modified

- `src/services/camera/detection_worker.py` — New: DetectionWorker daemon thread with dual RT-DETR inference pipeline
- `.gsd/milestones/M001/slices/S21/S21-PLAN.md` — Marked T02 as complete
