# Project Research Summary

**Project:** Smart Saw Control System v2.0 — Camera Vision & AI Detection
**Domain:** Industrial camera-based band saw tooth inspection integrated into existing async Qt desktop
**Researched:** 2026-03-16
**Confidence:** HIGH

## Executive Summary

This milestone ports and modernizes a working camera vision system from a legacy codebase (`eskiimas/smart-saw`) into the current industrial control system. The scope is clear: add camera capture (OpenCV), RT-DETR object detection (broken teeth and cracks), LDC-based blade wear calculation, and a camera GUI page — all behind a `camera.enabled` config flag that guarantees zero camera code runs on machines without the hardware. The source implementation already exists and has been directly analyzed, which gives this research unusually high confidence. The primary challenge is not building novel algorithms — it is clean integration into an existing asyncio + Qt6 system without disrupting the critical 10 Hz Modbus control loop.

The recommended architecture is a fully isolated `services/camera/` module that never touches the asyncio event loop. All OpenCV capture and AI inference runs in dedicated `threading.Thread` workers. Results flow through a single `CameraResultsStore` singleton — a thread-safe dict that serves as the sole integration boundary between camera subsystem and everything else (GUI, IoT pipeline, database). The GUI polls this store via QTimers; the asyncio data pipeline reads it once per 10 Hz cycle as an optional attachment. This keeps the camera subsystem independent, testable in isolation, and incapable of degrading the control loop.

The most significant risk is the numpy version transition. The existing `requirements.txt` caps numpy below 2.0, but `opencv-python-headless >= 4.11.0` requires numpy 2.x on Python 3.9+. This cap must be removed before any other library work begins. Secondary risks are all threading/import-time pitfalls well-documented in the research: blocking `cv2.VideoCapture.read()` in asyncio context, sharing PyTorch model instances across threads, and importing camera modules unconditionally at module level. Each of these has a clear, verified prevention strategy.

---

## Key Findings

### Recommended Stack

Four new library families are needed. The PySide6 GUI toolkit (already installed) handles camera frame display natively via `QImage`/`QPixmap` — no additional Qt packages required.

