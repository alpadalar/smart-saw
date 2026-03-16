---
estimated_steps: 6
estimated_files: 1
---

# T02: Build DetectionWorker for RT-DETR broken and crack detection

**Slice:** S21 — AI Detection Pipeline
**Milestone:** M001

## Description

Build the DetectionWorker — a single daemon thread that loads two RT-DETR models (broken tooth detection + crack detection) and runs sequential inference on live camera frames. Results are published to CameraResultsStore. This is the core AI detection capability of the camera system.

## Steps

1. Create `src/services/camera/detection_worker.py` with `from __future__ import annotations` at the top. Import threading, time, logging, datetime, os. Use `TYPE_CHECKING` guard for type hints referencing CameraResultsStore and CameraService. Do NOT import `torch`, `ultralytics`, `cv2` at module level — import them inside `run()`.

2. Define `class DetectionWorker(threading.Thread)`:
   - `__init__(self, config: dict, results_store: CameraResultsStore, camera_service: CameraService)`:
     - Extract from config dict: `config.get("detection", {})` → `enabled`, `interval_seconds` (default 2.0), `confidence_threshold` (default 0.5), `broken_model_path` (default "data/models/best.pt"), `crack_model_path` (default "data/models/catlak-best.pt")
     - Store results_store and camera_service references
     - Create `self._stop_event = threading.Event()`
     - Set `daemon=True`, `name="detection-worker"`
     - Initialize `self._model_load_failed = False` flag

3. Implement `run(self)`:
   - Import `torch` and `from ultralytics import RTDETR` at top of method
   - Determine device: `'cuda' if torch.cuda.is_available() else 'cpu'`
   - Load broken model: `RTDETR(self._broken_model_path)` → `.to(device)`. Wrap in try/except — if file not found or load fails, log error with path, set `_model_load_failed = True`, return
   - Check `_stop_event.is_set()` after broken model load
   - Load crack model: same pattern with crack path
   - Check `_stop_event.is_set()` after crack model load
   - Log success: model paths, device
   - Enter main loop: `while not self._stop_event.is_set():`
     - Get frame: `frame = self._camera_service.get_current_frame()` — if None, sleep interval, continue
     - Copy frame: `frame = frame.copy()` (release frame_lock before inference)
     - Run broken detection: `with torch.no_grad(): results = broken_model.predict(source=frame, device=device, conf=self._confidence, imgsz=960, verbose=False)`
     - Parse broken results: count class 0 as `tooth_count`, class 1 as `broken_count`. Track max confidence for broken.
     - Run crack detection: `with torch.no_grad(): results = crack_model.predict(source=frame, device=device, conf=self._confidence, imgsz=960, verbose=False)`
     - Parse crack results: count class 0 as `crack_count`. Track max confidence.
     - Save annotated frame to disk (optional — in a `detected/` subdir of recordings_path if recording)
     - Publish to store via `update_batch()`: `broken_count`, `broken_confidence`, `tooth_count`, `crack_count`, `crack_confidence`, `last_detection_ts` (ISO format string)
     - Log detection cycle: broken_count, crack_count at debug level
     - `self._stop_event.wait(self._interval)` at end of loop

4. Implement `stop(self)`:
   - `self._stop_event.set()`

5. Implement `@property model_load_failed(self) -> bool`:
   - Returns `self._model_load_failed`

6. Verify import and instantiation work without torch/ultralytics being loaded at module level.

## Must-Haves

- [ ] `from __future__ import annotations` at module top
- [ ] torch/ultralytics imported inside `run()`, not at module level
- [ ] Both RT-DETR models loaded inside `run()` method
- [ ] `_stop_event` checked between model loads and in main loop
- [ ] Frame copied before inference (don't hold camera_service lock)
- [ ] All inference wrapped in `torch.no_grad()`
- [ ] `imgsz=960`, `conf` from config, `verbose=False`
- [ ] Broken detection: class 0=tooth, class 1=broken
- [ ] Crack detection: class 0=crack
- [ ] Results published to store: broken_count, tooth_count, broken_confidence, crack_count, crack_confidence, last_detection_ts
- [ ] Graceful handling when model files missing (log error, set flag, return)
- [ ] daemon=True thread

## Verification

- `python3 -c "from src.services.camera.detection_worker import DetectionWorker; print('import OK')"`
- `python3 -c "from src.services.camera.detection_worker import DetectionWorker; from src.services.camera.results_store import CameraResultsStore; store=CameraResultsStore(); w=DetectionWorker({'detection':{'enabled':True,'interval_seconds':2,'confidence_threshold':0.5,'broken_model_path':'x.pt','crack_model_path':'y.pt'}}, store, None); assert w.daemon; assert w.name=='detection-worker'; assert not w.model_load_failed; print('instantiation OK')"`
- `python3 -c "from src.services.camera import CameraResultsStore; print('zero-import preserved')"` — verifies __init__.py still clean

## Observability Impact

- Signals added/changed: logger.info on model load success (path + device), logger.error on model load failure (path + exception), logger.debug each detection cycle (broken_count, crack_count)
- How a future agent inspects this: `CameraResultsStore.snapshot()` → check `broken_count`, `crack_count`, `last_detection_ts` keys; `DetectionWorker.model_load_failed` property
- Failure state exposed: model_load_failed flag set when model files missing; error logged with model path for diagnosis

## Inputs

- `src/services/camera/results_store.py` — CameraResultsStore with update/update_batch/get/snapshot API
- `src/services/camera/camera_service.py` — CameraService.get_current_frame() returns raw numpy BGR array or None
- T01 completed — ultralytics and torch in requirements.txt
- Old project reference: `/media/workspace/eskiimas/smart-saw/src/core/broken_detect.py` — RT-DETR model loading, predict call with conf=0.5 imgsz=960, class 0=tooth class 1=broken
- Old project reference: `/media/workspace/eskiimas/smart-saw/src/core/crack_detect.py` — same pattern, class 0=crack

## Expected Output

- `src/services/camera/detection_worker.py` — DetectionWorker(threading.Thread) with dual RT-DETR inference pipeline
