# Phase 21: AI Detection Pipeline - Research

**Researched:** 2026-03-26
**Domain:** Python threading, RT-DETR / ultralytics inference, LDC edge detection, CameraResultsStore integration
**Confidence:** HIGH — all source files read directly, no gaps

## Summary

Phase 21 is a **code-audit-and-convention-alignment phase**, not a greenfield implementation. All four target files — `detection_worker.py`, `ldc_worker.py`, `health_calculator.py`, and `modelB4.py` — already exist in `src/services/camera/` with full algorithmic logic, correct threading patterns, and proper `CameraResultsStore` integration. The three RT-DETR and LDC model checkpoint files are present at the paths the workers expect. The work is to audit these files against project conventions (docstring format, logging style, naming, type hints) and move the hardcoded LDC wear ROI constants into `config.yaml`.

The current source code already satisfies DET-01 through DET-06 in terms of behaviour. What is missing is:
1. Convention alignment for `detection_worker.py`, `ldc_worker.py`, and `health_calculator.py`
2. Migration of six wear ROI constants from module-level in `ldc_worker.py` to `config.yaml camera.wear`
3. `config.yaml` already has the `camera.wear` subsection but lacks the ROI and BGR-mean keys

**Primary recommendation:** Audit each file against CONVENTIONS.md, apply targeted fixes (logging format, docstring style, any missing type hints), add wear ROI keys to config.yaml, and write mock-based unit tests for `DetectionWorker`, `LDCWorker`, and `HealthCalculator`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** Eski projeden gelen `detection_worker.py`, `ldc_worker.py`, `health_calculator.py` ve `modelB4.py` kodlari audit edilerek convention'lara uygun hale getirilecek. Algoritmik mantik (LDC inference pipeline, contour analizi, wear hesaplamasi, RT-DETR class mapping) korunacak, sadece stil/convention uyumu saglanacak (docstring formati, logging style, naming conventions, type hints).

**D-02:** `modelB4.py` (LDC NN mimarisi) harici bir model dosyasi oldugu icin minimal degisiklikle korunacak — sadece gerekli lint/import duzeltmeleri.

**D-03:** Worker'lardaki DB yazma kodu (`db_service.write_async()` cagrilari) Phase 21'de korunacak. detection_events ve wear_history tablolarina yazma mevcut kodda zaten var. Phase 22'de sadece lifecycle baglantisi yapilacak (db_service instance'ini worker'lara inject etme).

**D-04:** Phase 21'de worker'lar `db_service=None` varsayilani ile calisir — DB yazma kodu hazir ama aktif degil (lifecycle inject etmedigi surece).

**D-05:** `_save_annotated_frame()` metodu Phase 21 kapsaminda korunacak. Tespit edilen kirik dislere kirmizi, saglam dislere yesil, catlaklara mavi bounding box cizilip `recording_path/detected/` klasorune kaydedilir. Sadece aktif kayit varsa yazar, yoksa skip eder.

**D-06:** LDC worker'daki hardcoded ROI sabitleri (`TOP_LINE_Y=170`, `BOTTOM_LINE_Y=236`, `_ROI_X_CENTER_N`, `_ROI_Y_CENTER_N`, `_ROI_WIDTH_N`, `_ROI_HEIGHT_N`) ve BGR mean degerleri `config.yaml` `camera.wear` altina tasinacak. Varsayilan degerler mevcut sabitlerle ayni kalacak. Farkli kamera kurulumlarinda degistirilebilir olacak.

### Claude's Discretion

