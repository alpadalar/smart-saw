---
estimated_steps: 7
estimated_files: 1
---

# T03: Build LDCWorker for edge detection wear measurement

**Slice:** S21 — AI Detection Pipeline
**Milestone:** M001

## Description

Build the LDCWorker — a daemon thread that loads the LDC edge detection model (modelB4 + BIPED checkpoint), runs per-frame LDC inference to produce edge maps, then computes saw blade wear percentage via contour analysis. After each wear update, recalculates the overall health score using HealthCalculator. Results are published to CameraResultsStore.

## Steps

1. Create `src/services/camera/ldc_worker.py` with `from __future__ import annotations` at top. Import threading, time, logging, os, datetime. Use `TYPE_CHECKING` guard for type hints referencing CameraResultsStore and CameraService. Do NOT import torch, cv2, numpy at module level — import them inside `run()`.

2. Define `class LDCWorker(threading.Thread)`:
   - `__init__(self, config: dict, results_store: CameraResultsStore, camera_service: CameraService)`:
     - Extract from config dict: `config.get("wear", {})` → `enabled`, `interval_seconds` (default 5.0), `ldc_checkpoint_path` (default "data/models/ldc/16_model.pth")
     - Also extract health config: `config.get("health", {})` → `broken_weight` (default 0.70), `wear_weight` (default 0.30) — pass to HealthCalculator constructor or use defaults
     - Store results_store and camera_service references
     - Create `self._stop_event = threading.Event()`
     - Set `daemon=True`, `name="ldc-worker"`
     - Initialize `self._model_load_failed = False` flag

3. Implement `run(self)`:
   - Import `torch`, `cv2`, `numpy as np` at top of method
   - Import `from src.services.camera.modelB4 import LDC`
   - Import `from src.services.camera.health_calculator import HealthCalculator`
   - Create HealthCalculator instance
   - Determine device: `'cuda' if torch.cuda.is_available() else 'cpu'`
   - Load LDC model:
     ```python
     model = LDC().to(device)
     ```
   - Load checkpoint: check file exists first. If missing, log error with path, set `_model_load_failed = True`, return
     ```python
     state = torch.load(checkpoint_path, map_location=device)
     model.load_state_dict(state)
     model.eval()
     ```
   - Check `_stop_event.is_set()` after model load
   - Log success: checkpoint path, device
   - Enter main loop: `while not self._stop_event.is_set():`

4. Implement LDC inference inside the loop:
   - Get frame: `frame = self._camera_service.get_current_frame()` — if None, sleep interval, continue
   - Copy frame: `frame = frame.copy()`
   - Preprocess (matching old VisionService._run_ldc_on_image):
     - `h, w = frame.shape[:2]`
     - Resize to 512x512: `resized = cv2.resize(frame, (512, 512))`
     - Convert to float32 and subtract BGR mean: `img = resized.astype(np.float32); img -= np.array([103.939, 116.779, 123.68], dtype=np.float32)`
     - Transpose HWC→CHW: `img = img.transpose(2, 0, 1)`
     - Create tensor: `tensor = torch.from_numpy(img).unsqueeze(0).to(device)`
   - Forward pass under `torch.no_grad()`:
     - `outputs = model(tensor)` → returns list of edge maps
     - Process fused output (last element): sigmoid → normalize 0-1 → scale to 0-255 uint8 → bitwise_not → resize back to (w, h)
     - Binarize: invert → threshold at 180 → invert back
     - Convert to BGR: `edge_bgr = cv2.cvtColor(edge_gray, cv2.COLOR_GRAY2BGR)`

