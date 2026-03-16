# S21: AI Detection Pipeline — Research

**Date:** 2026-03-16
**Depth:** Targeted

## Summary

S21 builds three new modules — `DetectionWorker`, `LDCWorker`, and `HealthCalculator` — that run RT-DETR broken/crack detection and LDC wear calculation in dedicated threads, writing results to the existing `CameraResultsStore` from S20. The old project has complete working implementations (`broken_detect.py`, `crack_detect.py`, `vision/service.py`, `saw_health_calculator.py`) that serve as direct porting references. The architecture pattern is established: background daemon threads with `threading.Event` stop signal, results published to the Lock-guarded store.

The work is straightforward porting with one structural change: the old project uses global module-level model singletons and separate files for broken/crack detection. The new design consolidates both RT-DETR models into a single `DetectionWorker` thread (sequential inference, no model sharing across threads), adds an `LDCWorker` thread for wear calculation, and a pure `HealthCalculator` class. All three publish results to `CameraResultsStore`.

Key constraints: models must load inside their thread's `run()` method (not at import time), all inference must be wrapped in `torch.no_grad()`, and no module imports `cv2` or `torch` at module level (use `from __future__ import annotations` for type hints). `kornia` is NOT needed — the old project's LDC pipeline uses only PyTorch and OpenCV, no kornia imports anywhere.

## Recommendation

Port directly from old project with these structural changes:

1. **DetectionWorker** — single thread, loads both RT-DETR models (broken `best.pt` + crack `catlak-best.pt`) sequentially inside `run()`. Reads frames from `CameraService.get_current_frame()` on a configurable interval (default 2s). Runs broken detection then crack detection on the same frame. Writes results to store as `broken_count`, `broken_confidence`, `crack_count`, `crack_confidence`, `detection_image_path`, `last_detection_ts`.

2. **LDCWorker** — single thread, loads LDC model (`modelB4.py` + BIPED checkpoint) inside `run()`. Reads frames on a configurable interval (default 5s). Runs LDC edge detection → wear calculation. Writes `wear_percentage`, `last_wear_ts` to store.

3. **HealthCalculator** — stateless class, called after detection or wear updates. Formula: `health = 100 - (broken_pct * broken_weight + wear_pct * wear_weight)`. Writes `health_score`, `health_status`, `health_color` to store.

4. **LDC model file** — vendor `modelB4.py` into `src/services/camera/` (pure PyTorch, ~240 lines, no external deps beyond torch). Copy the BIPED checkpoint (2.7MB) to `data/models/ldc/16_model.pth`.

5. **Config addition** — add `wear.ldc_model_path` and `wear.ldc_checkpoint_path` to the camera config section.

6. **Requirements** — add `ultralytics>=8.3.70`, `torch>=2.6.0`, `torchvision>=0.21.0` to `requirements.txt`. Skip `kornia` — not used.

## Implementation Landscape

### Key Files

- `src/services/camera/results_store.py` — Existing: thread-safe store. S21 adds new keys (`broken_count`, `crack_count`, `wear_percentage`, `health_score`, etc.) but no code changes needed — the store is key-agnostic.
- `src/services/camera/camera_service.py` — Existing: provides `get_current_frame()` returning raw numpy BGR array. Detection workers read frames from here.
- `src/services/camera/__init__.py` — Update exports to include new modules.
- `src/services/camera/detection_worker.py` — **New**: `DetectionWorker(threading.Thread)` running both RT-DETR models.
- `src/services/camera/ldc_worker.py` — **New**: `LDCWorker(threading.Thread)` running LDC edge detection + wear calculation.
- `src/services/camera/modelB4.py` — **New**: Vendored LDC model definition (copy from old project, no modifications needed).
- `src/services/camera/health_calculator.py` — **New**: `HealthCalculator` class with `calculate()` and status/color helpers.
- `config/config.yaml` — Add `wear.ldc_checkpoint_path` to camera config.
- `requirements.txt` — Add `ultralytics>=8.3.70`, `torch>=2.6.0`, `torchvision>=0.21.0`.

### Source References (Old Project)

| New File | Old Project Source | Key Changes |
|----------|-------------------|-------------|
| `detection_worker.py` | `core/broken_detect.py` + `core/crack_detect.py` | Merge into single thread; read live frames instead of scanning disk; write to store instead of JSON |
| `ldc_worker.py` | `vision/service.py` (VisionService._ldc_worker + _compute_wear) | Simplify to single thread; read frames from CameraService; write to store instead of CSV |
| `modelB4.py` | `vision/ldc/modelB4.py` | Copy as-is, no changes |
| `health_calculator.py` | `core/saw_health_calculator.py` | Direct port, minor cleanup |

### Build Order