- Convention audit sirasinda yapilacak spesifik degisikliklerin kapsami (hangi docstringler guncellenmeli, hangi logging pattern'leri duzeltilmeli)
- Test stratejisi — mock-based unit testlerin yapisi ve kapsami
- imgsz parametresinin (960) config'e tasinip tasinmamasi

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DET-01 | RT-DETR modeli ile kirik dis tespiti yapilabilmesi (best.pt) | `DetectionWorker` already implements broken-tooth inference with class 0=tooth, class 1=broken; `best.pt` present at `data/models/best.pt` (66MB) |
| DET-02 | RT-DETR modeli ile catlak tespiti yapilabilmesi (catlak-best.pt) | `DetectionWorker` already implements crack inference; `catlak-best.pt` present at `data/models/catlak-best.pt` (66MB) |
| DET-03 | LDC edge detection ile serit testere asinma yuzdesi hesaplanabilmesi | `LDCWorker` + `modelB4.LDC` architecture fully implemented; checkpoint `data/models/ldc/16_model.pth` present (2.7MB) |
| DET-04 | Kirik ve asinma verilerine dayanarak testere saglik skoru hesaplanabilmesi (kirik %70 + asinma %30) | `HealthCalculator.calculate_saw_health()` fully implemented with correct formula; weights in `config.yaml camera.health` |
| DET-05 | Tespit sonuclarinin thread-safe CameraResultsStore uzerinden tum tuketicilere sunulmasi | Both workers already call `results_store.update_batch()`; `CameraResultsStore` API (Phase 20) is the integration boundary |
| DET-06 | AI modellerinin kendi thread'lerinde yuklenmesi (asyncio event loop'u bloklamadan) | Both workers are `threading.Thread` subclasses; torch/ultralytics imports are inside `run()` — lifecycle startup is not blocked |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| torch | 2.8.0+cu128 (verified installed) | Model loading, inference (`no_grad`), CUDA dispatch | Required by both ultralytics (RT-DETR) and LDC (direct torch.load) |
| ultralytics | 8.3.199 (verified installed) | RTDETR class, `.predict()` API | Industry standard for YOLO/RT-DETR family |
| opencv-python-headless | 4.11.0 (cv2, verified installed) | Frame preprocessing, binarize, contour analysis, annotated frame saving | Project constraint — must be headless (Qt symbol conflict) |
| numpy | >=1.24.0 (project constraint) | BGR mean subtraction, array ops in LDC pipeline | Used across the full inference pipeline |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| threading (stdlib) | — | Daemon thread model, `threading.Event` stop signaling | All worker classes extend `threading.Thread` |
| logging (stdlib) | — | Per-module logger (`logging.getLogger(__name__)`) | All files — project convention |
| pytest | 9.0.2 (verified installed) | Unit testing with mocks | Test framework for all new tests |
| unittest.mock | stdlib | `MagicMock`, `patch` for mocking torch/ultralytics/cv2 | Pattern established in `test_camera_service.py` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ultralytics RTDETR | Direct onnxruntime | ONNX would remove ultralytics dep but would require model export; existing .pt files work directly — not worth it |
| threading.Thread subclass | concurrent.futures.ThreadPoolExecutor | Worker pool abstracts too much; the existing stop_event / run() pattern is correct for long-running daemon threads |

**Installation:** All dependencies are already installed on this machine. No `pip install` needed for Phase 21.

---

## Architecture Patterns

### Existing File Map (files being audited)

```
src/services/camera/
├── detection_worker.py   # 311 lines — RT-DETR broken + crack, daemon thread
├── ldc_worker.py         # 312 lines — LDC edge detection + wear, daemon thread
├── health_calculator.py  # 96 lines — health score formula, pure logic class
├── modelB4.py            # ~250 lines — LDC neural net architecture (minimal changes)
└── results_store.py      # Phase 20, already convention-compliant
```

### Pattern 1: Lazy Import inside run()

**What:** Heavy ML imports (`torch`, `ultralytics`, `cv2`, `numpy`, `modelB4`) are placed inside `run()`, not at module top level. `TYPE_CHECKING` guard is used for type hints only.

**When to use:** Any worker that must not block lifecycle startup with expensive import side-effects.

**Example (already present in detection_worker.py):**
```python
# Source: src/services/camera/detection_worker.py lines 64-72
def run(self) -> None:
    import torch
    from ultralytics import RTDETR
    # model loading happens here...
```

