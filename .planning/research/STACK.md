# Technology Stack — Camera Vision & AI Detection

**Project:** Smart Saw Control System v2.0
**Milestone:** Camera Vision & AI Detection
**Researched:** 2026-03-16
**Overall confidence:** HIGH

---

## Executive Summary

This milestone adds camera capture, RT-DETR object detection, LDC edge-based wear calculation, and a camera GUI page to an existing PySide6 industrial desktop application. Four new library families are required: OpenCV for camera I/O, ultralytics for RT-DETR inference, PyTorch + kornia for LDC edge detection, and no new GUI toolkit (PySide6 QImage/QPixmap handles frame display natively).

The single most important constraint: **numpy version pinning**. ultralytics >=8.3.x and opencv-python >=4.11.x have migrated toward numpy 2.x, but the transition is incomplete across the ecosystem. The existing `requirements.txt` pins `numpy<2.0,>=1.24.0`. This constraint must be relaxed to `numpy>=1.24.0` (no upper bound) and tested — or the inverse, hold numpy<2 and pin older opencv/ultralytics. Recommendation: allow numpy 2.x and pin opencv-python>=4.11.0 which declares numpy>=2 on Python 3.9+, then verify ultralytics 8.4.x works (it does as of 8.3.70+).

The camera display thread pattern (QThread worker emitting QImage signals to a QLabel slot) is a well-established PySide6 pattern. No additional Qt packages required beyond what is already installed.

---

## New Dependencies Required

### Camera I/O

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| `opencv-python-headless` | `>=4.11.0` | Frame capture (VideoCapture), BGR→RGB conversion, JPEG encoding | headless variant avoids OpenCV's own Qt5 GUI bindings which conflict with PySide6's Qt6. The `cv2` namespace is identical. Do NOT install `opencv-python` (has Qt5 GUI backend that conflicts). |

**Why opencv-python-headless not opencv-python:**
`opencv-python` ships compiled against Qt5 for its `cv2.imshow()` GUI. PySide6 uses Qt6. Both try to load different Qt major versions into the same process, causing symbol conflicts on Linux. The headless variant strips the GUI backend entirely — safe to use alongside PySide6. The `cv2` API surface for VideoCapture, imencode, cvtColor, and numpy array operations is identical.

**Latest version:** 4.13.0.92 (released 2026-02-05). Pin `>=4.11.0` to allow updates; the 4.11+ series adds numpy 2.x compatibility.

### AI Object Detection (RT-DETR)

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| `ultralytics` | `>=8.3.70` | RT-DETR inference via `from ultralytics import RTDETR` | Single unified API for loading custom `.pt` weights and running inference. Returns structured `Results` objects with `.boxes.xyxy`, `.boxes.conf`, `.boxes.cls`. Manages ONNX/TorchScript export if needed later. |

**Usage pattern:**
```python
from ultralytics import RTDETR

# Load custom-trained weights (best.pt or catlak-best.pt)
model = RTDETR("data/models/best.pt")

# Run inference on a numpy BGR frame from OpenCV
results = model(frame, conf=0.5, verbose=False)

# Extract detections
for result in results:
    boxes = result.boxes.xyxy    # (N, 4) tensor: x1, y1, x2, y2
    confs = result.boxes.conf    # (N,) tensor: confidence scores
    classes = result.boxes.cls   # (N,) tensor: class indices
```

**Latest version:** 8.4.22 (released 2026-03-14). Pin `>=8.3.70` for numpy 2.x compatibility fix.

### Deep Learning Runtime (PyTorch)

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| `torch` | `>=2.6.0` | Tensor operations, model execution backend for both ultralytics and LDC | Required by both ultralytics (RTDETR) and kornia (LDC). CPU-only sufficient for industrial panel PC without discrete GPU. |
| `torchvision` | `>=0.21.0` | Image transforms used by ultralytics internals | ultralytics imports torchvision transforms; must be version-matched to torch. |

**Version pairing (official PyTorch compatibility table):**

| torch | torchvision | Notes |
|-------|-------------|-------|
| 2.10.0 | 0.25.0 | Latest stable (2026-01-21) |
| 2.6.0 | 0.21.0 | Minimum recommended |

**Recommendation:** Pin `torch>=2.6.0` and `torchvision>=0.21.0`. Let pip resolve to latest compatible pair. Do NOT pin to exact versions — PyTorch releases often; allow updates.