1. **Copy `modelB4.py`** — zero risk, pure vendoring. Unblocks LDCWorker.
2. **`health_calculator.py`** — pure logic, no dependencies on camera/torch. Unit-testable immediately.
3. **`detection_worker.py`** — depends on ultralytics/torch being available. Thread reads from a `CameraService` instance and writes to `CameraResultsStore`.
4. **`ldc_worker.py`** — depends on `modelB4.py` and torch. Same thread pattern as detection worker.
5. **Config + requirements updates** — add LDC checkpoint path, add pip dependencies.
6. **Update `__init__.py`** — export new modules.

Build health_calculator first since it's pure logic and verifiable without any hardware or models. Then detection_worker and ldc_worker can be built in parallel since they're independent.

### Verification Approach

1. **health_calculator** — unit test: `calculate_saw_health(100, 5, 20.0)` returns expected score; status/color thresholds verified.
2. **detection_worker** — instantiation test: `DetectionWorker(config, results_store, camera_service)` constructs without error. Import test: `from src.services.camera.detection_worker import DetectionWorker`.
3. **ldc_worker** — instantiation test: same pattern. Verify `modelB4.py` imports: `from src.services.camera.modelB4 import LDC`.
4. **Integration test** — create a `CameraResultsStore`, mock a frame in it, start detection worker with a test image, verify store gets `broken_count` key populated.
5. **Zero-import guard** — verify `python3 -c "from src.services.camera import CameraResultsStore"` does NOT trigger torch/ultralytics imports. The new worker modules should NOT be imported in `__init__.py` at the top level.

## Constraints

- **Models load inside `run()` only** — `torch.load()` and `RTDETR()` constructor must execute inside the thread's `run()` method, never at import time or in `__init__()`. This prevents blocking the asyncio event loop and ensures models are only loaded when camera is enabled.
- **`from __future__ import annotations`** in all new camera module files — prevents type annotation evaluation from triggering torch/cv2 imports at import time.
- **`torch.no_grad()` wrapping all inference** — prevents gradient buffer allocation which would double memory usage.
- **No `kornia` dependency** — the LDC model and wear calculation use only torch + cv2 + numpy. The milestone research incorrectly listed kornia as required.
- **No DB writes in S21** — that's S22 scope. Workers only write to `CameraResultsStore`.
- **`__init__.py` must NOT import new worker modules** — they transitively import torch/ultralytics. Only `CameraResultsStore` and `CameraService` remain in `__init__.py` exports.
- **imgsz=960** — old project uses `imgsz=960` for RT-DETR inference. Preserve this for model accuracy parity.
- **BGR input to models** — OpenCV reads BGR, RT-DETR via ultralytics accepts BGR (handles conversion internally). LDC preprocessing uses BGR mean subtraction. Do not convert to RGB before model inference.

## Common Pitfalls

- **Shared model instances across threads** — each worker must own its own model instances, loaded inside its own `run()`. The old project uses global singletons with locks — don't copy that pattern.
- **Frame access race** — `CameraService.get_current_frame()` is Lock-guarded, returns the raw numpy array. Workers should copy the frame before processing to avoid holding the lock during inference.
- **Stop event not checked during model loading** — model loading takes 2-5s. Check `_stop_event.is_set()` after loading before entering the processing loop.
- **LDC checkpoint missing** — the BIPED checkpoint file (2.7MB) must be copied from the old project to `data/models/ldc/16_model.pth`. If missing, LDCWorker should log an error and exit gracefully, not crash.

## Open Risks

- **Model files not present in dev environment** — `best.pt`, `catlak-best.pt`, and `16_model.pth` are not in the current repo. Workers must handle missing model files gracefully (log error, set a `model_load_failed` flag, don't crash). These files will be copied from the old project during deployment.
- **CPU inference timing unknown** — RT-DETR at imgsz=960 on a 1280x720 frame may take 200-500ms per model on CPU. Two models per detection cycle = 400-1000ms. With 2s interval, this is fine. But on the industrial panel PC (likely weaker CPU), timing may need adjustment.

## Sources

- Old project broken detection: `/media/workspace/eskiimas/smart-saw/src/core/broken_detect.py` — RT-DETR model loading, per-frame inference with `conf=0.5, imgsz=960`, class 0=tooth, class 1=broken
- Old project crack detection: `/media/workspace/eskiimas/smart-saw/src/core/crack_detect.py` — separate RT-DETR model, class 0=crack
- Old project VisionService: `/media/workspace/eskiimas/smart-saw/src/vision/service.py` — LDC inference pipeline, wear calculation logic, 3-thread architecture (watcher/ldc/wear)
- Old project LDC model: `/media/workspace/eskiimas/smart-saw/src/vision/ldc/modelB4.py` — pure PyTorch, ~0.7M params, no kornia dependency
- Old project SawHealthCalculator: `/media/workspace/eskiimas/smart-saw/src/core/saw_health_calculator.py` — formula, status text, color codes
- Old project model files: `best.pt` (64MB), `catlak-best.pt` (64MB) at project root; `16_model.pth` (2.7MB) at `src/vision/ldc/checkpoints/BIPED/16/`
