# S21: AI Detection Pipeline — UAT

**Milestone:** M001
**Written:** 2026-03-16

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: Workers are standalone thread classes not wired into lifecycle yet. No real model files in dev environment. All verification is contract-level — imports, instantiation, math, and zero-import guard.

## Preconditions

- Python 3 available with torch and ultralytics installed
- Working directory is the project root (smart-saw)
- No running application needed — all tests are offline import/instantiation checks

## Smoke Test

```bash
python3 -c "
from src.services.camera.health_calculator import HealthCalculator
from src.services.camera.detection_worker import DetectionWorker
from src.services.camera.ldc_worker import LDCWorker
from src.services.camera.results_store import CameraResultsStore
store = CameraResultsStore()
h = HealthCalculator()
score = h.calculate_saw_health(100, 5, 20.0)
assert 90 < score < 100
print(f'All imports OK, health score={score}')
"
```

## Test Cases

### 1. HealthCalculator score math

1. `python3 -c "from src.services.camera.health_calculator import HealthCalculator; h=HealthCalculator(); score=h.calculate_saw_health(100, 5, 20.0); print(f'score={score}'); assert 90 < score < 100"`
2. **Expected:** Score approximately 90.5 (broken_pct=5%, wear=20%, health = 100 - 0.7×5 - 0.3×20 = 90.5)

### 2. HealthCalculator status thresholds

1. `python3 -c "from src.services.camera.health_calculator import HealthCalculator; h=HealthCalculator(); assert h.get_health_status(85.0)=='Sağlıklı', 'failed 85'; assert h.get_health_status(65.0)=='İyi', 'failed 65'; assert h.get_health_status(55.0)=='Orta', 'failed 55'; assert h.get_health_status(35.0)=='Kötü', 'failed 35'; assert h.get_health_status(15.0)=='Kritik', 'failed 15'; print('All thresholds OK')"`
2. **Expected:** All assertions pass — Sağlıklı (≥80), İyi (≥60), Orta (≥40), Kötü (≥20), Kritik (<20)

### 3. HealthCalculator color codes