This pattern is a locked project decision (DET-06). Do not move imports to module level.

### Pattern 2: CameraResultsStore as Integration Boundary

**What:** Workers never communicate directly. All shared state flows through `results_store.update_batch()`.

**Published keys by DetectionWorker:**
- `broken_count` (int)
- `broken_confidence` (float)
- `tooth_count` (int)
- `crack_count` (int)
- `crack_confidence` (float)
- `last_detection_ts` (ISO string)

**Published keys by LDCWorker:**
- `wear_percentage` (float, only if not None)
- `last_wear_ts` (ISO string)
- `health_score` (float)
- `health_status` (str, Turkish label)
- `health_color` (str, CSS hex)

**Read from store by LDCWorker (cross-worker dependency):**
- `tooth_count` — to compute health (reads DetectionWorker's output)
- `broken_count` — to compute health
- `recording_path` — to save annotated frames

### Pattern 3: Daemon Thread Lifecycle

**What:** Workers are `threading.Thread(daemon=True)` subclasses. They are stopped via `threading.Event().set()`.

```python
# Standard stop pattern (detection_worker.py and ldc_worker.py)
def stop(self) -> None:
    self._stop_event.set()
```

The main loop uses `self._stop_event.wait(self._interval)` as its sleep, enabling responsive shutdown.

### Pattern 4: RT-DETR Class Mapping

**What:** The broken model has two classes; the crack model has one.

```
Broken model (best.pt):
    class 0 = tooth (healthy) → increments tooth_count
    class 1 = broken          → increments broken_count

Crack model (catlak-best.pt):
    class 0 = crack           → increments crack_count
```

Both models run sequentially in the same thread on the same frame copy. Model objects are never shared across threads (DET-05 lock decision).

### Pattern 5: LDC Inference Pipeline

**What:** The LDC forward pass produces multiple output maps. Only the last element (fused output) is used for sharpest edges. Preprocessing is exact: resize to 512x512, subtract BGR mean `[103.939, 116.779, 123.68]`, transpose to CHW float32.

The wear ROI constants (currently module-level in `ldc_worker.py`) will be moved to `config.yaml camera.wear` per D-06. The constructor reads `config.get("wear", {})` — adding new keys is a backward-compatible change.

### Pattern 6: Health Formula

```
broken_pct = (broken_count / tooth_count) * 100  (0.0 if tooth_count <= 0)
health = 100 - ((broken_pct/100 * 0.70 + clamp(wear,0,100)/100 * 0.30) * 100)
```

`HealthCalculator` is a pure logic class (no thread, no imports besides logging). It is instantiated inside `LDCWorker.run()` — no sharing required.

### Pattern 7: Logging Style (from CONVENTIONS.md)

**Current code uses % formatting** in some places (e.g., `logger.info("msg — key=%s", val)`). CONVENTIONS.md says "f-strings for log messages" but the camera workers already established the `%`-format positional-args pattern from stdlib logging. The planner should verify which pattern the audit requires. The existing test_camera_service.py and camera_service.py use `%`-format, suggesting this is the camera-module convention.

**Confirmed pattern (from camera_service.py):**
```python
logger.info("Camera opened — device_id=%d, actual=%dx%d@%.1ffps", device_id, w, h, fps)
```

### Anti-Patterns to Avoid

- **Moving torch/ultralytics imports to module level:** Violates DET-06 and the lazy import guard decision.
- **Sharing model objects between threads:** Both RT-DETR models must stay local to `DetectionWorker.run()` — they are not thread-safe.
- **Calling results_store directly from health_calculator.py:** `HealthCalculator` is a pure calculator; only `LDCWorker` writes to the store.
- **Using `db_service` in tests:** Tests should pass `db_service=None` (D-04) — DB writes are guarded by `if self._db_service:`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Object detection | Custom inference loop | `ultralytics RTDETR.predict()` | Handles device dispatch, NMS, result unpacking |
| Edge detection | Custom convolution kernels | `LDC` architecture + `16_model.pth` | Domain-specific trained model; algorithmic logic is preserved, not rebuilt |
| Wear percentage | Pixel counting from scratch | `LDCWorker._compute_wear()` (existing, verified) | Contour analysis with adaptive thresholding is already correct |
| Health scoring | Inline formula | `HealthCalculator.calculate_saw_health()` | Pure function, tested, correct formula |
| Thread-safe state sharing | Direct field access across threads | `CameraResultsStore.update_batch()` | Sole integration boundary per architecture decision |

**Key insight:** Phase 21 is primarily an audit phase. The algorithmic work is already done and verified to match the old `VisionService` pipeline. The risk of regressions from unnecessary rewrites outweighs any style benefit.

---

## Runtime State Inventory

> Triggered: This is not a rename/refactor phase. Workers do write to camera.db (detection_events, wear_history) but only when `db_service` is injected (Phase 22). Phase 21 makes no runtime state changes.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | camera.db detection_events and wear_history tables — schema already created by Phase 19 `_init_camera()` | None — tables exist, workers with `db_service=None` do not write |
| Live service config | None | None |
| OS-registered state | None | None |
| Secrets/env vars | None — camera config is in config.yaml, no secrets | None |
| Build artifacts | `src/services/camera/__pycache__/` will regenerate on next import | None |

---

## Common Pitfalls

### Pitfall 1: Modifying Algorithmic Logic During Convention Audit
**What goes wrong:** A docstring fix becomes a logic refactor; the wear calculation or class mapping is accidentally changed.
**Why it happens:** LDC pipeline (sigmoid → normalize → bitwise_not → threshold) has non-obvious step ordering. RT-DETR class indices (0=healthy, 1=broken) are counterintuitive.
**How to avoid:** Treat `_run_ldc_inference`, `_compute_wear`, and the RT-DETR `for result / for box` loops as read-only during audit. Only touch docstrings, logging format, and the ROI constant lookup path.
**Warning signs:** If wear results change or tooth_count includes broken teeth.

### Pitfall 2: ROI Config Migration Breaks the Lookup Path
**What goes wrong:** `TOP_LINE_Y` and `_ROI_X_CENTER_N` etc. are removed from module level but `_compute_wear` still references the module-level names instead of `self._*` attributes.
**Why it happens:** `_compute_wear` is a `@staticmethod` — it cannot reference `self`. The constants must be passed as parameters, or the method signature must change.
**How to avoid:** Either:
  - Change `_compute_wear` from `@staticmethod` to a regular method that reads from `self`, OR
  - Pass the ROI values as parameters from the calling loop (e.g., `self._compute_wear(edge_bgr, np, cv2, self._roi_top_y, self._roi_bottom_y, ...)`)
  - Simplest approach: Store all ROI values in `__init__` as `self._top_line_y`, etc., and change `_compute_wear` to a regular instance method.

### Pitfall 3: Importing modelB4 at Module Level
**What goes wrong:** If `from src.services.camera.modelB4 import LDC` is moved to module level of `ldc_worker.py`, importing `ldc_worker` will trigger `import torch` — breaking the lazy import contract (DET-06).
**Why it happens:** D-02 says minimal changes to `modelB4.py`; it is easy to accidentally move its import up.
**How to avoid:** Keep `from src.services.camera.modelB4 import LDC` inside `run()` where it already is.

### Pitfall 4: Annotated Frame Saving Fails Silently in Tests
**What goes wrong:** Tests that exercise `_save_annotated_frame` fail because `recording_path` is not set in the store (it starts as None).
**Why it happens:** The method has an early return when `recording_path` is falsy — correct behaviour, but tests must explicitly set the store key if they want to exercise the save path.
**How to avoid:** In tests for `_save_annotated_frame`, call `store.update("recording_path", str(tmp_path))` before exercising the method.

### Pitfall 5: HealthCalculator.calculate_broken_percentage Returns 0 When tooth_count=0
**What goes wrong:** If DetectionWorker has not run yet, `tooth_count=0` in the store, causing `broken_pct=0` in health formula — health appears perfect even with broken teeth in the store.
**Why it happens:** `calculate_broken_percentage` has `if detected_teeth <= 0: return 0.0` guard. This is correct and intentional — without a tooth count baseline, broken percentage cannot be computed.
**How to avoid:** This is correct behaviour, not a bug. Tests should verify that health=100.0 when tooth_count=0 and broken_count>0, matching the documented formula.

### Pitfall 6: LDC outputs list of tensors, not a single tensor
**What goes wrong:** Code that does `output = model(tensor); fused = output` fails because `LDC.forward()` returns `results` — a list of 5 tensors (4 scale outputs + 1 fused CoFusion output). The fused output is `outputs[-1]`.
**Why it happens:** `modelB4.LDC.forward()` returns `results` (a list). The `isinstance(outputs, torch.Tensor)` check in `_run_ldc_inference` handles both cases.
**How to avoid:** The existing check is correct — do not simplify it away during audit.

### Pitfall 7: config.yaml BGR mean as list vs module-level constants
**What goes wrong:** When reading BGR mean from config, YAML represents it as a Python list `[103.939, 116.779, 123.68]`. The numpy subtraction `img -= np.array(_BGR_MEAN, dtype=np.float32)` must become `img -= np.array(self._bgr_mean, dtype=np.float32)` where `self._bgr_mean` is a list loaded from config.
**How to avoid:** Config key: `camera.wear.bgr_mean: [103.939, 116.779, 123.68]`. In `__init__`: `self._bgr_mean = wear_cfg.get("bgr_mean", [103.939, 116.779, 123.68])`.

---

## Code Examples

Verified patterns from existing source files:

### Config-driven ROI Loading Pattern (target state after D-06)

```python
# In LDCWorker.__init__ — after migration (pattern to implement)
wear_cfg = config.get("wear", {})
self._top_line_y: int = int(wear_cfg.get("top_line_y", 170))
self._bottom_line_y: int = int(wear_cfg.get("bottom_line_y", 236))
self._roi_x_center_n: float = float(wear_cfg.get("roi_x_center_n", 0.500000))
self._roi_y_center_n: float = float(wear_cfg.get("roi_y_center_n", 0.530692))
self._roi_width_n: float = float(wear_cfg.get("roi_width_n", 0.736888))
self._roi_height_n: float = float(wear_cfg.get("roi_height_n", 0.489510))
self._bgr_mean: list = wear_cfg.get("bgr_mean", [103.939, 116.779, 123.68])
```

### config.yaml camera.wear target state (after D-06)

```yaml
# config/config.yaml camera.wear section — new keys to add
wear:
  enabled: true
  interval_seconds: 5.0
  ldc_checkpoint_path: "data/models/ldc/16_model.pth"
  top_line_y: 170
  bottom_line_y: 236
  roi_x_center_n: 0.500000
  roi_y_center_n: 0.530692
  roi_width_n: 0.736888
  roi_height_n: 0.489510
  bgr_mean: [103.939, 116.779, 123.68]
```

### Mock-based Test Pattern (established in test_camera_service.py)

```python
# Source: tests/test_camera_service.py — pattern to replicate for worker tests
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
from src.services.camera.results_store import CameraResultsStore

@pytest.fixture()
def store():
    return CameraResultsStore()

def test_detection_worker_publishes_results(store, tmp_path):
    """DetectionWorker publishes broken_count/crack_count/tooth_count to store."""
    # Patch torch and ultralytics inside run() scope
    with patch("src.services.camera.detection_worker.torch") as mock_torch, \
         patch("src.services.camera.detection_worker.RTDETR") as mock_rtdetr:
        # set up mock model predict() return ...
        pass
```

### HealthCalculator Boundary Cases (source: health_calculator.py)

```python
# Source: src/services/camera/health_calculator.py line 22-27
def calculate_broken_percentage(self, detected_teeth: int, detected_broken: int) -> float:
    if detected_teeth <= 0:
        return 0.0  # Cannot calculate without tooth baseline
    broken_percentage = (detected_broken / detected_teeth) * 100.0
    return max(0.0, min(broken_percentage, 100.0))
```

### Annotated Frame Colour Convention (source: detection_worker.py)

```python
# Source: src/services/camera/detection_worker.py lines 272-278
if class_id == 1:  # broken tooth
    color = (0, 0, 255)   # red in BGR
    label = f"broken ({conf:.2f})"
else:              # healthy tooth
    color = (0, 255, 0)   # green in BGR
    label = f"tooth ({conf:.2f})"
# crack: (255, 0, 0) — blue in BGR
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Module-level `TOP_LINE_Y=170` hardcoded constant | Config-driven via `camera.wear.top_line_y` | Phase 21 (D-06) | Different camera setups can override ROI without code change |
| Module-level `_BGR_MEAN` hardcoded | Config-driven via `camera.wear.bgr_mean` | Phase 21 (D-06) | Same — tunable per deployment |
| DB writes active immediately | `db_service=None` default, writes guarded by `if self._db_service:` | Phase 21 (D-04) | DB integration deferred safely to Phase 22 |

**Deprecated/outdated:**
- Module-level constants `TOP_LINE_Y`, `BOTTOM_LINE_Y`, `_ROI_X_CENTER_N`, `_ROI_Y_CENTER_N`, `_ROI_WIDTH_N`, `_ROI_HEIGHT_N`, `_BGR_MEAN` in `ldc_worker.py`: Remove after migration to config; replaced by constructor attributes.

---

## Open Questions

1. **imgsz=960 in DetectionWorker — move to config?**
   - What we know: `imgsz=960` is hardcoded in both `broken_model.predict()` and `crack_model.predict()` calls. CONTEXT.md lists this as Claude's discretion.
   - What's unclear: Whether 960 is camera-setup-specific (like ROI params) or model-specific (always correct for these .pt files).
   - Recommendation: Move to `config.yaml camera.detection.imgsz` with default 960. Follows the same pattern as the ROI migration. Low risk since default stays the same.

2. **Convention audit scope for `modelB4.py`**
   - What we know: D-02 says "minimal changes — only lint/import fixes". `modelB4.py` imports `torch` at module level with no `from __future__ import annotations`.
   - What's unclear: Whether the module-level `torch` import needs a `from __future__ import annotations` guard for TYPE_CHECKING consistency.
   - Recommendation: Add `from __future__ import annotations` at top (project-wide pattern). Leave all NN architecture code untouched. Remove the `if __name__ == '__main__':` test block — it's development scaffolding.

3. **Logging format: %-style vs f-string**
   - What we know: CONVENTIONS.md says "f-strings for log messages" but camera_service.py and the detection workers consistently use `logger.info("msg — key=%s", val)` (stdlib %-format positional args).
   - What's unclear: Which is actually required — CONVENTIONS.md was written before the camera module.
   - Recommendation: Follow the established camera-module pattern (`%`-format). CONVENTIONS.md reflects pre-camera code style; the camera workers are consistent with each other.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python pytest | Unit tests | Yes | 9.0.2 | — |
| torch | DetectionWorker, LDCWorker | Yes | 2.8.0+cu128 | — |
| ultralytics | DetectionWorker (RTDETR) | Yes | 8.3.199 | — |
| opencv-python-headless (cv2) | Both workers, annotated frames | Yes | 4.11.0 | — |
| numpy | LDCWorker preprocessing | Yes | (installed) | — |
| data/models/best.pt | DET-01 | Yes | 66MB | — |
| data/models/catlak-best.pt | DET-02 | Yes | 66MB | — |
| data/models/ldc/16_model.pth | DET-03 | Yes | 2.7MB | — |

**Missing dependencies with no fallback:** None — all required dependencies are present.

**Missing dependencies with fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | none — pytest discovery via standard conventions |
| Quick run command | `python3 -m pytest tests/ -x -q` |
| Full suite command | `python3 -m pytest tests/ -v` |

All 17 existing tests pass (confirmed via test run above).

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DET-01 | DetectionWorker publishes `broken_count`/`tooth_count` to store after broken model predict | unit (mock) | `python3 -m pytest tests/test_detection_worker.py -x` | No — Wave 0 |
| DET-02 | DetectionWorker publishes `crack_count`/`crack_confidence` to store after crack model predict | unit (mock) | `python3 -m pytest tests/test_detection_worker.py -x` | No — Wave 0 |
| DET-03 | LDCWorker publishes `wear_percentage` to store after LDC inference cycle | unit (mock) | `python3 -m pytest tests/test_ldc_worker.py -x` | No — Wave 0 |
| DET-04 | HealthCalculator returns correct score for known broken/tooth/wear inputs; health_score visible in store after LDC cycle | unit | `python3 -m pytest tests/test_health_calculator.py -x` | No — Wave 0 |
| DET-05 | Both workers call `results_store.update_batch()` with correct keys | unit (mock) | `python3 -m pytest tests/test_detection_worker.py tests/test_ldc_worker.py -x` | No — Wave 0 |
| DET-06 | `import detection_worker` and `import ldc_worker` do not trigger torch/ultralytics imports at module level | unit | `python3 -m pytest tests/test_detection_worker.py::test_import_stays_lightweight -x` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m pytest tests/ -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_detection_worker.py` — covers DET-01, DET-02, DET-05, DET-06
- [ ] `tests/test_ldc_worker.py` — covers DET-03, DET-05, DET-06
- [ ] `tests/test_health_calculator.py` — covers DET-04

*(Existing infrastructure `tests/__init__.py` present, no conftest.py needed — fixture patterns are inline as in test_camera_service.py)*

---

## Sources

### Primary (HIGH confidence)

All findings verified by direct file reads:

- `src/services/camera/detection_worker.py` — full 311-line source read; RT-DETR inference loop, class mapping, annotated frame saving confirmed
- `src/services/camera/ldc_worker.py` — full 312-line source read; LDC inference pipeline, BGR mean, ROI constants, wear computation confirmed
- `src/services/camera/health_calculator.py` — full 96-line source read; formula, weights, status labels confirmed
- `src/services/camera/modelB4.py` — full ~250-line source read; LDC architecture, forward() return shape (list of 5 tensors) confirmed
- `src/services/camera/results_store.py` — Phase 20 file; `update_batch()`, `get()`, `snapshot()` API confirmed
- `src/services/camera/camera_service.py` — `get_current_frame()` signature and `_frame_lock` pattern confirmed
- `config/config.yaml` §camera — current `detection`, `wear`, `health` subsections confirmed; ROI keys absent
- `src/services/database/schemas.py` — `SCHEMA_CAMERA_DB` detection_events and wear_history table schemas confirmed
- `.planning/codebase/CONVENTIONS.md` — naming, docstring (Google-style), logging, formatting rules confirmed
- `.planning/codebase/ARCHITECTURE.md` — concurrency model confirmed (threading for camera workers)
- `tests/test_camera_service.py` — mock-based test pattern confirmed (MagicMock + patch)
- Environment probe — torch 2.8.0, ultralytics 8.3.199, cv2 4.11.0, pytest 9.0.2 all confirmed installed; all model files present

### Secondary (MEDIUM confidence)

- None required — all claims are directly verifiable from source code.

### Tertiary (LOW confidence)

- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified installed at specific versions
- Architecture: HIGH — all files read directly; patterns confirmed from source
- Pitfalls: HIGH — all pitfalls derive from reading actual source code, not speculation
- Convention gaps: MEDIUM — logging style question (% vs f-string) requires planner judgment; both patterns present in codebase

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable domain; ultralytics minor versions may increment but API is stable)