**Core technologies:**
- `opencv-python-headless >= 4.11.0`: Camera capture and JPEG encoding — headless variant mandatory to avoid Qt5/Qt6 symbol conflict on Linux; headless and full have identical `cv2` API for VideoCapture/imencode/cvtColor
- `ultralytics >= 8.3.70`: RT-DETR inference via `RTDETR("best.pt")` — unified API for custom weights, structured `Results` objects, numpy 2.x compatible since 8.3.70
- `torch >= 2.6.0` + `torchvision >= 0.21.0`: PyTorch runtime for both ultralytics and LDC — CPU-only deploy from PyTorch CPU index to reduce install size from ~2GB to ~200MB
- `kornia >= 0.7.0`: Differentiable image ops used by LDC model preprocessing — requires PyTorch (already added)
- **LDC model:** Vendored source code (not a pip package) — copy `modelB4.py` from [xavysp/LDC](https://github.com/xavysp/LDC) into `src/services/camera/`; weights file path set via `config.yaml`

**Critical version change:** Remove the `numpy<2.0` cap from `requirements.txt`. Change to `numpy>=1.24.0` (no upper bound). `opencv-python-headless 4.13.x` requires numpy 2.x on Python 3.9+. Not doing this blocks all new dependencies.

**What NOT to add:** `opencv-python` (Qt5 conflict), `onnxruntime`, `tensorrt`, `Pillow`, `supervision`, `qimage2ndarray`, `torchaudio`.

See [STACK.md](./STACK.md) for full dependency table, version pairing table, and updated `requirements.txt`.

### Expected Features

This is a migration, not greenfield. The source system has a complete implementation; the task is porting and integrating it correctly.

**Must have (table stakes) — v2.0 launch:**
- `camera.enabled` config flag — zero camera code runs when false; entire module conditionally loaded
- OpenCV frame capture + JPEG recording — CameraModule with 1920x1200, configurable FPS, multi-thread JPEG encoder
- RT-DETR broken tooth detection — `best.pt` model, batch post-processing after recording, results to `detection_stats.json`
- RT-DETR crack detection — `catlak-best.pt` model, same batch pattern, separate crack count
- LDC wear pipeline — VisionService watchdog, concurrent with recording, outputs `wear.csv`
- SawHealthCalculator — `health = 100 - (broken_pct * 0.7 + wear_pct * 0.3)`; status text
- Camera GUI page — live feed, detection stats, wear %, health score, sequential image thumbnails (4 frames)
- Sidebar navigation button — 5th button in existing sidebar; only appears when `camera.enabled=true`
- Detection results to SQLite — new `camera.db` with `detection_events` and `wear_history` tables
- Detection results to ThingsBoard IoT — camera telemetry fields added to existing HTTP send cycle

**Should have (differentiators) — port from old project, low risk:**
- Sequential image thumbnails panel (4 frames, 240x150px) — already in source; direct port
- Detection status OK/alert icons per category — single-glance defect status
- Wear visualization overlay (red boundary lines) — makes LDC measurement visible to operator
- Health status color coding — red/yellow/green comprehension without reading numbers
- Serit_id correlation on detection results — `serit_id` available from Modbus register 2230 in existing system

**Defer to v2.x+:**
- Per-recording history panel — UI redesign required; trigger: operator request
- Configurable confidence threshold via UI — trigger: false positive complaints
- Recording retention policy (auto-delete old recordings) — trigger: disk space alerts

**Anti-features (do not implement):**
- Real-time AI inference during recording — CPU cannot handle RT-DETR at frame rate; record-then-detect is the correct pattern
- Continuous video recording (MP4/AVI) — disk space: ~54GB/30min session; JPEG sequence with selective retention is intentional
- Multi-camera support — single `device_id` integer in config; document extension point, don't implement

See [FEATURES.md](./FEATURES.md) for full feature dependency graph, prioritization matrix, and file format specs.

### Architecture Approach

The camera subsystem is a self-contained module (`src/services/camera/`) loaded entirely via lazy imports behind the `camera.enabled` config guard. The sole integration boundary is `CameraResultsStore` — a thread-safe singleton that producers (camera/vision threads) write to and consumers (GUI QTimers, IoT pipeline) read from. Neither `CameraController` nor `DataProcessingPipeline` import any camera module directly; they only hold a reference to the store.

**Major components (build order = dependency order):**
1. **Config schema + DB schema** — additive-only changes to `config.yaml` and `schemas.py`; zero code risk; everything else depends on this
2. **CameraResultsStore** (`results_store.py`) — thread-safe dict with `threading.Lock`; no external deps; fully unit-testable in isolation
3. **CameraService** (`camera_service.py`) — OpenCV capture thread + JPEG encoder threads; fills store with `latest_frame`; testable with real hardware before models exist
4. **DetectionWorker + LDCWorker + HealthCalculator** — RT-DETR inference and LDC edge detection; models instantiated inside their own threads (not shared); testable with static test images
5. **VisionService** (`vision_service.py`) — orchestrates workers with scheduling (detection every 2s, LDC every 5s); wires DB writes via existing SQLiteService queue pattern
6. **Lifecycle integration** (`lifecycle.py`) — adds `_init_camera()` step after `_init_mqtt()`; lazy imports inside the config guard; camera DB created only when enabled
7. **Data pipeline IoT integration** (`data_processor.py`) — optional `camera_results_store` constructor parameter (defaults None); one `snapshot()` call per 10 Hz cycle; no hot-path changes
8. **CameraController** (`camera_controller.py`) — Qt widget; receives only `CameraResultsStore`; three QTimers at 500ms/1000ms/2000ms; never calls camera service directly
9. **MainController integration** (`main_controller.py`) — conditional 5th nav button + page; last because it's final assembly

**Key patterns:**
- Lazy import guard in `lifecycle.py` and `main_controller.py` — no `import cv2`/`import torch` unless `camera.enabled=true`
- Background threading for all camera/AI work — asyncio event loop never touched by camera code
- QTimer polling (not Qt signals from threads) — GUI reads store; store is the queue
- SQLiteService queue pattern for DB writes — detection thread calls `db_service.queue_write()`, never direct `sqlite3`

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full system diagram, data flow diagrams, code patterns, and build order with test criteria.

### Critical Pitfalls

Six critical/moderate pitfalls with verified prevention strategies:

1. **cv2.VideoCapture.read() blocking asyncio (Critical)** — Run all capture in a dedicated `threading.Thread`; asyncio side only reads the latest frame from the results store. Warning sign: Modbus read rate drops below 8 Hz when camera is enabled.

2. **Shared PyTorch/Ultralytics model instances across threads (Critical)** — Each detection pipeline instantiates its own model object inside its own thread's `run()` method. The broken and crack models run sequentially in a single detection thread. Warning sign: random `RuntimeError` during `.predict()` calls.

3. **torch.load() blocking asyncio at startup (Critical)** — Load all models inside `DetectionThread.run()`, not in `lifecycle._init_camera()`. Signal readiness via `asyncio.Event.set()` called with `call_soon_threadsafe`. Warning sign: startup takes 5+ seconds longer when camera is enabled.

4. **QLabel.setPixmap() called from camera thread (Critical)** — Camera page uses QTimer polling of `CameraResultsStore`, not direct calls from background threads. QTimer callbacks run in the Qt thread. Warning sign: segfaults when navigating to camera page.

5. **Unconditional camera module imports (Critical)** — Camera imports live inside `if camera_config.get('enabled', False):` guards in `lifecycle.py` and `main_controller.py`. Use `from __future__ import annotations` in camera module files to defer type annotation evaluation. Verify by running on a machine without OpenCV installed. Warning sign: `ModuleNotFoundError: No module named 'cv2'` at startup with camera disabled.

6. **BGR vs RGB color space corruption (Moderate)** — Define one canonical format (RGB) at the camera capture boundary. CameraService exposes `get_frame_rgb()` and `save_jpeg_bgr()` — convert once, never again downstream. Warning sign: orange/blue-tinted display or systematically low detection confidence.

See [PITFALLS.md](./PITFALLS.md) for full pitfall list including technical debt patterns, integration gotchas, performance traps, and a "looks done but isn't" checklist.

---

## Implications for Roadmap

Based on combined research, the dependency order from ARCHITECTURE.md directly maps to roadmap phase structure. Each phase is independently testable.

### Phase 1: Foundation — numpy Unblock + Config + DB Schema
**Rationale:** The numpy<2.0 cap blocks all new dependencies. Config schema and DB schema are additive-only with zero code risk. Nothing else can proceed until these exist. Do this first.
**Delivers:** Updated `requirements.txt` (numpy cap removed, 4 new libs added), `camera:` section in `config.yaml`, `SCHEMA_CAMERA_DB` in `schemas.py`, `camera.db` created conditionally in lifecycle
**Features from FEATURES.md:** `camera.enabled` config flag (entire feature gated on this)
**Avoids:** Pitfall 5 (unconditional import) — the `camera.enabled` flag is established here and gates everything downstream
**Research flag:** Standard patterns — no additional research needed

### Phase 2: CameraResultsStore + CameraService (Capture + Recording)
**Rationale:** All camera producers and consumers depend on CameraResultsStore. CameraService can be tested with real hardware before any AI models are involved. This is the infrastructure layer.
**Delivers:** `CameraResultsStore` (thread-safe singleton), `CameraService` (OpenCV capture + JPEG encoder threads), JPEG frame recording to `recordings/` directory
**Features from FEATURES.md:** OpenCV frame capture + JPEG recording, recordings directory structure
**Avoids:** Pitfall 1 (cap.read() in asyncio) — capture thread design established here; Pitfall 6 (BGR/RGB) — canonical frame format contract established in CameraService
**Architecture:** Pattern 1 (thread-safe results store) + Pattern 2 (background thread workers)
**Research flag:** Standard patterns — QThread worker with OpenCV is well-documented

### Phase 3: AI Detection Pipeline (RT-DETR + LDC + HealthCalculator)
**Rationale:** Depends on Phase 2 (needs frames). Models can be developed against test images. All three components (broken detect, crack detect, LDC wear) run in the same detection thread to avoid model sharing.
**Delivers:** `DetectionWorker` (broken + crack RT-DETR), `LDCWorker` (LDC edge detection + wear%), `HealthCalculator` (composite health score), results written to `CameraResultsStore` and `camera.db`
**Features from FEATURES.md:** RT-DETR broken tooth detection, RT-DETR crack detection, LDC wear pipeline, SawHealthCalculator
**Avoids:** Pitfall 2 (shared model instances) — models instantiated inside single detection thread; Pitfall 3 (torch.load() blocking startup) — models loaded in thread's run() method; Pitfall: torch.no_grad() missing — wrap all inference
**Architecture:** Pattern 2 (background thread workers); models owned by single thread
**Research flag:** Standard ML inference pattern — well-documented via Ultralytics thread-safe inference guide

### Phase 4: VisionService Orchestration + Lifecycle Integration
**Rationale:** VisionService wires Phase 3 workers with scheduling and the SQLiteService queue. Lifecycle integration connects everything to the application startup/shutdown sequence. These are tightly coupled — do together.
**Delivers:** `VisionService` (orchestrates detection + LDC scheduling), `lifecycle.py` `_init_camera()` step with lazy imports, camera stop in shutdown sequence before SQLite flush
**Features from FEATURES.md:** Detection results to SQLite (via queue pattern)
**Avoids:** Pitfall 3 (startup blocking) — `_init_camera()` only starts threads, models load in threads; integration gotcha: SQLite writes must go through queue, not direct sqlite3
**Architecture:** Pattern 4 (lifecycle integration conditional step)
**Research flag:** Standard patterns — follows existing MQTT service lifecycle pattern exactly

### Phase 5: Data Pipeline IoT Integration
**Rationale:** Optional attachment to the 10 Hz loop. Zero risk to existing functionality — `camera_results_store=None` is the default and all consumers are None-guarded.
**Delivers:** `DataProcessingPipeline` optional `camera_results_store` parameter, vision snapshot included in ThingsBoard telemetry at each 10 Hz cycle
**Features from FEATURES.md:** Detection results to ThingsBoard IoT
**Avoids:** Integration gotcha: IoT send must go through existing batching, not direct from detection thread
**Architecture:** Optional field attachment — no hot-path changes to existing 10 Hz loop
**Research flag:** Standard patterns — follows existing IoT telemetry pattern

### Phase 6: Camera GUI Page + Sidebar Integration
**Rationale:** GUI can now be built against the fully functional backend (Phases 1-5). CameraController only reads `CameraResultsStore` — it is decoupled from the camera hardware and models.
**Delivers:** `CameraController` Qt widget (live feed at 500ms, stats at 1000ms, health at 2000ms), sequential image thumbnails panel, detection status icons, wear visualization overlay, health color coding, 5th sidebar navigation button in MainController
**Features from FEATURES.md:** Camera GUI page, sidebar nav button, sequential thumbnails (P2), status icons (P2), wear vis overlay (P2)
**Avoids:** Pitfall 4 (setPixmap from wrong thread) — QTimers poll store in Qt thread, never call camera service directly; Pitfall: QLabel with QTimer not 0ms interval
**Architecture:** Pattern 3 (GUI polling via QTimers); CameraController receives only store
**Research flag:** Standard Qt patterns; sidebar button geometry is concrete (y=649 based on 121px spacing), verify no layout overlap

### Phase Ordering Rationale

- **Foundation first:** numpy cap removal is a hard blocker — no pip install succeeds until this is fixed. Config and DB schema are pure additions with no risk.
- **Infrastructure before workers:** CameraResultsStore must exist before any component writes to or reads from it. CameraService must exist before DetectionWorker needs frames.
- **Detection before lifecycle:** Workers are independently testable. Lifecycle integration only makes sense once the whole camera stack works.
- **Lifecycle before IoT:** IoT integration references `camera_results_store` which is created in `_init_camera()`.
- **Backend before GUI:** CameraController reads from CameraResultsStore; building the GUI last means it can be developed against real results from the real pipeline.
- **Separating GUI from lifecycle:** GUI integration (Phase 6) is separated from lifecycle integration (Phase 4) because GUI work can proceed in parallel once the store exists, and it carries the most layout/UX iteration risk.

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 3 (AI Detection):** LDC model integration requires vendoring source code (`modelB4.py`) from [xavysp/LDC](https://github.com/xavysp/LDC). The BIPED checkpoint path and LDC preprocessing pipeline need to be matched to the existing source project's implementation. Review `eskiimas/smart-saw/src/vision/wear_detection/` before implementation.
- **Phase 3 (AI Detection):** CPU-only PyTorch inference at 2 Hz on 1280x720 frames — validate on actual panel PC hardware before committing to this scheduling interval. RT-DETR at 2 Hz and LDC at 0.2 Hz are estimates; measure and adjust.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Foundation):** requirements.txt edits and additive YAML/schema changes — no research needed
- **Phase 2 (Capture):** OpenCV VideoCapture in a thread with queue — well-documented; existing source project has working implementation to reference
- **Phase 4 (Lifecycle):** Follows existing MQTT service pattern exactly — `_init_mqtt()` is the template
- **Phase 5 (IoT):** Adding optional fields to existing telemetry dict — trivial
- **Phase 6 (GUI):** CameraPage port from `eskiimas/smart-saw/src/gui/controllers/pyside_camera.py` — direct reference implementation exists

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All library versions verified on PyPI as of 2026-03-16; numpy 2.x transition issue confirmed via GitHub issues and PyPI metadata; only CPU-only inference performance is MEDIUM (measure on real hardware) |
| Features | HIGH | Direct source code analysis of working legacy system; all features are ports, not novel implementations; feature dependencies mapped with exact data formats (JSON schema, CSV format, directory structure) |
| Architecture | HIGH | Existing codebase patterns directly inspected (`lifecycle.py`, `mqtt_client.py`, `sqlite_service.py`); patterns verified against official Qt and Python docs; build order derived from strict dependency analysis |
| Pitfalls | HIGH | All six critical pitfalls verified against official documentation (OpenCV GitHub, Ultralytics docs, PyTorch issue tracker, Qt for Python docs); each pitfall has a confirmed prevention strategy |

**Overall confidence:** HIGH

### Gaps to Address

- **CPU inference timing:** RT-DETR and LDC inference times on the actual industrial panel PC CPU are not measured. The 2 Hz detection interval and 0.2 Hz LDC interval are conservative estimates. Validate during Phase 3 implementation and adjust `config.yaml` `interval_seconds` values accordingly.

- **LDC weights and source compatibility:** The LDC model source (`modelB4.py`) and BIPED weights must be confirmed against the version used in `eskiimas/smart-saw`. The LDC GitHub has multiple model variants. Match exactly to avoid behavioral differences in wear calculation.

- **Sidebar button geometry:** The 5th sidebar button is projected at y=649 based on the existing 121px spacing pattern. Verify against the actual `.ui` file or `main_controller.py` layout before implementing.

- **Wear baseline calibration:** The wear calculation requires a `baseline_edge_count` (edge pixel count on a new blade). This value is machine-specific and must be calibrated per installation. Document this as a required setup step, not a software default.

- **serit_id and makine_id at camera page:** The camera page needs `serit_id` (Modbus register 2230) and `makine_id` (register 2251) for linking detection results to blade sessions. These are already captured in the existing system. Confirm the data path from `raw_data` to `CameraResultsStore` or camera page constructor during Phase 4 implementation.

---

## Sources

### Primary (HIGH confidence)
- Direct code analysis: `/media/workspace/eskiimas/smart-saw/src/` — complete working camera implementation (camera.py, broken_detect.py, crack_detect.py, vision/service.py, saw_health_calculator.py, gui/controllers/pyside_camera.py)
- [ultralytics PyPI](https://pypi.org/project/ultralytics/) — v8.4.22, 2026-03-14
- [Ultralytics RT-DETR docs](https://docs.ultralytics.com/models/rtdetr/) + [predict docs](https://docs.ultralytics.com/modes/predict/)
- [Ultralytics Thread-Safe Inference Guide](https://docs.ultralytics.com/guides/yolo-thread-safe-inference/)
- [opencv-python PyPI](https://pypi.org/project/opencv-python/) — v4.13.0.92, 2026-02-05
- [PyTorch Versions wiki](https://github.com/pytorch/pytorch/wiki/PyTorch-Versions) — official compatibility table
- [torch PyPI](https://pypi.org/project/torch/) — v2.10.0, 2026-01-21
- [kornia PyPI](https://pypi.org/project/kornia/) — v0.8.2, 2025-11-08
- [LDC GitHub xavysp/LDC](https://github.com/xavysp/LDC) — ~0.7M params, PyTorch >=1.6
- [Qt for Python QThread docs](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html)
- [PySide6 QImage docs](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html)
- Existing codebase: `src/core/lifecycle.py`, `src/services/iot/mqtt_client.py`, `src/services/database/sqlite_service.py`

### Secondary (MEDIUM confidence)
- [pytorch/pytorch Issue #5879: torch.load blocks asyncio](https://github.com/pytorch/pytorch/issues/5879)
- [opencv/opencv Issue #24229: VideoCapture thread safety](https://github.com/opencv/opencv/issues/24229)
- [numpy 2.x ecosystem tracking](https://github.com/numpy/numpy/issues/26191)
- [How to display OpenCV video in PyQt apps (gist)](https://gist.github.com/docPhil99/ca4da12c9d6f29b9cea137b617c7b8b1)
- [PyTorch CUDA semantics docs](https://docs.pytorch.org/docs/stable/notes/cuda.html)

---
*Research completed: 2026-03-16*
*Ready for roadmap: yes*

# Architecture Research: Camera Vision & AI Detection Integration

**Domain:** Industrial IoT + Computer Vision + Embedded Qt Desktop
**Researched:** 2026-03-16
**Confidence:** HIGH
**Milestone:** v2.0 — Camera Vision & AI Detection

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            GUI Thread (Qt Event Loop)                        │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ControlPanel  │  │  Positioning   │  │    Sensor    │  │  CameraPage   │  │
│  │ Controller   │  │  Controller    │  │  Controller  │  │  Controller   │  │
│  └──────────────┘  └────────────────┘  └──────────────┘  └───────┬───────┘  │
│                                                                   │ QTimers  │
├───────────────────────────────────────────────────────────────────┼──────────┤
│                       asyncio Event Loop (Main Thread)            │          │
│  ┌────────────────────────────────────────────────────────────┐   │          │
│  │                  DataProcessingPipeline (10 Hz)             │   │          │
│  │  read → process → control → write → save → IoT             │   │          │
│  └────────────────────────────────────────────────────────────┘   │          │
│                                                                    │          │
│  ┌───────────────────────────┐  ┌─────────────────────────────┐   │          │
│  │    CameraService          │  │   VisionService              │   │          │
│  │  (background threads)     │  │  (background threads)        │   │          │
│  │  ┌──────────────────┐     │  │  ┌──────────────────────┐   │   │          │
│  │  │ CaptureThread    │     │  │  │ DetectionWorker      │   │   │          │
│  │  │ (OpenCV, ~30fps) │     │  │  │ (RT-DETR models)     │   │   │          │
│  │  └──────────────────┘     │  │  └──────────────────────┘   │   │          │
│  │  ┌──────────────────┐     │  │  ┌──────────────────────┐   │   │          │
│  │  │ EncoderThreads   │     │  │  │ LDCWorker (wear)     │   │   │          │
│  │  │ (JPEG to disk)   │     │  │  └──────────────────────┘   │   │          │
│  │  └──────────────────┘     │  └─────────────────────────────┘   │          │
│  └───────────────────────────┘                                     │          │
│                                                                    │          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐   │          │
│  │ModbusReader  │  │ControlManager│  │CameraResultsStore      │◄──┘          │
│  │ModbusWriter  │  │ControlManager│  │(thread-safe singleton) │              │
│  └──────────────┘  └──────────────┘  └────────────────────────┘              │
├─────────────────────────────────────────────────────────────────────────────┤
│                            Storage Layer                                      │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐  │
│  │  raw.db   │  │ total.db  │  │   ml.db   │  │anomaly.db │  │camera.db │  │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Location |
|-----------|----------------|----------|
| `ApplicationLifecycle` | Startup/shutdown orchestration; conditionally initializes CameraService | `src/core/lifecycle.py` — MODIFIED |
| `CameraService` | OpenCV frame capture, JPEG encoding to disk; thread-safe singleton; lazy-loaded | `src/services/camera/camera_service.py` — NEW |
| `VisionService` | Schedules detection workers; coordinates RT-DETR and LDC results | `src/services/camera/vision_service.py` — NEW |
| `DetectionWorker` | Runs RT-DETR inference (broken + crack) on JPEG frames | `src/services/camera/detection_worker.py` — NEW |
| `LDCWorker` | LDC edge detection pipeline; computes wear percentage | `src/services/camera/ldc_worker.py` — NEW |
| `HealthCalculator` | Combines broken% (70%) + wear% (30%) into saw health score | `src/services/camera/health_calculator.py` — NEW |
| `CameraResultsStore` | Thread-safe in-memory store: latest frame, detection results, wear %, health | `src/services/camera/results_store.py` — NEW |
| `CameraPage` | Qt widget; QTimers poll CameraResultsStore; renders live frame + stats | `src/gui/controllers/camera_controller.py` — NEW |
| `MainController` | Adds 5th nav button + page; conditionally shows camera nav button | `src/gui/controllers/main_controller.py` — MODIFIED |
| `DataProcessingPipeline` | Optionally pulls latest vision results to include in IoT telemetry | `src/services/processing/data_processor.py` — MODIFIED |
| `schemas.py` | Adds `camera.db` schema for detection event history | `src/services/database/schemas.py` — MODIFIED |
| `config.yaml` | Adds `camera:` section with enabled flag, device, paths, model paths | `config/config.yaml` — MODIFIED |

---

## Config-Driven Modularity: The Core Constraint

The single most important architectural constraint: `camera.enabled: false` must mean **zero camera code is imported or executed**. This prevents import errors on machines without camera hardware, without OpenCV, or without model files.

### Implementation Pattern: Lazy Import Guard

```python
# In ApplicationLifecycle.start()
async def _init_camera(self):
    camera_config = self.config.get('camera', {})
    if not camera_config.get('enabled', False):
        logger.info("Camera disabled in config — skipping")
        return   # No further imports, no imports triggered

    # Lazy import: only executed when camera.enabled=true
    from ..services.camera.camera_service import CameraService
    from ..services.camera.vision_service import VisionService

    self.camera_service = CameraService(camera_config)
    self.vision_service = VisionService(camera_config, self.camera_service)
    await self.camera_service.start()
    await self.vision_service.start()
```

```python
# In MainController._setup_ui()
camera_config = self.config.get('camera', {}) if self.config else {}
if camera_config.get('enabled', False):
    from .camera_controller import CameraController   # Lazy import
    self.camera_page = CameraController(
        self.camera_results_store,  # Passed via constructor
        parent=self.stackedWidget
    )
    self.stackedWidget.addWidget(self.camera_page)
    self._add_camera_nav_button()   # Add 5th sidebar button
```

This pattern ensures `import cv2`, `import torch`, `from ultralytics import RTDETR` are never executed unless `camera.enabled: true`.

### What "camera.enabled=false" Must Guarantee

- `import cv2` never runs
- `import torch` / `from ultralytics import RTDETR` never run
- `camera_controller.py` module never imported
- No camera database created
- No camera-related QTimers created
- GUI sidebar shows 4 buttons (unchanged)

---

## Recommended Project Structure

```
src/
├── services/
│   ├── camera/                   # NEW — entire module conditionally loaded
│   │   ├── __init__.py
│   │   ├── camera_service.py     # OpenCV capture thread + JPEG encoder threads
│   │   ├── vision_service.py     # Orchestrates detection + LDC workers
│   │   ├── detection_worker.py   # RT-DETR inference (broken + crack)
│   │   ├── ldc_worker.py         # LDC edge detection + wear calculation
│   │   ├── health_calculator.py  # Health score: broken*0.7 + wear*0.3
│   │   └── results_store.py      # Thread-safe singleton for latest results
│   ├── database/
│   │   └── schemas.py            # MODIFIED: add SCHEMA_CAMERA_DB
│   ├── processing/
│   │   └── data_processor.py     # MODIFIED: optionally attach vision results to IoT
│   └── iot/
│       └── (unchanged)
├── gui/
│   └── controllers/
│       ├── main_controller.py    # MODIFIED: conditional 5th page + nav button
│       └── camera_controller.py  # NEW — CameraPage Qt widget
├── core/
│   └── lifecycle.py              # MODIFIED: _init_camera() step
└── ml/
    └── (unchanged — existing models for Modbus-based detection)

config/
└── config.yaml                   # MODIFIED: camera: section added

data/
└── models/
    ├── Bagging_dataset_v17_20250509.pkl  # existing
    ├── best.pt                           # NEW: RT-DETR broken tooth model
    └── catlak-best.pt                    # NEW: RT-DETR crack model
```

### Structure Rationale

- **`services/camera/`:** Self-contained module. Everything camera lives here. If `camera.enabled=false`, this entire directory is never imported. Keeps camera concerns out of core pipeline.
- **`results_store.py`:** Decouples producer (camera threads) from consumers (GUI, IoT pipeline). Thread-safe read from any context without blocking.
- **`camera_controller.py`:** Separate from other controllers so it can be entirely skipped. Does not receive `data_pipeline` — it only reads `CameraResultsStore`.
- **No modification to `DataProcessingPipeline` hot path:** Vision results are appended as an optional field; the 10 Hz loop does not block on camera.

---

## Architectural Patterns

### Pattern 1: Thread-Safe Results Store (Read-Many, Write-Few)

**What:** A singleton dict protected by `threading.Lock()`, written by background camera/vision threads, read by GUI QTimers and optionally the data pipeline.

**When to use:** Multiple producers (detection, LDC, capture) write infrequently; multiple consumers (GUI timers, IoT) read frequently.

**Trade-offs:** Simple, low-latency reads. Lock contention is negligible because writes are rare (detection runs at 0.5–2 Hz, reads at 2–5 Hz).

```python
class CameraResultsStore:
    """Thread-safe store for latest camera/vision results."""
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._results = {
            'latest_frame': None,          # bytes (JPEG)
            'broken_detected': False,
            'crack_detected': False,
            'broken_confidence': 0.0,
            'crack_confidence': 0.0,
            'wear_percentage': 0.0,
            'health_score': 100.0,
            'last_detection_ts': None,
            'last_wear_ts': None,
        }

    def update(self, key: str, value) -> None:
        with self._lock:
            self._results[key] = value

    def update_batch(self, updates: dict) -> None:
        with self._lock:
            self._results.update(updates)

    def get(self, key: str, default=None):
        with self._lock:
            return self._results.get(key, default)

    def snapshot(self) -> dict:
        """Return complete copy for GUI rendering."""
        with self._lock:
            return dict(self._results)
```

### Pattern 2: Background Thread Workers (Camera & Vision)

**What:** Long-running threads for capture and inference, controlled by `threading.Event` for stop signaling.

**When to use:** CPU/GPU-bound work (OpenCV capture, model inference) that must not block the asyncio event loop.

**Trade-offs:** Threads are appropriate here because cv2/torch are not async-compatible. The main asyncio loop is never involved — camera is truly parallel.

```python
class CameraService:
    def __init__(self, config: dict):
        self._stop_event = threading.Event()
        self._capture_thread = None
        self._frame_queue = queue.Queue(maxsize=5)  # Drop old frames

    async def start(self):
        """Called from asyncio context but spawns threads."""
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name="Camera-Capture"
        )
        self._capture_thread.start()

    async def stop(self):
        self._stop_event.set()
        if self._capture_thread:
            self._capture_thread.join(timeout=5.0)

    def _capture_loop(self):
        cap = cv2.VideoCapture(self._device_id)
        while not self._stop_event.is_set():
            ret, frame = cap.read()
            if ret:
                try:
                    self._frame_queue.put_nowait(frame)
                except queue.Full:
                    pass  # Drop oldest frame — real-time preferred over buffering
        cap.release()
```

### Pattern 3: GUI Polling via QTimers (Camera Page)

**What:** CameraPage does not subscribe to events from background threads. Instead, it uses QTimers at different intervals to poll CameraResultsStore.

**When to use:** Qt UI updates must happen in the Qt thread. QTimers are the correct mechanism. Polling at different rates for different data types prevents over-rendering.

**Trade-offs:** Slight latency (up to one timer interval) before display updates. Acceptable for camera health display. Live frame can be polled at 500ms (2 Hz) — plenty for a health monitor, not a video stream.

```python
class CameraController(QWidget):
    def __init__(self, results_store: CameraResultsStore, parent=None):
        super().__init__(parent)
        self.results_store = results_store

        # Different update rates for different data
        self._frame_timer = QTimer(self)
        self._frame_timer.timeout.connect(self._update_frame)
        self._frame_timer.start(500)      # 2 Hz — live frame preview

        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._update_stats)
        self._stats_timer.start(1000)     # 1 Hz — detection results, wear %

        self._health_timer = QTimer(self)
        self._health_timer.timeout.connect(self._update_health)
        self._health_timer.start(2000)    # 0.5 Hz — health score, history

    def stop_timers(self):
        """Called from MainController.closeEvent()."""
        self._frame_timer.stop()
        self._stats_timer.stop()
        self._health_timer.stop()
```

### Pattern 4: Lifecycle Integration (Conditional Step)

**What:** `ApplicationLifecycle.start()` gains a `_init_camera()` step inserted after `_init_mqtt()` and before `_init_data_pipeline()`. The camera service must exist before the pipeline so the pipeline can optionally reference `CameraResultsStore`.

**When to use:** Any optional subsystem that requires startup/shutdown lifecycle hooks.

```python
# In ApplicationLifecycle.start()
# 4. Initialize MQTT (optional)
await self._init_mqtt()

# 4.5 Initialize camera (optional, config-driven)
await self._init_camera()     # NEW STEP

# 5. Initialize data pipeline
await self._init_data_pipeline()
```

---

## Data Flow

### Camera Data Flow (Independent from 10 Hz Loop)

```
OpenCV device
    ↓ (~30 fps)
CaptureThread
    ↓ (queue.put_nowait — drops if full)
_frame_queue
    ↓
EncoderThread (JPEG)
    ├─→ JPEG bytes to disk (recordings/)
    └─→ CameraResultsStore.update('latest_frame', jpeg_bytes)

DetectionWorker (triggered every N frames or on schedule)
    ← reads JPEG from disk or frame_queue
    ↓ RT-DETR inference (best.pt + catlak-best.pt)
    └─→ CameraResultsStore.update_batch({
            'broken_detected': True/False,
            'crack_detected': True/False,
            'broken_confidence': 0.87,
            'crack_confidence': 0.0,
            'last_detection_ts': datetime.now()
        })

LDCWorker (triggered on schedule, e.g. every 5s)
    ← reads frame from CameraResultsStore or disk
    ↓ LDC edge detection → wear calculation
    └─→ CameraResultsStore.update_batch({
            'wear_percentage': 23.5,
            'last_wear_ts': datetime.now()
        })

HealthCalculator (triggered after detection or wear update)
    ← reads broken_detected + wear_percentage from store
    ↓ health = (1 - broken_weight) * 100 if not broken else 0
       combined with wear weighting
    └─→ CameraResultsStore.update('health_score', 76.5)
```

### GUI Camera Page Data Flow

```
QTimer (500ms) → CameraResultsStore.get('latest_frame')
    → QLabel.setPixmap(QPixmap.fromImage(...))

QTimer (1000ms) → CameraResultsStore.snapshot()
    → Update detection labels (broken/crack status + confidence)
    → Update wear % label

QTimer (2000ms) → CameraResultsStore.get('health_score')
    → Update health indicator widget
    → (Optionally) read history from camera.db for trend graph
```

### IoT Integration Data Flow

```
DataProcessingPipeline._processing_loop() (10 Hz)
    ↓ (Step 6 — queue IoT)
    if self.camera_results_store:
        vision_snapshot = self.camera_results_store.snapshot()
        # Merge into ProcessedData or attach as extra fields
    await self.iot_service.queue_telemetry(processed_data, vision_data)
```

### DB Write Flow (Camera Events)

```
DetectionWorker (on positive detection)
    → SQLiteService('camera').write_async(
        INSERT INTO detection_events (timestamp, event_type, confidence, ...)
    )

LDCWorker (on wear update)
    → SQLiteService('camera').write_async(
        INSERT INTO wear_events (timestamp, wear_percentage, ...)
    )
```

---

## Integration Points: New vs Modified

### New Components (no existing code touched)

| Component | File | Notes |
|-----------|------|-------|
| CameraService | `src/services/camera/camera_service.py` | OpenCV threads, JPEG encoding |
| VisionService | `src/services/camera/vision_service.py` | Orchestrates workers |
| DetectionWorker | `src/services/camera/detection_worker.py` | RT-DETR models |
| LDCWorker | `src/services/camera/ldc_worker.py` | Wear detection |
| HealthCalculator | `src/services/camera/health_calculator.py` | Health score |
| CameraResultsStore | `src/services/camera/results_store.py` | Thread-safe store |
| CameraController | `src/gui/controllers/camera_controller.py` | Qt camera page |

### Modified Components (minimal, surgical changes)

| Component | File | What Changes |
|-----------|------|-------------|
| ApplicationLifecycle | `src/core/lifecycle.py` | Add `_init_camera()` step; add `camera_service`, `vision_service` attributes; add camera to stop sequence |
| MainController | `src/gui/controllers/main_controller.py` | Conditional 5th nav button + page; pass `results_store` to CameraController; add camera page to `stop_timers()` |
| DataProcessingPipeline | `src/services/processing/data_processor.py` | Optional `camera_results_store` parameter (defaults None); if present, attach vision snapshot to IoT telemetry — no hot-path changes |
| schemas.py | `src/services/database/schemas.py` | Add `SCHEMA_CAMERA_DB` constant; add `'camera'` key to `SCHEMAS` dict |
| config.yaml | `config/config.yaml` | Add `camera:` section at end |

### Integration Boundary: CameraResultsStore

`CameraResultsStore` is the sole integration boundary between the camera subsystem and everything else. Neither `DataProcessingPipeline` nor `CameraController` import from `services/camera/` modules directly — they only hold a reference to the store. This means:

- If camera is disabled: `CameraResultsStore` is never instantiated, both consumers receive `None` and skip gracefully.
- If camera crashes: Store holds stale data; consumers continue without blocking.
- Adding future camera features: only `CameraResultsStore` interface needs to expand, not all consumers.

---

## Build Order

Dependency analysis drives this order. Each step is independently testable.

### Step 1: Config Schema + Database Schema

**Files:** `config/config.yaml`, `src/services/database/schemas.py`

**Why first:** Everything else depends on config structure and DB schema. Zero code risk — only additive.

```yaml
# config.yaml addition
camera:
  enabled: false          # Default off — safe on machines without camera
  device_id: 0            # OpenCV device index
  fps: 30
  resolution: [1280, 720]
  jpeg_quality: 85
  recordings_path: "data/recordings"

  detection:
    enabled: true
    broken_model_path: "data/models/best.pt"
    crack_model_path: "data/models/catlak-best.pt"
    interval_seconds: 2.0   # Run detection every 2 seconds
    confidence_threshold: 0.5

  wear:
    enabled: true
    interval_seconds: 5.0

  health:
    broken_weight: 0.70
    wear_weight: 0.30
```

```python
# schemas.py addition
SCHEMA_CAMERA_DB = """
CREATE TABLE IF NOT EXISTS detection_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- 'broken_tooth', 'crack', 'wear_update'
    confidence REAL,
    wear_percentage REAL,
    health_score REAL,
    kesim_id INTEGER,          -- Link to active cutting session
    image_path TEXT            -- Path to JPEG that triggered detection
);
CREATE INDEX IF NOT EXISTS idx_detection_ts ON detection_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_detection_type ON detection_events(event_type);
CREATE INDEX IF NOT EXISTS idx_detection_kesim ON detection_events(kesim_id);

CREATE TABLE IF NOT EXISTS wear_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    wear_percentage REAL,
    health_score REAL
);
CREATE INDEX IF NOT EXISTS idx_wear_ts ON wear_history(timestamp);
"""
```

### Step 2: CameraResultsStore

**Files:** `src/services/camera/__init__.py`, `src/services/camera/results_store.py`

**Why second:** All other camera components and both consumers depend on this. Pure Python, no external deps, fully testable in isolation.

**Test criteria:** Unit test that two threads write concurrently while one thread reads — no deadlock, reads return consistent snapshots.

### Step 3: CameraService (Capture + Encoding)

**Files:** `src/services/camera/camera_service.py`

**Dependencies:** Step 2 (results_store), `cv2`, `config.yaml`

**Why third:** Vision workers need frames from this service. Camera hardware can be tested independently before models are involved.

**Test criteria:** Start service, verify frames appear in results_store within 2 seconds. Test `stop()` cleans up threads.

### Step 4: DetectionWorker + LDCWorker + HealthCalculator

**Files:** `src/services/camera/detection_worker.py`, `src/services/camera/ldc_worker.py`, `src/services/camera/health_calculator.py`

**Dependencies:** Step 3, model files (best.pt, catlak-best.pt)

**Why fourth:** Pure processing — can be developed/tested with test images before full integration.

**Test criteria:** Feed a test JPEG, verify detection results appear in results_store. Verify health_score updates after detection.

### Step 5: VisionService (Orchestration)

**Files:** `src/services/camera/vision_service.py`

**Dependencies:** Steps 3 and 4

**Why fifth:** Wires the workers together with scheduling. Verifiable once workers exist.

**Test criteria:** Start full camera stack (service + vision), verify detection_events write to camera.db.

### Step 6: Lifecycle Integration

**Files:** `src/core/lifecycle.py`

**Dependencies:** Step 5

**Why sixth:** Lifecycle wires everything into the startup sequence. At this point the camera subsystem is complete and tested in isolation.

**Changes:**
```python
# Add attribute declarations in __init__
self.camera_service: Optional['CameraService'] = None
self.vision_service: Optional['VisionService'] = None
self.camera_results_store: Optional['CameraResultsStore'] = None

# Add _init_camera() method with lazy imports
async def _init_camera(self):
    camera_config = self.config.get('camera', {})
    if not camera_config.get('enabled', False):
        logger.info("Camera disabled — skipping")
        return
    from ..services.camera.results_store import CameraResultsStore
    from ..services.camera.camera_service import CameraService
    from ..services.camera.vision_service import VisionService
    self.camera_results_store = CameraResultsStore()
    self.camera_service = CameraService(camera_config, self.camera_results_store)
    self.vision_service = VisionService(camera_config, self.camera_results_store,
                                        self.db_services.get('camera'))
    await self.camera_service.start()
    await self.vision_service.start()

# Add to stop() sequence (before data pipeline stop)
if self.vision_service:
    await self.vision_service.stop()
if self.camera_service:
    await self.camera_service.stop()
```

### Step 7: Data Pipeline IoT Integration

**Files:** `src/services/processing/data_processor.py`

**Dependencies:** Step 2

**Why seventh:** Pipeline integration is optional and low-risk. The pipeline simply checks if `camera_results_store` is not None.

**Changes:**
```python
# Constructor — add optional parameter (defaults None, backward-compatible)
def __init__(self, config, modbus_reader, modbus_writer,
             control_manager, db_services, mqtt_service=None,
             camera_results_store=None):   # NEW — optional
    ...
    self.camera_results_store = camera_results_store

# In _processing_loop(), in IoT step
if self.iot_service:
    vision_data = (self.camera_results_store.snapshot()
                   if self.camera_results_store else None)
    await self.iot_service.queue_telemetry(processed_data, vision_data)
```

### Step 8: GUI CameraController

**Files:** `src/gui/controllers/camera_controller.py`

**Dependencies:** Step 2 (results_store)

**Why eighth:** UI can now be built against the real results_store. All backend is ready.

**Key constraints:**
- Receives `CameraResultsStore` by constructor injection — never imports `CameraService` or `VisionService`
- Uses `QLabel` with `setPixmap()` for frame display (QPixmap.fromImage from JPEG bytes)
- QTimers: 500ms frame, 1000ms stats, 2000ms health
- `stop_timers()` method required (called from `MainController.closeEvent()`)

### Step 9: MainController Integration

**Files:** `src/gui/controllers/main_controller.py`

**Dependencies:** Step 8

**Why last:** MainController wiring is the final assembly step. Risk is purely in layout changes (sidebar button geometry).

**Changes:**
```python
def _setup_ui(self):
    # ... existing 4 pages ...
    self.nav_buttons = [
        self.btnControlPanel,
        self.btnPositioning,
        self.btnSensor,
        self.btnTracking
    ]

    # NEW: Conditionally add camera page
    self.camera_page = None
    camera_config = getattr(self, 'config', {}).get('camera', {})
    if camera_config.get('enabled', False) and self.camera_results_store:
        from .camera_controller import CameraController
        self.camera_page = CameraController(
            self.camera_results_store,
            parent=self.stackedWidget
        )
        self.stackedWidget.addWidget(self.camera_page)   # Index 4
        self._add_camera_nav_button()

def closeEvent(self, event):
    # ... existing timer stops ...
    if self.camera_page and hasattr(self.camera_page, 'stop_timers'):
        self.camera_page.stop_timers()
    event.accept()
```

**Sidebar button geometry:** Current buttons are at y=165, 286, 407, 528 (spacing 121px). Camera button at y=649. Verify this does not overlap with any existing element.

---

## Scaling Considerations

This is a single-machine embedded system, not a multi-user web service. "Scaling" here means resource management on the industrial panel PC.

| Concern | Current | With Camera Added | Mitigation |
|---------|---------|-------------------|------------|
| CPU load | Low (10 Hz async) | +1 capture thread, +1-2 detection threads | Detection runs on schedule (2s interval), not every frame |
| Memory | Modest (~200 MB) | +JPEG buffer (~2 MB), +model weights (RT-DETR ~60 MB each) | Models loaded once; JPEG queue bounded (maxsize=5) |
| Disk (recordings) | N/A | ~1 MB/min at 85% JPEG quality, 30fps | Implement rotation/cleanup; configurable recording policy |
| asyncio loop | 10 Hz, <5ms/cycle | Unchanged — camera runs in separate threads | No camera code in asyncio hot path |
| Qt thread | 5 Hz GUI update | +3 QTimers at 0.5-2 Hz | These are lightweight polls — negligible |

---

## Anti-Patterns

### Anti-Pattern 1: Importing Camera Modules at Module Level

**What people do:**
```python
# In lifecycle.py (top of file)
from ..services.camera.camera_service import CameraService  # BAD
```

**Why it's wrong:** Even if camera is disabled in config, Python imports the module and all its transitive dependencies (`import cv2`, `import torch`). On machines without these packages, the application crashes at startup with `ModuleNotFoundError`.

**Do this instead:** Lazy import inside the guard:
```python
async def _init_camera(self):
    if not self.config.get('camera', {}).get('enabled', False):
        return
    from ..services.camera.camera_service import CameraService  # GOOD
```

### Anti-Pattern 2: Running Detection in the asyncio Loop

**What people do:**
```python
# In DataProcessingPipeline._processing_loop()
raw_data = await modbus_reader.read_all_sensors()
result = await run_rtdetr_inference(frame)   # BAD — blocks for 200-500ms
```

**Why it's wrong:** RT-DETR inference takes 200–500ms on CPU (even longer). Blocking the asyncio loop drops it below the 10 Hz target, causing Modbus read failures and control loop degradation.

**Do this instead:** Detection runs in a dedicated thread via `ThreadPoolExecutor` or a daemon thread. Results are placed in `CameraResultsStore`. The asyncio loop only reads the store (microseconds).

### Anti-Pattern 3: Blocking QTimer Callbacks with Inference

**What people do:**
```python
def _update_frame(self):
    frame = self.camera_service.capture()    # BAD — could block
    result = self.model.predict(frame)       # BAD — 200ms blocks Qt
    self.label.setPixmap(...)
```

**Why it's wrong:** QTimer callbacks run in the Qt thread. Any blocking call freezes the entire GUI.

**Do this instead:** QTimer callbacks only read from `CameraResultsStore` — they never call blocking operations:
```python
def _update_frame(self):
    jpeg = self.results_store.get('latest_frame')   # GOOD — microsecond lock
    if jpeg:
        self.label.setPixmap(self._jpeg_to_pixmap(jpeg))
```

### Anti-Pattern 4: Tight Coupling Between CameraController and CameraService

**What people do:**
```python
class CameraController(QWidget):
    def __init__(self, camera_service, vision_service, ...):
        self.camera_service = camera_service  # BAD — knows too much
        self.vision_service = vision_service
```

**Why it's wrong:** Camera controller becomes unable to be instantiated (or tested) without real camera hardware and loaded models.

**Do this instead:** CameraController only receives `CameraResultsStore`. It cannot restart capture, trigger detection, or control the camera — it only reads results:
```python
class CameraController(QWidget):
    def __init__(self, results_store: CameraResultsStore, parent=None):
        self.results_store = results_store   # GOOD — single dependency
```

### Anti-Pattern 5: Creating camera.db When Camera is Disabled

**What people do:**
```python
# In _init_databases() — always
for db_name in ['raw', 'total', 'log', 'ml', 'anomaly', 'camera']:
    service = SQLiteService(db_file, SCHEMAS[db_name])
```

**Why it's wrong:** Creates an empty database file even when camera is disabled. Wastes inodes, confuses operators inspecting the data directory.

**Do this instead:** Add `'camera'` to db_services only inside `_init_camera()`:
```python
async def _init_camera(self):
    if not camera_config.get('enabled', False):
        return
    # Create camera.db only when enabled
    camera_db = SQLiteService(db_path / 'camera.db', SCHEMA_CAMERA_DB)
    camera_db.start()
    self.db_services['camera'] = camera_db
```

---

## Integration Points Summary

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenCV (cv2) | Capture thread calls `cv2.VideoCapture()` | Lazy-imported; fails gracefully if not installed when camera disabled |
| Ultralytics / RT-DETR | `model = RTDETR('best.pt')` in `DetectionWorker.__init__()` | Models loaded once on startup; CUDA/CPU auto-detected |
| ThingsBoard IoT | `vision_data` dict passed alongside `processed_data` to `queue_telemetry()` | Optional field — IoT service skips if `None` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CameraService → CameraResultsStore | `results_store.update('latest_frame', jpeg)` | Lock-protected write; non-blocking |
| DetectionWorker → CameraResultsStore | `results_store.update_batch({...})` | Batch write for atomicity |
| CameraController → CameraResultsStore | `results_store.snapshot()` in QTimer callback | Read-only; millisecond-range lock |
| DataProcessingPipeline → CameraResultsStore | `results_store.snapshot()` once per 10 Hz cycle | Optional; None-guarded |
| VisionService → SQLiteService('camera') | `db.write_async(sql, params)` | Same non-blocking write pattern as all other DBs |
| ApplicationLifecycle → CameraService/VisionService | `await service.start()` / `await service.stop()` | Async interface matches existing service pattern |
| MainController → CameraResultsStore | Constructor injection via lifecycle | store passed: `lifecycle.camera_results_store` |

---

## Sources

- Existing codebase: `src/core/lifecycle.py`, `src/gui/app.py`, `src/gui/controllers/main_controller.py`, `src/services/processing/data_processor.py` — direct inspection, HIGH confidence
- Existing patterns: `src/services/iot/mqtt_client.py` (optional service pattern), `src/services/database/sqlite_service.py` (queue-based async writes) — HIGH confidence
- Project requirements: `.planning/PROJECT.md` — config-driven modularity constraint, camera feature list — HIGH confidence
- Thread safety pattern: Python `threading.Lock()` + `dict.update()` — established pattern from v1.3 AnomalyManager refactor — HIGH confidence
- OpenCV thread safety: OpenCV VideoCapture is not thread-safe for the capture object itself; single capture thread is the correct pattern — MEDIUM confidence (community consensus, aligns with old project design described in milestone_context)
- RT-DETR/Ultralytics: Model inference is not thread-safe with shared model objects; separate worker per model or sequential inference in single thread — MEDIUM confidence (standard ML serving pattern)

---

*Architecture research for: Smart Saw v2.0 Camera Vision & AI Detection Integration*
*Researched: 2026-03-16*

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

# Feature Research

**Domain:** Industrial camera-based band saw tooth inspection system
**Researched:** 2026-03-16
**Confidence:** HIGH (based on direct analysis of existing working implementation in source project + domain analysis)

---

## Context: Source System Already Exists

This is not a greenfield feature set. The old project (`/media/workspace/eskiimas/smart-saw/`) has a
complete, working camera vision system. The migration task is: port, modularize, and config-drive it
into the current codebase. Feature research here identifies what is table stakes (must port), what is
a differentiator (adds value beyond the port), and what to skip.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features the industrial operator expects once "camera vision" is announced. Missing any of these
makes the feature feel broken or incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Live camera feed in GUI | Camera page without live video is broken by definition | MEDIUM | QLabel + QTimer at 500ms; CameraModule captures continuously in background thread; frame shown via QImage/QPixmap conversion |
| Broken tooth detection (count + frames) | Core safety requirement — broken teeth damage workpiece and machine | HIGH | RT-DETR model (best.pt), runs post-recording on full frame set; outputs tooth count, broken count, annotated frames saved to detected/ folder |
| Crack detection (count + frames) | Structural failure of blade body, distinct from tooth breakage | HIGH | Separate RT-DETR model (catlak-best.pt), runs independently; outputs crack count, annotated frames to detected-crack/ folder |
| Wear percentage display | Blade wear is a continuous degradation metric; maintenance scheduling depends on it | HIGH | LDC edge detection pipeline (3-thread: watcher, ldc_worker, wear_worker); outputs wear % per frame to wear.csv; UI reads CSV average |
| Saw health composite score | Operators need single "is the blade OK?" number; separate stats are too cognitive | MEDIUM | Formula: health = 100 - (broken_pct * 0.7 + wear_pct * 0.3); status text (Saglikli/Iyi/Orta/Kritik/Tehlikeli) |
| Detection results to database | All vision results must persist — same as all other sensor data in this system | MEDIUM | New SQLite table (or camera.db) for detection_events; serit_id, timestamp, broken_count, crack_count, wear_percent, health_score |
| Detection results to ThingsBoard IoT | Existing telemetry pipeline expects all operational data | MEDIUM | Add camera telemetry fields to existing http_client send cycle |
| Camera page navigation button in sidebar | All existing pages (Control, Positioning, Sensor, Monitoring) have sidebar nav; camera page must too | LOW | Add btnCamera to existing sidebar widget; wire to camera page |
| config-driven enable/disable | System must run without camera hardware (factory floor may not have camera on all machines) | MEDIUM | `camera.enabled: false` in config.yaml suppresses all imports/threads; zero overhead when disabled |

### Differentiators (Competitive Advantage)

Features that go beyond a direct port and increase the system's value. None of these are in the old
project as-is.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Sequential image thumbnails panel (4 frames) | Operator can quickly scan recent blade images without opening file explorer | MEDIUM | Already present in old CameraPage (_siralı_goruntu_labels, _max_images=4, 240x150px each); worth porting as it directly answers "what did the blade look like?" |
| Detection status OK/alert icons per category | Single-glance status for each defect type; more scannable than numbers alone | LOW | Old code uses okey icon per detection type; simple QLabel icon swap based on count threshold |
| Real-time stats progress during batch detection | Detection over 500+ frames takes minutes; progress feedback prevents operator from thinking system hung | MEDIUM | The old detect_broken_objects() updates detection_stats.json per frame; GUI timer polls JSON to show live progress |
| Wear visualization overlay (red boundary lines) | Makes the algorithm's measurement visible; builds operator trust in automation | MEDIUM | Wear worker saves wear_vis/ images with OpenCV drawn reference lines and measured boundary; GUI can show latest vis image |
| Health status color coding | Immediate red/yellow/green comprehension; no number reading needed | LOW | SawHealthCalculator.get_health_color() already implemented; apply as label background or icon |
| Per-recording history in sidebar | Show previous session detection summaries; helps maintenance scheduling | HIGH | Not in old project; requires UI redesign; defer unless explicitly requested |
| Serit_id correlation on camera results | Link blade identity to visual inspection results; enables per-blade wear tracking across sessions | LOW | Just pass serit_id from existing system context when recording detection results |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time AI inference during recording | "Why not detect while recording?" — seems faster | At 50fps/1920x1200, RT-DETR inference per frame requires a powerful GPU; on typical industrial PC (CPU-only or basic GPU), inference at full frame rate would drop to <1fps and block recording; recording quality degrades | Record first, then batch-process; keeps recording pipeline clean and inference pipeline independent |
| Live wear percentage during recording | "Show wear while recording is happening" | LDC pipeline already runs concurrently with recording via VisionService watchdog — but this is complex async I/O; introducing it creates watchdog latency, queue overflow risk | LDC pipeline runs concurrently post-frame-write already (VisionService design); UI polls wear.csv every 2s — this is the right pattern |
| Web dashboard for camera results | Remote viewing of blade images from browser | Out of scope; existing system is desktop-first (industrial panel PC); add HTTP server complexity | Export summary CSV; use ThingsBoard dashboard for aggregated metrics |
| Continuous video recording (MP4/AVI) | "Keep full video history" | Disk space: 1920x1200 @ 50fps = ~1.8GB/min uncompressed; 30 minute session = 54GB; JPEG frame sequence is intentional design choice (selectively discard, random-access, no codec dependency) | JPEG frame sequence with configurable retention window; delete old recordings after N days |
| Interactive detection result editing | "Let operator mark false positives" | Adds UI complexity; creates ground truth labeling workflow; model retraining out of scope for this milestone | Log all detections; trust model confidence threshold (0.5 default) |
| Multi-camera support | "What if we need two cameras?" | CameraModule is designed for single device ID; multi-camera needs significant architecture change | Config `camera.device_id` is a single integer; document extension point, don't implement now |

---

## Feature Dependencies

```
Camera Page (GUI)
    requires --> CameraModule (OpenCV capture, multi-thread JPEG recording)
    requires --> Broken Detect (RT-DETR model, lazy-loaded)
    requires --> Crack Detect (RT-DETR model, lazy-loaded)
    requires --> VisionService (LDC pipeline, wear.csv writer)
    requires --> SawHealthCalculator (composite score)
    requires --> recordings/ directory structure
    requires --> camera.enabled config flag

CameraModule
    requires --> OpenCV (cv2.VideoCapture)
    requires --> camera config (device_id, width, height, fps, jpeg_quality, num_threads)
    requires --> recordings/ base directory

Broken Detect
    requires --> CameraModule (must record first, then detect)
    requires --> ultralytics RTDETR
    requires --> best.pt model file
    requires --> detection_stats.json output format

Crack Detect
    requires --> CameraModule (must record first, then detect)
    requires --> ultralytics RTDETR
    requires --> catlak-best.pt model file
    requires --> detection_stats.json (shared file, same recording dir)

VisionService (LDC wear pipeline)
    requires --> recordings/ directory (watches for new frame files)
    requires --> LDC model (modelB4.py + BIPED checkpoint)
    requires --> PyTorch
    requires --> wear.csv output format

SawHealthCalculator
    requires --> Broken Detect stats (total_tooth, total_broken)
    requires --> VisionService wear percentage

DB Integration
    requires --> Broken Detect + Crack Detect completed stats
    requires --> VisionService final wear_percent
    requires --> Existing SQLiteService pattern
    requires --> serit_id from existing system context

IoT Integration
    requires --> DB Integration (same detection_event row ID)
    requires --> Existing HTTP ThingsBoard client

config-driven enable
    requires --> lifecycle.py startup sequence understands camera.enabled
    requires --> CameraModule, VisionService, all camera imports guarded by flag
```

### Dependency Notes

- **CameraModule before detection:** Broken and crack detection run as batch post-processing on the latest recording folder. Recording must complete (or be manually stopped) before running detection models. This is intentional — not a limitation.
- **VisionService concurrent with recording:** Unlike detection models, VisionService watches the recording directory in real time and processes frames as they appear. It runs from `start()` to `stop()` alongside the main application, not just during active recording.
- **Shared detection_stats.json:** Both broken detect and crack detect write to the same JSON file in the recording directory. They use separate keys (`total_tooth`, `total_broken`, `total_crack`). Write operations must be thread-safe (old code uses per-file Lock).
- **config.enabled gates everything:** If `camera.enabled = false`, none of the above services should be instantiated. This includes skipping the GUI camera page entirely.

---

## MVP Definition

### Launch With (v2.0 — the milestone deliverable)

These are what PROJECT.md lists as "Active" requirements.

- [ ] **config-driven camera module** — `camera.enabled` in config.yaml; false = zero camera code loaded in lifecycle
- [ ] **OpenCV frame capture + JPEG recording** — CameraModule ported; 1920x1200, configurable FPS, multi-thread save
- [ ] **RT-DETR broken tooth detection** — best.pt model; batch post-processing; results to detection_stats.json
- [ ] **RT-DETR crack detection** — catlak-best.pt model; batch post-processing; results to detection_stats.json
- [ ] **LDC wear pipeline** — VisionService ported; concurrent watchdog; wear.csv per recording
- [ ] **SawHealthCalculator** — 70% broken / 30% wear formula; status text
- [ ] **Camera GUI page** — live feed, detection stats labels, wear %, health score; sequential image thumbnails
- [ ] **Sidebar navigation button** — camera icon added to existing sidebar widget
- [ ] **Detection results to SQLite** — new camera detection table; serit_id, timestamp, counts, wear, health
- [ ] **Detection results to ThingsBoard** — camera telemetry fields added to existing HTTP send cycle
- [ ] **Lifecycle integration** — camera services start/stop in ApplicationLifecycle based on config

### Add After Validation (v2.x)

Features worth adding once the v2.0 integration is verified stable.

- [ ] **Per-recording history panel** — show previous session summaries; trigger: operators request historical comparison
- [ ] **Configurable confidence threshold** — expose RT-DETR `conf` param in config.yaml; trigger: false positive complaints from operators
- [ ] **Recording retention policy** — auto-delete recordings older than N days; trigger: disk space alerts

### Future Consideration (v3+)

- [ ] **Online/incremental model updates** — retrain on false positives collected by operators; very high complexity
- [ ] **Multi-camera support** — second camera for blade back side; requires architecture change
- [ ] **Video export** — compile JPEG sequence to MP4 for shareable reports; trigger: explicit customer request

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| config-driven enable/disable | HIGH | LOW | P1 |
| CameraModule (capture + recording) | HIGH | MEDIUM | P1 |
| Broken tooth detection | HIGH | MEDIUM | P1 |
| Crack detection | HIGH | MEDIUM | P1 |
| LDC wear pipeline | HIGH | HIGH | P1 |
| SawHealthCalculator | HIGH | LOW | P1 |
| Camera GUI page | HIGH | HIGH | P1 |
| Sidebar nav button | HIGH | LOW | P1 |
| SQLite integration | MEDIUM | LOW | P1 |
| IoT telemetry | MEDIUM | LOW | P1 |
| Sequential image thumbnails | MEDIUM | LOW | P2 |
| Detection status icons | LOW | LOW | P2 |
| Wear visualization overlay | MEDIUM | MEDIUM | P2 |
| Per-recording history panel | MEDIUM | HIGH | P3 |
| Configurable confidence threshold | LOW | LOW | P3 |
| Recording retention policy | MEDIUM | LOW | P3 |

**Priority key:**
- P1: Must have for v2.0 launch (milestone scope)
- P2: Port from old project, adds polish, low risk
- P3: Defer to v2.x or later

---

## Implementation Details from Source Analysis

### Camera Module Architecture (Directly Ported)

The old `CameraModule` (`src/core/camera.py`) uses:
- `cv2.VideoCapture(CAMERA_DEVICE_ID)` with platform-aware backend (DSHOW on Windows)
- Continuous capture thread (`capture_loop` daemon thread)
- `Queue(maxsize=100)` feeding N save threads (configurable, default 4-8)
- JPEG quality 92, frame naming `frame_{n:06d}.jpg`
- `frame_ready` Event for live GUI updates
- Detection runs as a separate thread triggered post-recording
- `_detection_finish_callback` notifies GUI when batch is done

### Detection Stats File Format

`recordings/{YYYYMMDD-HHMMSS}/detection_stats.json`:
```json
{
    "total_tooth": 142,
    "total_broken": 7,
    "broken_ratio": 0.049,
    "total_crack": 3,
    "timestamp": "2026-03-16 14:22:33",
    "total_frames": 2500,
    "processed_frames": 2500,
    "status": "completed",
    "crack_status": "completed"
}
```

### Wear CSV Format

`recordings/{YYYYMMDD-HHMMSS}/wear.csv`:
```
timestamp,frame,wear_percent
2026-03-16T14:22:33,frame_000001.png,12.45
```

### Directory Structure for a Recording Session

```
recordings/
  20260316-142233/
    frame_000001.jpg ... frame_002500.jpg   (raw captures)
    detected/
      frame_000012_tooth3_broken1.jpg       (annotated, broken detect output)
    detected-crack/
      frame_000098_crack2.jpg               (annotated, crack detect output)
    ldc/
      frame_000001.png ...                  (edge maps from LDC)
    wear_vis/
      frame_000001.png ...                  (wear visualization overlays)
    wear.csv                                (wear % per frame)
    detection_stats.json                    (aggregate stats)
```

### GUI Page Timer Architecture

From old `CameraPage` (pyside_camera.py):
- `_camera_stream_timer` — 500ms — updates live feed QLabel
- `_periodic_timer` — 1000ms — syncs labels (frame count, state)
- `_wear_timer` — 2000ms — reads wear.csv, updates wear label
- `_kirik_frame_timer` — 5000ms — refreshes detected image thumbnails
- `_combined_image_refresh_timer` — 10000ms — refreshes all image panels
- `_datetime_timer` — 1000ms — updates date/time display

### Integration with Existing System

The camera page needs to receive `serit_id` and `makine_id` from the existing system's config/state.
The old project had no such linkage (standalone). In the new system, wire these from:
- `serit_id`: `raw_data.serit_id` (already in Modbus register 2230)
- `makine_id`: `raw_data.makine_id` (already in Modbus register 2251)

Both are already being captured and stored in existing DB tables as of v1.6.

---

## Sources

- Direct code analysis: `/media/workspace/eskiimas/smart-saw/src/core/camera.py` — CameraModule implementation
- Direct code analysis: `/media/workspace/eskiimas/smart-saw/src/core/broken_detect.py` — RT-DETR broken tooth detection
- Direct code analysis: `/media/workspace/eskiimas/smart-saw/src/core/crack_detect.py` — RT-DETR crack detection
- Direct code analysis: `/media/workspace/eskiimas/smart-saw/src/vision/service.py` — VisionService LDC wear pipeline
- Direct code analysis: `/media/workspace/eskiimas/smart-saw/src/vision/wear_detection/wear_calculation.py` — Wear algorithm
- Direct code analysis: `/media/workspace/eskiimas/smart-saw/src/core/saw_health_calculator.py` — Health score formula
- Direct code analysis: `/media/workspace/eskiimas/smart-saw/src/gui/controllers/pyside_camera.py` — Camera GUI page
- Project context: `/media/workspace/smart-saw/.planning/PROJECT.md` — v2.0 milestone requirements
- Current project config: `/media/workspace/smart-saw/config/config.yaml` — Existing system integration points

---

*Feature research for: Industrial camera-based saw tooth inspection system (v2.0 milestone)*
*Researched: 2026-03-16*

# Pitfalls Research

**Domain:** Adding camera vision & AI detection to an existing industrial async control system
**Researched:** 2026-03-16
**Confidence:** HIGH (OpenCV threading, PyTorch CUDA, Qt display patterns verified via official docs and community issue trackers)

---

## Critical Pitfalls

Mistakes that cause rewrites, data loss, or safety failures.

---

### Pitfall 1: cv2.VideoCapture.read() Blocks the Asyncio Event Loop

**What goes wrong:**
A developer calls `cap.read()` directly inside an `async def` coroutine or anywhere reachable from the 10 Hz asyncio processing loop. The call blocks for 30–100ms waiting for a USB/V4L2 frame. The asyncio event loop stalls. Modbus reads start missing their 100ms slot, IoT telemetry backs up, and the SQLite write queue grows. The effect looks like intermittent Modbus timeouts or database queue alarms — nothing in the camera code shows an obvious error.

**Why it happens:**
`cv2.VideoCapture.read()` is a synchronous, blocking C extension call. Although it releases the GIL while waiting in V4L2 or GStreamer, it still occupies the OS thread that asyncio is running on. Asyncio cannot schedule other coroutines while the thread is blocked.

**How to avoid:**
Run all camera capture in a dedicated `threading.Thread` (never in the asyncio event loop thread). The capture thread fills a `queue.Queue(maxsize=1)` or a `threading.Event` + shared frame reference using a lock. The asyncio side only reads the latest frame — never waits for capture.

```python
# WRONG: called from asyncio context
async def update_display():
    ret, frame = cap.read()  # Blocks event loop for 30-100ms

# RIGHT: camera runs in its own thread
class CameraCapture(threading.Thread):
    def run(self):
        while self._running:
            ret, frame = self._cap.read()
            if ret:
                with self._lock:
                    self._latest_frame = frame
```

**Warning signs:**
- Modbus read rate drops below 8 Hz when camera is enabled
- `data_pipeline.get_stats()['errors']` increases after camera start
- Health monitor logs database queue warnings shortly after camera init

**Phase to address:** Camera module phase (frame capture implementation). The capture thread must be designed before the detection pipeline is connected.

---

### Pitfall 2: Sharing a Single PyTorch/Ultralytics Model Across Multiple Threads

**What goes wrong:**
Three detection models (RT-DETR broken, RT-DETR crack, LDC edge) are loaded once at startup and called from different threads or at different times in the same detection loop. Internally, YOLO/Ultralytics models maintain per-call state (result buffers, preprocessing state). Concurrent or interleaved access causes `RuntimeError` during inference, silent wrong predictions, or CUDA context corruption requiring a process restart.

**Why it happens:**
Ultralytics documents explicitly that sharing a single model instance across threads causes race conditions on internal state. This is especially dangerous with two RT-DETR models that use the same Ultralytics predictor base class — their shared underlying C++ state is not re-entrant.

**How to avoid:**
Each detection pipeline gets its own model instance, loaded in the thread or context that will use it. For the sequential detection approach (broken → crack → LDC, one per frame), all three models load into the same detection thread and are called sequentially without sharing.

```python
# WRONG: one model, called from multiple call paths
class VisionService:
    def __init__(self):
        self.broken_model = YOLO("broken_best.pt")  # Shared instance

# RIGHT: models owned by the single detection thread
class DetectionThread(threading.Thread):
    def run(self):
        # Models instantiated inside the thread that uses them
        broken_model = YOLO("broken_best.pt")
        crack_model = YOLO("crack_best.pt")
        ldc_model = ...
        while self._running:
            frame = self._get_frame()
            broken_result = broken_model(frame)
            crack_result = crack_model(frame)
```

**Warning signs:**
- `RuntimeError` during `.predict()` calls that appears randomly
- Predictions differ between runs on the same frame
- CUDA errors after model is called from more than one call site

**Phase to address:** AI detection pipeline phase. The detection thread architecture must be settled before model loading code is written.

---

### Pitfall 3: torch.load() and CUDA Context Initialization Blocks Asyncio at Startup

**What goes wrong:**
Model loading (`torch.load()` or `YOLO("model.pt")`) is placed in `ApplicationLifecycle._init_camera()` and called with `await asyncio.get_event_loop().run_in_executor(None, ...)` — or worse, called synchronously. CUDA context initialization on first load takes 2–6 seconds. During this window, the asyncio event loop is frozen or the executor threadpool is saturated, delaying the rest of the startup sequence (Modbus connect, data pipeline start). If models are loaded synchronously they fully block the event loop.

**Why it happens:**
`torch.load()` is CPU-bound and performs CUDA driver initialization on first call. There is a confirmed PyTorch issue (`torch.load block asyncio loop · Issue #5879`) documenting that PyTorch holds the GIL and blocks the event loop. CUDA context init is an additional 1–3 second hit on first model load.

**How to avoid:**
Load all models in the detection thread's `run()` method after the thread starts, not in the lifecycle `start()` sequence. Lifecycle only starts the thread; the thread loads its own models asynchronously from the asyncio perspective. Signal readiness via an `asyncio.Event` set with `call_soon_threadsafe` when loading completes.

```python
class DetectionThread(threading.Thread):
    def run(self):
        # All model loading happens here, off the event loop thread
        self._broken_model = YOLO("broken_best.pt")
        self._crack_model = YOLO("crack_best.pt")
        self._ready_event.set()  # Signal lifecycle that models are ready
        self._detection_loop()
```

**Warning signs:**
- Startup takes 5+ seconds longer when camera is enabled
- Modbus "initial connection failed" logs on hardware that previously connected immediately
- Lifecycle startup sequence hangs on camera init step

**Phase to address:** Lifecycle integration phase (camera services startup/shutdown). Define the async-boundary contract between lifecycle and detection thread before model loading is implemented.

---

### Pitfall 4: QLabel.setPixmap() Called from Camera Thread (Not GUI Thread)

**What goes wrong:**
The camera display code calls `self.camera_label.setPixmap(...)` from a camera capture thread or detection thread. Qt silently queues the paint event on some platforms but crashes on others with "QObject: Cannot create children for a parent that is in a different thread." Even when it does not crash, the display update races with Qt's own repaint cycle, causing tearing, missed frames, or occasional segfaults on Linux.

**Why it happens:**
Qt enforces that all GUI operations happen on the thread that created the `QApplication`. `QLabel` and `QPixmap` are not thread-safe. Any cross-thread pixmap update bypasses Qt's object ownership model.

**How to avoid:**
Camera thread emits a Qt signal (`frame_ready = Signal(QImage)`) connected to a slot on the `CameraPage` widget. The signal carries a `QImage` (not `np.ndarray` or `QPixmap` — those are not safe to cross thread boundaries). The slot converts to `QPixmap` and calls `setPixmap` — all in the GUI thread.

```python
# Camera capture thread
class CameraThread(QThread):  # or threading.Thread with signal emission
    frame_ready = Signal(QImage)

    def _emit_frame(self, bgr_frame):
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.frame_ready.emit(image.copy())  # .copy() detaches from numpy buffer

# GUI widget slot
class CameraPage(QWidget):
    @Slot(QImage)
    def _on_frame_ready(self, image: QImage):
        self.camera_label.setPixmap(QPixmap.fromImage(image))
```

**Warning signs:**
- Application crashes when navigating to the camera page
- Occasional segfaults that only occur when the camera is running
- "QObject::setParent" or "timers cannot be stopped" error messages on shutdown

**Phase to address:** Camera GUI page phase. The signal/slot frame delivery pattern must be established before any display code is written.

---

### Pitfall 5: Config-Driven Optional Import Breaks at Runtime When camera.enabled=false

**What goes wrong:**
The camera module file is imported unconditionally by `lifecycle.py` even when `camera.enabled: false`. Inside that file, `import cv2`, `import torch`, or `from ultralytics import YOLO` fail with `ModuleNotFoundError` if those packages are not installed. The application crashes at startup on machines without the vision stack, even though the feature is disabled in config.

A related failure: the try/except guard wraps the import but the module variable is set to `None`, and later code that checks `if cv2 is None: return` misses a call site. One unguarded reference to `cv2` (e.g., in a type annotation evaluated at import time) causes `NameError`.

**Why it happens:**
Python evaluates module-level imports and type annotations at import time, not at use time. A `try: import cv2 except ImportError: cv2 = None` guard is bypassed by any `def foo(frame: cv2.Mat)` annotation in the same file.

**How to avoid:**
- The lifecycle uses `if config['camera']['enabled']` before importing anything camera-related
- Camera module files use `from __future__ import annotations` to defer annotation evaluation
- All camera imports live inside `if TYPE_CHECKING:` blocks or inside function bodies that are only called when the feature is enabled
- Use a boolean flag, not module-as-None: `CAMERA_AVAILABLE = False` then check the flag

```python
# lifecycle.py
async def _init_camera(self):
    if not self.config.get('camera', {}).get('enabled', False):
        logger.info("Camera disabled in config - skipping")
        return

    # Import ONLY after the config check passes
    from ..services.vision.camera_service import CameraService
    self.camera_service = CameraService(self.config)
```

**Warning signs:**
- `ModuleNotFoundError: No module named 'cv2'` in traceback that includes lifecycle startup
- Application that worked without camera suddenly fails after adding camera module files
- Type annotations referencing `cv2` or `torch` appear at module level

**Phase to address:** Camera module foundation phase (the very first camera phase). The import guard pattern must be established before any other camera code is written.

---

### Pitfall 6: BGR vs RGB Color Space Corruption in the Detection-Display Pipeline

**What goes wrong:**
OpenCV reads frames in BGR. The detection model (RT-DETR) expects RGB (standard PyTorch/torchvision convention). The display path (QImage) also expects RGB. A missing `cvtColor` conversion at one stage causes: (a) wrong colors in the live display — the image looks orange/blue-tinted, or (b) reduced detection accuracy because the model sees swapped channels that don't match training data color statistics, causing lower confidence scores on real detections.

The worst case: a conversion is applied twice (once before detection, once before display), causing a double-swap that looks correct in the display but feeds corrupted data to the model.

**Why it happens:**
The BGR/RGB distinction is a constant source of confusion when multiple consumers (model inference, recording, display) each touch the same frame. Each consumer has a different expectation, and the format is invisible at runtime — a `np.ndarray` carries no channel order metadata.

**How to avoid:**
Define one canonical frame format for the internal pipeline (choose RGB for model compatibility) and convert once at the camera capture boundary. Document this explicitly in the camera service.

```python
class CameraCapture:
    def get_frame_rgb(self) -> np.ndarray:
        """Returns frame in RGB format. Convert once here, never again downstream."""
        with self._lock:
            if self._latest_frame_bgr is None:
                return None
            return cv2.cvtColor(self._latest_frame_bgr, cv2.COLOR_BGR2RGB)

    def save_jpeg_bgr(self, path: str):
        """cv2.imwrite expects BGR — use raw frame, not converted."""
        with self._lock:
            if self._latest_frame_bgr is not None:
                cv2.imwrite(path, self._latest_frame_bgr)
```

**Warning signs:**
- Live display shows orange skin tones or blue sky that should appear red/normal
- Detection confidence scores are systematically lower than expected from the model's training metrics
- A "color looks correct" check passes in isolation but fails end-to-end

**Phase to address:** Camera module phase (frame capture and format contract). Establish the canonical format decision in the camera service before the display or detection pipelines touch any frames.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Call detection every frame (30 Hz) instead of on a timer | Simpler code | GPU thrashes at 30 Hz; existing 10 Hz ML model and detection compete for CUDA; detection latency spikes under load | Never — use a configurable detection interval (e.g., every 3rd frame or 1 Hz) |
| Storing raw frames (PNG/BMP) instead of JPEG | No lossy compression | Disk fills in hours on an industrial panel PC with limited storage | Never for continuous recording; JPEG with quality 85 is the right default |
| Running LDC edge detection on CPU inside detection thread | Avoids GPU memory pressure | LDC on large frames (1280x720) takes 80–200ms on CPU, stalling the detection thread | Acceptable only if frame resolution is 640x480 or smaller |
| Importing torch at module top-level for type hints | Convenient | Breaks camera.enabled=false deployments without GPU drivers | Never — use `TYPE_CHECKING` guard |
| Writing detection results to SQLite synchronously from detection thread | Simplest code | SQLite calls from a non-queue thread bypass the existing write-queue pattern, risking lock contention with the 10 Hz pipeline | Never — use the existing SQLite queue pattern |
| Loading all three models sequentially in lifecycle startup | Deterministic order | Blocks asyncio event loop for 6–18 seconds on cold start | Never — load in detection thread, not lifecycle |

---

## Integration Gotchas

Common mistakes when connecting camera/AI components to the existing system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| SQLite (detection results) | Writing from detection thread directly using `sqlite3.connect()` | Use the existing `SQLiteService` queue pattern: call `db_service.queue_write(sql, params)` from the detection thread |
| IoT / ThingsBoard | Calling `iot_service.send_telemetry()` synchronously from detection thread | Queue detection results to the main data pipeline so the existing IoT batching handles them at the next 10 Hz cycle |
| 10 Hz processing loop | Passing detection results via a shared dict without a lock | Use `threading.Lock` or `queue.Queue` for the detection-result-to-pipeline handoff; the same lock pattern used by `AnomalyManager` |
| Lifecycle shutdown | Not stopping camera/detection threads before database flush | Add camera stop to lifecycle `stop()` before step 5 (SQLite flush), mirroring how GUI thread is joined first |
| Config | Reading `camera.enabled` at each call site | Read once during `_init_camera()` and store as `self._camera_enabled`; avoids scattered config reads |
| Health monitor | Not including camera/detection thread health in the 30s health check | Add frame rate and detection queue depth to `get_status()` so health monitor can alarm on camera stalls |

---

## Performance Traps

Patterns that work during testing but fail under sustained industrial operation.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Detection thread reads frames faster than they are produced | CPU spins at 100% in detection thread polling an empty queue | Use `queue.get(timeout=0.1)` instead of `get_nowait()` with a spin loop | Immediately — becomes visible as high CPU in `top` |
| QTimer interval set to 0ms for "fastest possible" display | Qt paint events flood the GUI thread; existing GUI updates (graphs, sensor labels) starve | Use 100–200ms QTimer interval for camera display (5–10 Hz is sufficient for live monitoring) | When camera page is open and operator interacts with other controls |
| Saving JPEG per-frame during active detection at 30 Hz | Disk I/O 1–3 MB/s sustained; SSD write amplification; detection thread stalls waiting for `cv2.imwrite` | Write JPEG in a separate writer thread with a bounded queue; only record when `testere_durumu == 3` (cutting state) | After 30–60 minutes of continuous operation |
| Loading 3 models without `torch.no_grad()` context | Gradient buffers allocated for every inference call; GPU memory doubles | Wrap all inference in `with torch.no_grad():` | Models load fine; OOM error appears during the first cutting session |
| Not calling `cap.release()` on camera service stop | USB camera device remains held; restart required to re-open camera | Always call `cap.release()` in the camera thread's cleanup; add to lifecycle stop sequence | When operator exits and restarts application |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Camera display working:** Often missing RGB conversion — verify colors look correct on real hardware, not just a test image
- [ ] **Detection results saving:** Often missing the SQLite queue pattern — verify with `db_service.get_stats()['queue_size']` that writes are going through the queue, not direct sqlite3 calls
- [ ] **config camera.enabled=false:** Often still imports cv2 — verify by running on a machine without OpenCV installed; startup should succeed
- [ ] **Lifecycle shutdown:** Often camera thread is not joined before shutdown completes — verify no "Timers cannot be stopped from another thread" errors on exit
- [ ] **GPU memory:** Often `torch.no_grad()` missing — verify with `torch.cuda.memory_allocated()` before and after inference; should not grow
- [ ] **Detection thread safety:** Often models accessed from more than one call site — verify there is exactly one path to each model's `.predict()` method
- [ ] **IoT integration:** Often detection results bypass the IoT service entirely — verify ThingsBoard receives detection telemetry by checking device attributes after a test cut
- [ ] **JPEG recording:** Often records every frame even when saw is idle — verify recording only activates when `testere_durumu == 3`

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Asyncio event loop blocked by `cap.read()` | MEDIUM | Refactor: move all capture to a dedicated thread; no asyncio changes needed in detection code |
| Model shared across threads (race condition) | MEDIUM | Add `threading.Lock` around all `.predict()` calls as temporary fix; proper fix is per-thread model instances |
| `torch.load()` blocking startup | LOW | Move model loading from `_init_camera()` to `DetectionThread.run()` — typically a 10-line change |
| Camera imported unconditionally (import error) | LOW | Add lifecycle config guard; add `from __future__ import annotations` to camera module files |
| BGR/RGB double conversion (bad predictions) | LOW | Add a `_frame_format = "RGB"` constant to camera service; audit all call sites in 30 minutes |
| QLabel.setPixmap() from wrong thread (crash) | HIGH | Must redesign frame delivery to use Qt signal/slot; no quick fix; plan 1–2 hours refactor |
| JPEG write stalling detection thread | MEDIUM | Extract JPEG write to a writer thread with bounded queue; 50-line change but requires adding a new thread lifecycle |
| Detection results not reaching IoT | LOW | Add detection result fields to the telemetry dict in data pipeline; no architectural change needed |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| cap.read() blocking asyncio (Pitfall 1) | Camera capture module phase | Measure Modbus read rate (must stay at 10 Hz) with camera running |
| Shared model instances (Pitfall 2) | Detection pipeline phase | Code review: grep for model instantiation outside thread `run()` method |
| torch.load() blocking startup (Pitfall 3) | Lifecycle integration phase | Time startup with and without camera enabled; delta must be < 500ms |
| setPixmap() from wrong thread (Pitfall 4) | Camera GUI page phase | Run application with Python's `-W error` mode; any cross-thread Qt warning becomes an error |
| Unconditional cv2 import (Pitfall 5) | Camera module foundation (first camera phase) | Test startup with camera.enabled=false on a machine without OpenCV installed |
| BGR/RGB corruption (Pitfall 6) | Camera module phase | Manual verification: display a known test image (red object); verify it appears red |
| JPEG recording stalling detection | JPEG recording phase | Profile detection thread frame processing time; must stay < 50ms per frame |
| SQLite detection writes bypassing queue | Detection results storage phase | Check `db_service.get_stats()` — queue_size should increase, not zero |
| Lifecycle shutdown ordering | Lifecycle integration phase | Automated: run app, start camera, kill gracefully; no segfault, no "timer" errors |
| torch.no_grad() missing (GPU OOM) | Detection pipeline phase | `torch.cuda.memory_allocated()` must be stable after 100 inference calls |

---

## Sources

- [opencv/opencv Issue #24393: How to avoid blocking with cv2.VideoCapture.read()](https://github.com/opencv/opencv/issues/24393) — confirms blocking nature of VideoCapture.read()
- [opencv/opencv Issue #24229: Does cv::VideoCapture have any thread lock?](https://github.com/opencv/opencv/issues/24229) — documents thread safety constraints
- [Ultralytics YOLO Thread-Safe Inference Guide](https://docs.ultralytics.com/guides/yolo-thread-safe-inference/) — official guidance on per-thread model instantiation
- [pytorch/pytorch Issue #5879: torch.load blocks asyncio loop](https://github.com/pytorch/pytorch/issues/5879) — confirmed asyncio blocking during torch.load
- [PyTorch CUDA semantics documentation](https://docs.pytorch.org/docs/stable/notes/cuda.html) — CUDA context initialization overhead
- [PySide6 QImage documentation](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html) — thread safety constraints for QPixmap/QImage
- [How to display OpenCV video in PyQt apps (gist)](https://gist.github.com/docPhil99/ca4da12c9d6f29b9cea137b617c7b8b1) — QThread + Signal pattern for OpenCV/Qt
- [Multithreading PySide6 applications with QThreadPool — pythonguis.com](https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/) — Qt threading patterns
- [Python optional imports discussion — discuss.python.org](https://discuss.python.org/t/optional-imports-for-optional-dependencies/104760) — config-driven import guard patterns
- [PyTorch Frequently Asked Questions — memory management](https://docs.pytorch.org/docs/stable/notes/faq.html) — `torch.no_grad()` and GPU memory
- [Codebase ARCHITECTURE.md](../.planning/codebase/ARCHITECTURE.md) — existing concurrency model (asyncio + threading hybrid)
- [src/core/lifecycle.py](../src/core/lifecycle.py) — existing startup/shutdown sequence; camera services must follow same pattern

---
*Pitfalls research for: camera vision & AI detection integration into existing industrial async control system*
*Researched: 2026-03-16*