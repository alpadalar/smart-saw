# S21: AI Detection Pipeline

**Goal:** RT-DETR broken/crack detection and LDC wear calculation run in dedicated threads with results published to CameraResultsStore.
**Demo:** `python3 -c "from src.services.camera.health_calculator import HealthCalculator; h=HealthCalculator(); print(h.calculate_saw_health(100, 5, 20.0))"` prints a health score; DetectionWorker and LDCWorker instantiate without error; all new modules import cleanly without triggering torch/ultralytics at `__init__.py` level.

## Must-Haves

- DetectionWorker thread loads both RT-DETR models (broken + crack) inside `run()`, reads frames from CameraService, writes results to CameraResultsStore
- LDCWorker thread loads LDC model (modelB4 + BIPED checkpoint) inside `run()`, reads frames, computes wear percentage, writes to store
- HealthCalculator computes health score from broken count and wear percentage (70/30 weight)
- modelB4.py vendored into src/services/camera/
- All inference wrapped in `torch.no_grad()`
- `from __future__ import annotations` in all new modules
- Models load inside `run()` only — never at import time or `__init__()`
- `__init__.py` does NOT import new worker modules (zero-import guard)
- Graceful handling when model files are missing (log error, don't crash)
- `ultralytics`, `torch`, `torchvision` added to requirements.txt
- LDC checkpoint path added to camera config

## Proof Level

- This slice proves: contract
- Real runtime required: no (model files not in dev environment)
- Human/UAT required: no

## Verification

- `python3 -c "from src.services.camera.health_calculator import HealthCalculator; h=HealthCalculator(); score=h.calculate_saw_health(100, 5, 20.0); assert 90 < score < 100, f'unexpected {score}'; print('health_calculator OK')"` — health score math correct
- `python3 -c "from src.services.camera.health_calculator import HealthCalculator; h=HealthCalculator(); assert h.get_health_status(85.0)=='Sağlıklı'; assert h.get_health_status(55.0)=='İyi'; assert h.get_health_color(15.0)=='#FF0000'; print('status/color OK')"` — status text and color thresholds
- `python3 -c "from src.services.camera.modelB4 import LDC; print('modelB4 OK')"` — LDC model definition imports (requires torch)
- `python3 -c "from src.services.camera.detection_worker import DetectionWorker; print('detection_worker OK')"` — import succeeds
- `python3 -c "from src.services.camera.ldc_worker import LDCWorker; print('ldc_worker OK')"` — import succeeds
- `python3 -c "from src.services.camera import CameraResultsStore; print('zero-import OK')"` — does NOT trigger torch/ultralytics import
- `python3 -c "from src.services.camera.detection_worker import DetectionWorker; from src.services.camera.results_store import CameraResultsStore; store=CameraResultsStore(); w=DetectionWorker({'detection':{'enabled':True,'interval_seconds':2,'confidence_threshold':0.5,'broken_model_path':'x.pt','crack_model_path':'y.pt'}}, store, None); print('detection instantiation OK')"` — constructor works without models
- `python3 -c "from src.services.camera.ldc_worker import LDCWorker; from src.services.camera.results_store import CameraResultsStore; store=CameraResultsStore(); w=LDCWorker({'wear':{'enabled':True,'interval_seconds':5,'ldc_checkpoint_path':'x.pth'}}, store, None); print('ldc instantiation OK')"` — constructor works without models
- `grep -q 'ultralytics' requirements.txt && grep -q 'torch>=' requirements.txt && echo 'requirements OK'`
- `grep -q 'ldc_checkpoint_path' config/config.yaml && echo 'config OK'`

## Observability / Diagnostics

- Runtime signals: logger.info on model load success/failure with model path and device; logger.info on each detection cycle with broken_count/crack_count; logger.info on each wear calculation with wear_percentage; logger.error on model file missing or load failure
- Inspection surfaces: `CameraResultsStore.snapshot()` returns detection keys (`broken_count`, `crack_count`, `wear_percentage`, `health_score`, `health_status`, `health_color`, `last_detection_ts`, `last_wear_ts`)
- Failure visibility: Workers log error with model path when checkpoint not found; set `model_load_failed` flag readable from outside; exit `run()` gracefully without crash
- Redaction constraints: none

## Integration Closure

- Upstream surfaces consumed: `CameraResultsStore` (results_store.py), `CameraService.get_current_frame()` (camera_service.py), camera config section (config.yaml)
- New wiring introduced in this slice: none — workers are standalone thread classes, not wired into lifecycle yet
- What remains before the milestone is truly usable end-to-end: S22 lifecycle wiring (start/stop workers), S23 IoT integration, S24 GUI

## Tasks

- [x] **T01: Vendor modelB4, build HealthCalculator, update deps and config** `est:45m`
  - Why: Provides the foundational pieces — LDC model definition, health scoring logic, and dependency declarations. All pure logic/vendoring, testable immediately without models or hardware. Unblocks T02 and T03.
  - Files: `src/services/camera/modelB4.py`, `src/services/camera/health_calculator.py`, `requirements.txt`, `config/config.yaml`
  - Do: Copy modelB4.py from old project (`/media/workspace/eskiimas/smart-saw/src/vision/ldc/modelB4.py`) into `src/services/camera/modelB4.py` — add `from __future__ import annotations` at top, keep everything else as-is. Build HealthCalculator class porting from old project's `saw_health_calculator.py` — same formula (broken_weight=0.7, wear_weight=0.3), same status thresholds, same color codes. Add `from __future__ import annotations`. Add `ultralytics>=8.3.70`, `torch>=2.6.0`, `torchvision>=0.21.0` to requirements.txt. Add `ldc_checkpoint_path: "data/models/ldc/16_model.pth"` to camera.wear config section.
  - Verify: `python3 -c "from src.services.camera.modelB4 import LDC; print('OK')"` and health calculator unit tests (calculate_saw_health, get_health_status, get_health_color)
  - Done when: modelB4 imports LDC class; HealthCalculator returns correct scores for known inputs; requirements.txt has torch/ultralytics; config has ldc_checkpoint_path

- [x] **T02: Build DetectionWorker for RT-DETR broken and crack detection** `est:1h`
  - Why: Implements the core broken tooth and crack detection pipeline — the primary AI capability of the camera system. Single thread running two RT-DETR models sequentially, reading live frames from CameraService and publishing results to CameraResultsStore.
  - Files: `src/services/camera/detection_worker.py`
  - Do: Create DetectionWorker(threading.Thread) with constructor taking (config, results_store, camera_service). Load both RT-DETR models (broken `best.pt` + crack `catlak-best.pt`) inside `run()` using ultralytics RTDETR class. On each cycle: get frame via camera_service.get_current_frame(), copy it, run broken detection (class 0=tooth, class 1=broken, conf=0.5, imgsz=960), then crack detection (class 0=crack, conf=0.5, imgsz=960) on same frame. Write results to store: broken_count, broken_confidence, crack_count, crack_confidence, detection_image_path, last_detection_ts. All inference in torch.no_grad(). Check _stop_event between model loads and before each cycle. Handle missing model files gracefully (log error, return). Use `from __future__ import annotations`.
  - Verify: `python3 -c "from src.services.camera.detection_worker import DetectionWorker; print('OK')"` and instantiation test with mock config
  - Done when: DetectionWorker imports cleanly; constructor accepts (config, store, camera_service); run() loads models inside thread; detection cycle reads frame, runs both models, writes results to store

- [x] **T03: Build LDCWorker for edge detection wear measurement** `est:1h`
  - Why: Implements the wear measurement pipeline — LDC edge detection followed by contour-based wear percentage calculation. Reads frames from CameraService, runs LDC model, computes wear, publishes to store, and triggers health recalculation.
  - Files: `src/services/camera/ldc_worker.py`
  - Do: Create LDCWorker(threading.Thread) with constructor taking (config, results_store, camera_service). Load LDC model from modelB4.py and BIPED checkpoint inside `run()`. On each cycle: get frame, resize to 512x512, BGR mean subtraction ([103.939, 116.779, 123.68]), transpose to CHW, run LDC forward pass under torch.no_grad(), sigmoid + normalize + threshold the fused output, compute wear via contour analysis (same TOP_LINE_Y=170, BOTTOM_LINE_Y=236 logic as old VisionService._compute_wear). Write wear_percentage, last_wear_ts to store. After each detection or wear update, call HealthCalculator.calculate_saw_health() and write health_score, health_status, health_color to store. Handle missing checkpoint gracefully. Use `from __future__ import annotations`.
  - Verify: `python3 -c "from src.services.camera.ldc_worker import LDCWorker; print('OK')"` and instantiation test with mock config
  - Done when: LDCWorker imports cleanly; constructor accepts (config, store, camera_service); run() loads LDC model inside thread; wear cycle reads frame, runs LDC, computes wear, writes results and health score to store

## Files Likely Touched

- `src/services/camera/modelB4.py` — New: vendored LDC model definition
- `src/services/camera/health_calculator.py` — New: HealthCalculator with scoring formula
- `src/services/camera/detection_worker.py` — New: DetectionWorker thread with RT-DETR
- `src/services/camera/ldc_worker.py` — New: LDCWorker thread with LDC + wear calculation
- `requirements.txt` — Add ultralytics, torch, torchvision
- `config/config.yaml` — Add ldc_checkpoint_path to wear section