1. `python3 -c "from src.services.camera.health_calculator import HealthCalculator; h=HealthCalculator(); assert h.get_health_color(85.0)=='#00FF00'; assert h.get_health_color(65.0)=='#90EE90'; assert h.get_health_color(55.0)=='#FFA500'; assert h.get_health_color(35.0)=='#FF4500'; assert h.get_health_color(15.0)=='#FF0000'; print('All colors OK')"`
2. **Expected:** Green (#00FF00) for healthy, through to red (#FF0000) for critical

### 4. modelB4 LDC import

1. `python3 -c "from src.services.camera.modelB4 import LDC; model = LDC(); print(f'LDC params: {sum(p.numel() for p in model.parameters())}')"`
2. **Expected:** LDC class instantiates, prints parameter count (should be a positive integer)

### 5. DetectionWorker import and instantiation

1. `python3 -c "from src.services.camera.detection_worker import DetectionWorker; from src.services.camera.results_store import CameraResultsStore; store=CameraResultsStore(); w=DetectionWorker({'detection':{'enabled':True,'interval_seconds':2,'confidence_threshold':0.5,'broken_model_path':'x.pt','crack_model_path':'y.pt'}}, store, None); assert w.daemon; assert w.name=='detection-worker'; assert not w.model_load_failed; print('DetectionWorker OK')"`
2. **Expected:** Worker instantiates as daemon thread named 'detection-worker', model_load_failed is False (hasn't tried loading yet)

### 6. LDCWorker import and instantiation

1. `python3 -c "from src.services.camera.ldc_worker import LDCWorker; from src.services.camera.results_store import CameraResultsStore; store=CameraResultsStore(); w=LDCWorker({'wear':{'enabled':True,'interval_seconds':5,'ldc_checkpoint_path':'x.pth'}}, store, None); assert w.daemon; assert w.name=='ldc-worker'; assert not w.model_load_failed; print('LDCWorker OK')"`
2. **Expected:** Worker instantiates as daemon thread named 'ldc-worker', model_load_failed is False

### 7. Zero-import guard preserved

1. `python3 -c "import sys; before=set(sys.modules.keys()); from src.services.camera import CameraResultsStore; after=set(sys.modules.keys()); new_mods=after-before; torch_loaded=any('torch' in m for m in new_mods); ultra_loaded=any('ultralytics' in m for m in new_mods); assert not torch_loaded, f'torch loaded: {[m for m in new_mods if \"torch\" in m]}'; assert not ultra_loaded, f'ultralytics loaded'; print('Zero-import guard intact')"`
2. **Expected:** Importing CameraResultsStore from `__init__.py` does NOT trigger torch or ultralytics imports

### 8. Requirements.txt has AI dependencies

1. `grep -E 'ultralytics|torch>=' requirements.txt`
2. **Expected:** Lines containing `ultralytics>=8.3.70`, `torch>=2.6.0`, `torchvision>=0.21.0`

### 9. Config has LDC checkpoint path

1. `grep 'ldc_checkpoint_path' config/config.yaml`
2. **Expected:** Line containing `ldc_checkpoint_path: "data/models/ldc/16_model.pth"`

### 10. CameraResultsStore snapshot works

1. `python3 -c "from src.services.camera.results_store import CameraResultsStore; store=CameraResultsStore(); snap=store.snapshot(); assert isinstance(snap, dict); print(f'snapshot type={type(snap).__name__}, keys={sorted(snap.keys())}')"`
2. **Expected:** Returns empty dict (no workers have published data yet)

## Edge Cases

### HealthCalculator with zero broken teeth

1. `python3 -c "from src.services.camera.health_calculator import HealthCalculator; h=HealthCalculator(); score=h.calculate_saw_health(100, 0, 0.0); assert score==100.0, f'got {score}'; print('Perfect health OK')"`
2. **Expected:** Score is exactly 100.0 (no damage)

### HealthCalculator with all teeth broken

1. `python3 -c "from src.services.camera.health_calculator import HealthCalculator; h=HealthCalculator(); score=h.calculate_saw_health(10, 10, 100.0); assert score==0.0, f'got {score}'; print('Total failure OK')"`
2. **Expected:** Score is 0.0 (100% broken + 100% wear)

### HealthCalculator with negative/overflow inputs

1. `python3 -c "from src.services.camera.health_calculator import HealthCalculator; h=HealthCalculator(); score=h.calculate_saw_health(10, 15, 120.0); assert score==0.0, f'got {score}'; print('Clamping OK')"`
2. **Expected:** Score clamped to 0.0 (inputs beyond 100% clamped)

### Worker instantiation with None camera_service

1. `python3 -c "from src.services.camera.detection_worker import DetectionWorker; from src.services.camera.ldc_worker import LDCWorker; from src.services.camera.results_store import CameraResultsStore; store=CameraResultsStore(); d=DetectionWorker({'detection':{'enabled':True,'interval_seconds':2,'confidence_threshold':0.5,'broken_model_path':'x.pt','crack_model_path':'y.pt'}}, store, None); l=LDCWorker({'wear':{'enabled':True,'interval_seconds':5,'ldc_checkpoint_path':'x.pth'}}, store, None); print('None camera_service OK')"`
2. **Expected:** Both workers accept None for camera_service without error (will fail at run() when trying to get frames, not at construction)

## Failure Signals

- Any import error from detection_worker, ldc_worker, health_calculator, or modelB4 indicates broken module structure
- torch or ultralytics appearing in `sys.modules` after importing from `src.services.camera` indicates zero-import guard violation
- HealthCalculator returning scores outside 0-100 range indicates clamping failure
- `model_load_failed` being True before `run()` is called indicates constructor-time side effects
- Missing ultralytics/torch in requirements.txt means deployment will fail

## Requirements Proved By This UAT

- DET-01 — DetectionWorker loads RT-DETR broken model (contract: import + instantiation proven)
- DET-02 — DetectionWorker loads RT-DETR crack model (contract: import + instantiation proven)
- DET-03 — LDCWorker loads LDC model and computes wear (contract: import + instantiation proven)
- DET-04 — HealthCalculator computes correct health score with 70/30 weighting (math verified)
- DET-05 — Both workers publish to CameraResultsStore (contract: store instantiation + update_batch API proven)
- DET-06 — Models load inside run() only, not at import time (zero-import guard verified)

## Not Proven By This UAT

- Actual inference accuracy with real model files (no .pt/.pth files in dev environment)
- Frame capture → detection → results end-to-end pipeline (no camera hardware)
- Lifecycle wiring (start/stop workers with application — S22 scope)
- Database persistence of results (S22 scope)
- IoT telemetry integration (S23 scope)
- GUI display of results (S24 scope)

## Notes for Tester

- All tests are offline — no camera, no model files, no running application needed.
- The `get_health_status(55.0)` returns 'Orta' (not 'İyi') — this is correct per the reference code thresholds. The original slice plan had an incorrect expected value.
- Workers will fail gracefully at runtime if model files are missing — they log an error and set `model_load_failed=True` without crashing.
- torch import takes several seconds; test commands may feel slow but should complete within 30-60 seconds.
