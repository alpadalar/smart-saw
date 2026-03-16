---
id: T03
parent: S21
milestone: M001
provides:
  - LDCWorker daemon thread with LDC inference + contour-based wear calculation + health scoring
key_files:
  - src/services/camera/ldc_worker.py
key_decisions:
  - Heavy ML imports (torch, cv2, numpy) and model imports (LDC, HealthCalculator) inside run() only — matches DetectionWorker pattern
  - LDC inference and wear computation split into static helper methods (_run_ldc_inference, _compute_wear) for testability and readability
  - Wear constants (TOP_LINE_Y, BOTTOM_LINE_Y, ROI bbox) as module-level constants — matches old VisionService values exactly
patterns_established:
  - Static helper methods for inference and computation within worker threads — keeps run() focused on lifecycle
  - torch/np/cv2 passed as arguments to static methods rather than re-importing inside each helper
observability_surfaces:
  - "logger.info on LDC model load success (checkpoint path + device)"
  - "logger.error on checkpoint missing or load failure (with path)"
  - "logger.debug each wear cycle (wear_percentage, health_score)"
  - "CameraResultsStore keys: wear_percentage, health_score, health_status, health_color, last_wear_ts"
  - "LDCWorker.model_load_failed property for external health checks"
duration: 15m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T03: Build LDCWorker for edge detection wear measurement

**LDCWorker daemon thread with LDC edge detection, contour-based wear measurement, and health score recalculation — published to CameraResultsStore**

## What Happened

Built `ldc_worker.py` following the DetectionWorker pattern established in T02. The worker:

1. Loads LDC model (modelB4 architecture) and BIPED checkpoint inside `run()` — no heavy imports at module level
2. Runs per-frame LDC inference: 512x512 resize, BGR mean subtraction, CHW float32, sigmoid → normalize → uint8 → bitwise_not → resize → binarize
3. Computes wear percentage via contour analysis in the ROI band (TOP_LINE_Y=170 to BOTTOM_LINE_Y=236) using the exact algorithm from old VisionService._compute_wear
4. After each cycle, reads current broken/tooth counts from store, recalculates overall health via HealthCalculator, and publishes wear + health results atomically via update_batch()

Split inference and wear computation into `_run_ldc_inference()` and `_compute_wear()` static methods — keeps `run()` focused on lifecycle orchestration while making the heavy logic independently testable.

## Verification

Task-level checks (all passed):
- `python3 -c "from src.services.camera.ldc_worker import LDCWorker; print('import OK')"` ✓
- `python3 -c "...LDCWorker({'wear':{'enabled':True,...}}, store, None); assert w.daemon; assert w.name=='ldc-worker'; assert not w.model_load_failed..."` ✓
- `python3 -c "from src.services.camera import CameraResultsStore; print('zero-import preserved')"` ✓

Slice-level checks (9/10 passed):
- health_calculator OK ✓
- status/color OK — **PARTIAL**: `get_health_status(85.0)=='Sağlıklı'` ✓, `get_health_color(15.0)=='#FF0000'` ✓, but `get_health_status(55.0)=='İyi'` fails (returns 'Orta' — 55 is in 40-60 range). Pre-existing T01 boundary issue.
- modelB4 OK ✓
- detection_worker OK ✓
- ldc_worker OK ✓
- zero-import OK ✓
- detection instantiation OK ✓
- ldc instantiation OK ✓
- requirements OK ✓
- config OK ✓

## Diagnostics

- `CameraResultsStore.snapshot()` → check `wear_percentage`, `health_score`, `health_status`, `health_color`, `last_wear_ts`
- `LDCWorker.model_load_failed` → True if checkpoint file missing; error logged with path
- Runtime: worker logs at DEBUG level for each wear cycle — enable with `logging.basicConfig(level=logging.DEBUG)`

## Deviations

- Split inference and wear computation into static helper methods rather than inline in `run()` — cleaner separation, same logic.
- Passed torch/np/cv2 as arguments to static methods instead of re-importing inside each helper — avoids redundant imports while keeping methods static.

## Known Issues

- Pre-existing: slice verification check `get_health_status(55.0)=='İyi'` fails — 55.0 falls in the "Orta" (40-60) range per HealthCalculator thresholds. The slice plan test has a wrong expected value. Not introduced by this task.

## Files Created/Modified

- `src/services/camera/ldc_worker.py` — New: LDCWorker thread with LDC inference + wear calculation + health scoring
- `.gsd/milestones/M001/slices/S21/S21-PLAN.md` — Marked T03 as done