**CPU-only install note:** The default `torch` wheel from PyPI includes CUDA. For industrial panel PCs without GPU, install from PyTorch's CPU index:
```
--index-url https://download.pytorch.org/whl/cpu
```
This reduces install size significantly (~200MB vs ~2GB). Add this to deployment documentation, not requirements.txt, since the index URL is environment-specific.

### LDC Edge Detection + Wear Calculation

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| `kornia` | `>=0.7.0` | Differentiable image processing used by LDC model (gaussian blur, morphological ops) | LDC's original implementation uses kornia for several preprocessing and postprocessing operations. Requires PyTorch (already added). |

**LDC model integration approach:**
LDC (Lightweight Dense CNN for Edge Detection, ~0.7M parameters) is not a pip package — it is source code. The model files (`modelB4.py` or `modelB5.py`) from [github.com/xavysp/LDC](https://github.com/xavysp/LDC) are copied directly into `src/services/camera/` as part of the codebase. The trained weights file (`.pth`) is loaded via `torch.load()`. This means:
- No `pip install ldc` — copy model source into repo
- Weights file path configured via `config.yaml` (same pattern as `ml.model_path`)
- Inference is pure PyTorch forward pass on a single frame

**LDC wear calculation output:** The edge map (float32 numpy array, 0-1 range) is postprocessed to count edge pixels in the tooth region, comparing against a reference baseline to compute wear percentage. This is custom application logic, not a library.

**Latest kornia version:** 0.8.2 (released 2025-11-08). Pin `>=0.7.0` for stable API.

---

## numpy Version Strategy

**Critical constraint — resolve before any other install.**

The existing `requirements.txt` pins `numpy<2.0,>=1.24.0`. This must change:

| Package | numpy Requirement |
|---------|-----------------|
| ultralytics >=8.3.70 | numpy >=1.23.0 (no upper bound since 8.3.70) |
| opencv-python-headless >=4.11.0 | numpy >=2 (on Python 3.9+) for 4.13.x |
| torch 2.6+ | numpy >=1.26.4 |
| kornia 0.7+ | numpy >=1.21.2 |
| existing scikit-learn, pandas | numpy >=1.24.0 |

**Resolution:** Change requirements.txt line from `numpy<2.0,>=1.24.0` to `numpy>=1.24.0`. Allow pip to install numpy 2.x. Test the full stack. If scikit-learn or joblib complain (they typically don't above numpy 2.0 with recent versions), pin those to current versions explicitly.

**Do NOT** stay on numpy<2.0 and try to work around it — opencv-python-headless 4.13.x requires numpy>=2 on Python 3.9+.

---

## PySide6 Camera Display (No New Packages)

PySide6 already installed (`>=6.4.0`). The camera display pipeline uses built-in Qt classes:

| Qt Class | Import | Purpose |
|----------|--------|---------|
| `QThread` | `PySide6.QtCore` | Camera capture worker — isolates blocking VideoCapture.read() from GUI event loop |
| `Signal` | `PySide6.QtCore` | Worker emits `Signal(QImage)` per frame |
| `QImage` | `PySide6.QtGui` | Wrap numpy BGR frame (after cvtColor to RGB) |
| `QPixmap` | `PySide6.QtGui` | Convert QImage for display in QLabel |
| `QLabel` | `PySide6.QtWidgets` | Display area — `setPixmap(QPixmap.fromImage(qimage))` |

**Frame conversion pattern (no extra library needed):**
```python
import cv2
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt

# Convert OpenCV BGR frame to QImage
frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
h, w, ch = frame_rgb.shape
bytes_per_line = ch * w
qimage = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

# Display in QLabel (called via signal from worker thread)
label.setPixmap(QPixmap.fromImage(qimage).scaled(
    label.size(), Qt.AspectRatioMode.KeepAspectRatio,
    Qt.TransformationMode.SmoothTransformation
))
```

**Why not qimage2ndarray:** Adds a dependency for a 3-line conversion. The manual QImage construction is adequate and keeps dependencies minimal.

**Thread model:** QThread subclass owns the VideoCapture loop. Emits `frame_ready = Signal(QImage)` at the camera's native frame rate (typ. 15-30 FPS). The GUI slot connected to this signal calls `setPixmap`. This follows the established project pattern (`run_coroutine_threadsafe` for async→GUI, this is GUI→GUI but cross-thread via signal).

---

## Updated requirements.txt

```txt
# Smart Saw Control System - Dependencies
# Python >= 3.10 required

# Core
python-dotenv>=1.0.0

# Async I/O
aiofiles>=23.0.0

# Modbus Communication
pymodbus[asyncio]>=3.5.0

# Database
aiosqlite>=0.19.0
asyncpg>=0.29.0

# MQTT / IoT
aiomqtt>=1.2.0
httpx>=0.24.0

# GUI
PySide6>=6.4.0

# Machine Learning (existing)
numpy>=1.24.0          # Removed <2.0 cap — required by opencv-python-headless >=4.11
scikit-learn>=1.3.0
joblib>=1.3.0
pandas>=2.0.0

# Configuration
pyyaml>=6.0

# Logging
colorlog>=6.7.0

# === NEW: Camera Vision & AI Detection (v2.0) ===

# Camera capture (headless — no Qt5 GUI backend, safe alongside PySide6 Qt6)
opencv-python-headless>=4.11.0

# RT-DETR object detection (broken teeth, crack detection)
ultralytics>=8.3.70

# PyTorch runtime (required by ultralytics and LDC)
# NOTE: For CPU-only deployment install from:
#   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
torch>=2.6.0
torchvision>=0.21.0

# Differentiable image ops used by LDC edge detection model
kornia>=0.7.0
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Camera capture | `opencv-python-headless` | `opencv-python` | Qt5 vs Qt6 conflict on Linux |
| Object detection | `ultralytics` (RTDETR) | PyTorch native (raw model code) | ultralytics handles preprocessing, NMS-free pipeline, results API |
| Object detection | `ultralytics` (RTDETR) | ONNX Runtime + exported model | Adds onnxruntime dependency; losing ultralytics training/export workflow |
| Edge detection | LDC (vendored source) | Canny (cv2.Canny) | Canny is parameter-sensitive, non-learned; LDC is pretrained on edge datasets |
| Edge detection | LDC (vendored source) | HED (pytorch-hed pip) | LDC is lighter (~0.7M params vs HED's ~14.7M); better for real-time on CPU |
| Frame display | PySide6 QImage/QPixmap | `cv2PySide6` package | Adds dependency; 3-line QImage construction is sufficient |
| Frame display | PySide6 QImage/QPixmap | `qimage2ndarray` | Same as above — unnecessary |
| numpy | `>=1.24.0` (allow 2.x) | Pin `<2.0` | Would require pinning older opencv-python-headless; blocks security updates |

---

## Config-Driven Modularity

The project requires `camera.enabled=false` to prevent any camera code from loading. This is a design constraint, not a library constraint. The pattern from `lifecycle.py` (config-driven service init):

**config.yaml addition:**
```yaml
camera:
  enabled: false          # Set true to enable camera module
  device_index: 0         # VideoCapture device index (0 = first USB cam)
  fps: 15                 # Target capture rate
  resolution:
    width: 1280
    height: 720
  jpeg_quality: 85        # JPEG recording quality
  models:
    broken_tooth: "data/models/best.pt"
    crack: "data/models/catlak-best.pt"
    ldc_weights: "data/models/ldc_weights.pth"
  detection:
    confidence_threshold: 0.5
    inference_rate_hz: 2    # Run inference at 2 Hz to manage CPU load
  wear:
    baseline_edge_count: null   # Calibrated per saw band
    wear_threshold_percent: 70  # Warn above 70% wear
  health:
    broken_weight: 0.70   # 70% contribution from broken/crack detections
    wear_weight: 0.30     # 30% contribution from wear calculation
```

**Lifecycle guard pattern (matches existing style):**
```python
# In lifecycle.py — camera services only loaded if enabled
if self.config.get("camera.enabled", False):
    from ..services.camera import CameraService
    self.camera_service = CameraService(config=self.config)
    await self.camera_service.start()
```

This ensures `import ultralytics`, `import cv2`, `import torch` never execute when `camera.enabled=false`, so the application starts normally even without these packages installed in constrained environments.

---

## Integration Points with Existing System

| New Component | Integrates With | How |
|---------------|----------------|-----|
| CameraService (new) | `lifecycle.py` | Config-guarded startup/shutdown, same pattern as `MQTTService` |
| RT-DETR detector | `SQLiteService` | Writes detection events to new `camera_detections` table in `anomaly.db` or new `camera.db` |
| RT-DETR detector | `ThingsBoard IoT` | Publishes detection results as telemetry fields (broken_tooth_detected, crack_detected, wear_percent, health_score) |
| Camera GUI page | `GUIApplication` (app.py) | Added as 5th page in `QStackedWidget`; sidebar button added to navigation |
| Camera GUI page | `CameraService` | Worker `QThread` lives in service; GUI page connects to its signals |
| LDC wear calculator | existing `ProcessedData` model | No model change — wear % stored separately in camera DB |

---

## What NOT to Add

| Package | Reason |
|---------|--------|
| `onnxruntime` | Not needed — ultralytics runs native PyTorch; ONNX export is optional for deployment |
| `tensorrt` | GPU-specific; industrial panel PC is CPU-only |
| `opencv-python` | Conflicts with PySide6 Qt6 on Linux — use headless variant only |
| `Pillow` | Not needed — OpenCV handles JPEG encoding; QImage handles display |
| `supervision` | Roboflow's annotation library; unnecessary wrapper over ultralytics Results API |
| `albumentations` | Training augmentation only; not used at inference time |
| `tflite-runtime` | TF-specific; project uses PyTorch models |
| `cv2PySide6` | Thin wrapper providing no value over direct QImage construction |
| `qimage2ndarray` | Same as above — 3-line conversion is sufficient |
| `imutils` | Old utility library; opencv-python-headless covers all needed ops |
| `torchaudio` | Audio processing; irrelevant to vision pipeline |

---

## Confidence Assessment

| Area | Confidence | Sources | Notes |
|------|------------|---------|-------|
| ultralytics RT-DETR API | HIGH | PyPI (8.4.22), ultralytics docs, official RT-DETR docs | Verified latest version, API confirmed stable |
| opencv-python-headless version | HIGH | PyPI (4.13.0.92 current) | Official PyPI, date verified |
| torch/torchvision versions | HIGH | PyTorch Versions wiki (official), PyPI | 2.10.0/0.25.0 latest; 2.6.0/0.21.0 minimum safe |
| kornia version | HIGH | PyPI (0.8.2 current) | Official PyPI |
| numpy 2.x transition | MEDIUM | Multiple GitHub issues, PyPI metadata | Ecosystem still in transition; `>=4.11.0` opencv-python-headless works with numpy 2.x; verify on deployment |
| opencv-python-headless vs opencv-python conflict | HIGH | OpenCV forum, multiple sources | Qt5 vs Qt6 symbol conflict is well-documented and consistent |
| QThread + QImage camera display | HIGH | Qt for Python official docs, multiple working examples | Standard established pattern |
| LDC as vendored source | HIGH | LDC GitHub (xavysp/LDC) — pip package does not exist | Confirmed: no pip install, must vendor model code |
| CPU-only PyTorch performance | MEDIUM | General knowledge | Inference at 2 Hz on CPU for ~720p image should be feasible for panel PC; validate with actual hardware |

---

## Sources

- [ultralytics PyPI page](https://pypi.org/project/ultralytics/) — version 8.4.22 confirmed (2026-03-14)
- [Ultralytics RT-DETR docs](https://docs.ultralytics.com/models/rtdetr/) — custom model loading, Results API
- [ultralytics predict docs](https://docs.ultralytics.com/modes/predict/) — `.boxes.xyxy`, `.boxes.conf`, `.boxes.cls`
- [opencv-python PyPI](https://pypi.org/project/opencv-python/) — latest 4.13.0.92 (2026-02-05)
- [PyTorch Versions wiki](https://github.com/pytorch/pytorch/wiki/PyTorch-Versions) — official version compatibility table
- [torch PyPI](https://pypi.org/project/torch/) — 2.10.0 latest (2026-01-21)
- [torchvision PyPI](https://pypi.org/project/torchvision/) — 0.25.0 latest
- [kornia PyPI](https://pypi.org/project/kornia/) — 0.8.2 latest (2025-11-08)
- [LDC GitHub xavysp/LDC](https://github.com/xavysp/LDC) — Lightweight Dense CNN, ~0.7M params, PyTorch >=1.6
- [Qt for Python QThread docs](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html) — official threading docs
- [QImage construction from numpy](https://github.com/fernicar/PySide6_Examples_Doc_2025_v6.9.1/tree/6.9.1/examples/external/opencv) — PySide6 2025 official example
- [opencv-python GitHub](https://github.com/opencv/opencv-python) — headless vs full variant documentation
- [numpy 2.x ecosystem tracking](https://github.com/numpy/numpy/issues/26191) — compatibility status
