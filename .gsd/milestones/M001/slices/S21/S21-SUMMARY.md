---
id: S21
parent: M001
milestone: M001
provides:
  - DetectionWorker daemon thread with dual RT-DETR inference (broken tooth + crack detection)
  - LDCWorker daemon thread with LDC edge detection + contour-based wear percentage calculation
  - HealthCalculator class with 70/30 weighted scoring, Turkish status labels, hex color codes
  - Vendored modelB4.py (LDC network architecture) for edge detection
  - AI/Vision dependencies declared (ultralytics, torch, torchvision)
  - LDC checkpoint path in camera config
requires:
  - slice: S20
    provides: CameraResultsStore (thread-safe key-value store), CameraService.get_current_frame(), camera config section, zero-import guard in __init__.py
  - slice: S19
    provides: camera.db schema in schemas.py, numpy cap removed, camera config section foundation
affects:
  - S22
  - S23
  - S24
key_files:
  - src/services/camera/detection_worker.py
  - src/services/camera/ldc_worker.py
  - src/services/camera/health_calculator.py
  - src/services/camera/modelB4.py
  - requirements.txt
  - config/config.yaml
key_decisions:
  - Both RT-DETR models (broken+crack) consolidated into single DetectionWorker thread — sequential inference on same frame, simpler than two threads with model sharing
  - LDC model vendored as modelB4.py into src/services/camera/ — pure PyTorch ~240 lines, no external deps beyond torch
  - Workers import torch/ultralytics inside run() not at module level — preserves zero-import guard when camera.enabled=false
  - HealthCalculator called from LDCWorker after each wear update — collocated with the slower measurement cycle
  - Heavy ML imports (torch, ultralytics, cv2) deferred to run() or helper methods — never at module level
  - Static helper methods (_run_ldc_inference, _compute_wear) for testability within LDCWorker
  - cv2 imported inside _save_annotated_frame() in DetectionWorker — consistent lazy-import pattern
patterns_established:
  - Worker thread pattern: threading.Thread daemon, constructor takes (config, results_store, camera_service), models load inside run(), _stop_event for graceful shutdown, model_load_failed property for health checks
  - Lazy ML import pattern: torch/ultralytics/cv2 imported inside run() or static helpers, TYPE_CHECKING guard for type hints
  - Results publishing: workers write to CameraResultsStore via update_batch() for atomic multi-key updates
  - Graceful model-missing handling: log error with path, set model_load_failed flag, exit run() without crash
observability_surfaces:
  - "CameraResultsStore.snapshot() — returns dict with broken_count, broken_confidence, tooth_count, crack_count, crack_confidence, wear_percentage, health_score, health_status, health_color, last_detection_ts, last_wear_ts"
  - "DetectionWorker.model_load_failed / LDCWorker.model_load_failed — boolean property for external health checks"
  - "logger.info on model load success (path + device) and failure (path + exception)"
  - "logger.debug on each detection cycle (broken_count, tooth_count, crack_count) and wear cycle (wear_percentage, health_score)"
  - "HealthCalculator logs at DEBUG level on each calculation"
drill_down_paths:
  - .gsd/milestones/M001/slices/S21/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S21/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S21/tasks/T03-SUMMARY.md
duration: 45m
verification_result: passed
completed_at: 2026-03-16
---

# S21: AI Detection Pipeline

**RT-DETR broken/crack detection and LDC wear calculation workers with HealthCalculator, all publishing to CameraResultsStore via lazy-loaded models in dedicated daemon threads**

## What Happened

Built the three core AI inference components of the camera vision system:

**T01** vendored the LDC model definition (`modelB4.py`) from the old project and built `HealthCalculator` — a standalone class (no torch dependency) that computes saw health from broken count and wear percentage using a 70/30 weighted formula. Same thresholds, Turkish status labels, and hex color codes as the reference `SawHealthCalculator`. Added `ultralytics>=8.3.70`, `torch>=2.6.0`, `torchvision>=0.21.0` to requirements.txt and `ldc_checkpoint_path` to camera config.

**T02** built `DetectionWorker(threading.Thread)` — a daemon thread that loads two RT-DETR models (broken tooth `best.pt` + crack `catlak-best.pt`) inside `run()`, reads frames from CameraService, runs sequential inference on the same frame copy, and publishes broken_count, crack_count, confidence scores, and timestamps to CameraResultsStore. Annotated frames are optionally saved when recording is active.

**T03** built `LDCWorker(threading.Thread)` — a daemon thread that loads the LDC model (modelB4 architecture + BIPED checkpoint) inside `run()`, runs edge detection (512×512 resize, BGR mean subtraction, sigmoid → normalize → threshold), computes wear percentage via contour analysis in the ROI band (TOP_LINE_Y=170, BOTTOM_LINE_Y=236), then calls HealthCalculator to derive health_score/status/color. All results published atomically to CameraResultsStore.

Both workers follow the same pattern: constructor takes (config, results_store, camera_service) with no I/O, models load lazily inside `run()` with try/except, `_stop_event` enables graceful shutdown, and `model_load_failed` property allows external health checks. Neither worker is wired into lifecycle yet — they're standalone thread classes ready for S22.

## Verification

All 10 slice-level checks pass:

| Check | Result |
|-------|--------|
| health_calculator OK (score math: 90 < 90.5 < 100) | ✅ |
| status/color OK (Sağlıklı at 85, #FF0000 at 15) | ✅ |
| modelB4 OK (LDC class imports) | ✅ |
| detection_worker OK (import succeeds) | ✅ |
| ldc_worker OK (import succeeds) | ✅ |
| zero-import OK (CameraResultsStore without torch) | ✅ |
| detection instantiation OK (constructor with mock config) | ✅ |
| ldc instantiation OK (constructor with mock config) | ✅ |
| requirements OK (ultralytics + torch in requirements.txt) | ✅ |
| config OK (ldc_checkpoint_path in config.yaml) | ✅ |

Observability verified:
- `CameraResultsStore.snapshot()` returns dict (empty until workers run with real models)
- `DetectionWorker.model_load_failed` returns False before run() (no failure yet)
- `LDCWorker.model_load_failed` returns False before run() (no failure yet)

## Requirements Advanced

- DET-01 — DetectionWorker loads broken tooth RT-DETR model and runs inference; contract proven (import + instantiation), runtime needs real model files
- DET-02 — DetectionWorker loads crack RT-DETR model and runs inference; contract proven, runtime needs model files
- DET-03 — LDCWorker loads LDC model, runs edge detection, computes wear percentage via contour analysis; contract proven
- DET-04 — HealthCalculator computes health score from broken count (70%) + wear percentage (30%); math verified with known inputs
- DET-05 — Both workers publish results to CameraResultsStore via update_batch(); store keys verified
- DET-06 — Both workers load models inside run() in their own daemon threads; import-time safety verified

## Requirements Validated

- none — all DET requirements are contract-proven (import, instantiation, math) but need real model files and camera hardware for full validation

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- Slice plan verification test `get_health_status(55.0)=='İyi'` is incorrect — 55.0 falls in the "Orta" range (40-60) per the reference code's `>=60` threshold for "İyi". The HealthCalculator implementation matches the reference exactly. Adjusted verification to test correct boundaries instead.
- LDCWorker splits inference and wear computation into static helper methods (`_run_ldc_inference`, `_compute_wear`) rather than inlining in `run()` — cleaner separation, same logic.
- DetectionWorker saves annotated frames with microsecond timestamps to avoid collisions — not specified in plan but prevents overwrites at high detection rates.

## Known Limitations

- Workers are standalone thread classes — not wired into application lifecycle yet (S22 scope)
- No real model files in dev environment — all verification is contract-level (imports, instantiation, math)
- HealthCalculator assumes `total_teeth` is always provided; no fallback for unknown tooth count

## Follow-ups

- S22: Wire DetectionWorker and LDCWorker into lifecycle (start/stop with camera service)
- S22: Write detection results to camera.db via SQLiteService queue
- S23: Include camera telemetry (broken_count, wear_percentage, health_score) in ThingsBoard payload

## Files Created/Modified

- `src/services/camera/modelB4.py` — New: vendored LDC model definition (LDC, CoFusion, DenseBlock, UpConvBlock classes)
- `src/services/camera/health_calculator.py` — New: HealthCalculator with calculate_saw_health, get_health_status, get_health_color
- `src/services/camera/detection_worker.py` — New: DetectionWorker daemon thread with dual RT-DETR inference pipeline
- `src/services/camera/ldc_worker.py` — New: LDCWorker daemon thread with LDC inference + contour wear + health scoring
- `requirements.txt` — Added AI/Vision section (ultralytics, torch, torchvision)
- `config/config.yaml` — Added ldc_checkpoint_path to camera.wear section

## Forward Intelligence

### What the next slice should know
- Workers are ready to instantiate — pass (config['camera'], CameraResultsStore(), camera_service) to constructors. Call `worker.start()` to begin, `worker.stop()` then `worker.join()` to shutdown.
- DetectionWorker and LDCWorker are both daemon threads — they'll die with the main process, but explicit stop/join is cleaner.
- CameraResultsStore keys written by workers: `broken_count`, `broken_confidence`, `tooth_count`, `crack_count`, `crack_confidence`, `last_detection_ts` (from DetectionWorker); `wear_percentage`, `health_score`, `health_status`, `health_color`, `last_wear_ts` (from LDCWorker).
- HealthCalculator is a standalone class with no torch dependency — safe to import anywhere without triggering heavy ML loads.

### What's fragile
- Model path resolution — workers use paths from config directly. If config paths are relative, they resolve against cwd. S22 should ensure paths are absolute or relative to a known base.
- LDC wear computation uses hardcoded ROI constants (TOP_LINE_Y=170, BOTTOM_LINE_Y=236) matching the old project. If camera angle or resolution changes, these need recalibration.

### Authoritative diagnostics
- `CameraResultsStore.snapshot()` — single call returns all detection and wear state; the ground truth for what workers have published
- `worker.model_load_failed` — check before assuming worker is producing results; True means checkpoint wasn't found or failed to load
- Worker thread logs — INFO on model load success/failure, DEBUG on each inference cycle

### What assumptions changed
- Plan assumed `get_health_status(55.0)` returns 'İyi' — actually returns 'Orta' per reference code thresholds (İyi requires >=60). Not a bug, just incorrect test expectation in the plan.
