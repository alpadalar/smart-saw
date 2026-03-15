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