5. Implement wear calculation (matching old VisionService._compute_wear):
   - Constants: `TOP_LINE_Y = 170`, `BOTTOM_LINE_Y = 236`
   - Define ROI using normalized bounding box: `x_center_n=0.500000`, `y_center_n=0.530692`, `width_n=0.736888`, `height_n=0.489510`
   - Calculate pixel coordinates, clamp to image bounds, y1=TOP_LINE_Y, y2=BOTTOM_LINE_Y
   - Extract ROI, convert to grayscale
   - Adaptive threshold: if mean < 90 use THRESH_BINARY at 180, else THRESH_BINARY_INV at 128
   - Find contours, collect Y coordinates
   - If < 5 contour points, wear_percentage = None (skip)
   - Otherwise: find top 10% of Y values (min k=5, max k=50), mean of smallest = min_y
   - `wear_y = min_y + y1`
   - `percent = ((wear_y - TOP_LINE_Y) / (BOTTOM_LINE_Y - TOP_LINE_Y)) * 100.0` clamped 0-100

6. Publish results and recalculate health:
   - Write to store: `wear_percentage`, `last_wear_ts` (ISO format)
   - Read current detection state from store: `tooth_count = store.get("tooth_count", 0)`, `broken_count = store.get("broken_count", 0)`
   - Calculate health: `health_calc.calculate_saw_health(tooth_count, broken_count, wear_percentage)`
   - Get status and color
   - Write to store via `update_batch()`: `health_score`, `health_status`, `health_color`
   - Log wear cycle at debug level
   - `self._stop_event.wait(self._interval)` at end of loop

7. Implement `stop(self)` and `@property model_load_failed`.

## Must-Haves

- [ ] `from __future__ import annotations` at module top
- [ ] torch/cv2/numpy imported inside `run()`, not at module level
- [ ] LDC model + checkpoint loaded inside `run()` method
- [ ] BGR mean subtraction: [103.939, 116.779, 123.68]
- [ ] LDC input: 512x512 resized, CHW, float32
- [ ] All inference wrapped in `torch.no_grad()`
- [ ] Fused output (last map): sigmoid → normalize → uint8 → bitwise_not → resize → binarize
- [ ] Wear calculation with TOP_LINE_Y=170, BOTTOM_LINE_Y=236 matching old project
- [ ] HealthCalculator called after each wear update, results in store
- [ ] Graceful handling when checkpoint missing (log error, set flag, return)
- [ ] daemon=True thread

## Verification

- `python3 -c "from src.services.camera.ldc_worker import LDCWorker; print('import OK')"`
- `python3 -c "from src.services.camera.ldc_worker import LDCWorker; from src.services.camera.results_store import CameraResultsStore; store=CameraResultsStore(); w=LDCWorker({'wear':{'enabled':True,'interval_seconds':5,'ldc_checkpoint_path':'x.pth'},'health':{}}, store, None); assert w.daemon; assert w.name=='ldc-worker'; assert not w.model_load_failed; print('instantiation OK')"`
- `python3 -c "from src.services.camera import CameraResultsStore; print('zero-import preserved')"` — verifies __init__.py still clean

## Observability Impact

- Signals added/changed: logger.info on LDC model load success (checkpoint path + device), logger.error on checkpoint missing or load failure, logger.debug each wear cycle (wear_percentage, health_score)
- How a future agent inspects this: `CameraResultsStore.snapshot()` → check `wear_percentage`, `health_score`, `health_status`, `health_color`, `last_wear_ts` keys; `LDCWorker.model_load_failed` property
- Failure state exposed: model_load_failed flag set when checkpoint missing; error logged with path

## Inputs

- `src/services/camera/modelB4.py` — LDC class from T01
- `src/services/camera/health_calculator.py` — HealthCalculator from T01
- `src/services/camera/results_store.py` — CameraResultsStore API
- `src/services/camera/camera_service.py` — CameraService.get_current_frame()
- Old project reference: `/media/workspace/eskiimas/smart-saw/src/vision/service.py` — VisionService._run_ldc_on_image (preprocessing, forward pass, post-processing) and _compute_wear (ROI, contour analysis, wear percentage formula)

## Expected Output

- `src/services/camera/ldc_worker.py` — LDCWorker(threading.Thread) with LDC inference + wear calculation + health scoring pipeline
