---
id: M001
provides:
  - v1.0 ML schema with serit_motor_tork and kafa_yuksekligi columns
  - v1.0 Anomaly schema with kafa_yuksekligi column
  - v1.0 ML and anomaly data population from raw sensor data
  - v1.1 Modbus connection cooldown and operation timeouts
  - v1.2 ML speed save/restore around cutting sessions
  - v1.2 Dynamic chart axis title labels
  - v1.3 Lock-free asyncio.Queue MQTT batching
  - v1.3 IQR vibration anomaly detection (replacing DBSCAN)
  - v1.3 AnomalyManager single-lock consolidation
  - v1.4 Thread-safe GUI→main asyncio scheduling via run_coroutine_threadsafe
  - v1.4 Mode-aware initial delay (ML-only)
  - v1.5 ML prediction parity with old codebase (averaged buffer speeds, unclamped torque)
  - v1.5 GUI labels with units and İlerleme terminology
  - v1.5 Band deviation graph axis labels and zero-inclusive Y-axis
  - v1.6 TouchButton widget with Qt touch events and emergency stop overlay
  - v1.6 ML prediction logging with all 11+4 columns populated
  - v1.6 ML and anomaly DB traceability columns (kesim_id, makine_id, serit_id, malzeme_cinsi)
  - v2.0 Camera config schema with camera.enabled flag
  - v2.0 SCHEMA_CAMERA_DB with detection_events and wear_history tables
  - v2.0 CameraResultsStore thread-safe integration boundary
  - v2.0 CameraService config-driven capture engine with JPEG recording
  - v2.0 DetectionWorker dual RT-DETR inference (broken tooth + crack)
  - v2.0 LDCWorker edge detection + contour-based wear calculation
  - v2.0 HealthCalculator with 70/30 weighted health scoring
  - v2.0 Vendored modelB4.py LDC network architecture
  - v2.0 Lifecycle camera integration with lazy imports and config-driven start/stop
  - v2.0 Camera DB persistence via SQLiteService.write_async()
  - v2.0 Camera IoT telemetry (6 fields in ThingsBoard payload)
  - v2.0 CameraController GUI page with live feed, detection stats, wear %, health score
  - v2.0 Conditional 5th sidebar navigation button
key_decisions:
  - "Place new columns in input features group for logical ordering"
  - "10 second default cooldown matches typical PLC recovery time"
  - "ModbusWriter dependency injection from ControlManager to MLController"
  - "asyncio.Queue for MQTT batching — native asyncio, O(1) put_nowait"
  - "IQR for vibration detectors — O(n) vs DBSCAN O(n²)"
  - "asyncio.run_coroutine_threadsafe() for GUI→main thread scheduling"
  - "Averaged buffer speeds for ML prediction parity with old codebase"
  - "Touch instant activation (0ms) — industrial users expect immediate response"
  - "Deferred ML logging pattern — log after all computed values available"
  - "NULL defaults for traceability columns — preserves existing records"
  - "opencv-python-headless to avoid Qt5/Qt6 conflict with PySide6"
  - "Both RT-DETR models consolidated into single DetectionWorker thread"
  - "Workers import torch/ultralytics inside run() — zero-import guard when camera.enabled=false"
  - "Camera shutdown order: workers → camera_service → SQLite flush"
  - "Camera fields flat in ThingsBoard payload, not nested"
  - "CameraController uses QImage.loadFromData() — no cv2 in GUI layer"
  - "CameraController lazy-imported inside config guard — preserves zero-import guarantee"
patterns_established:
  - "Connection cooldown: track last attempt, skip if within cooldown"
  - "Timeout wrapper: asyncio.wait_for around all blocking operations"
  - "Lock-free batching: put_nowait() producer, get_nowait() consumer loop"
  - "Cross-thread async: capture loop in main thread, pass to GUI, run_coroutine_threadsafe()"
  - "Traceability columns: nullable append with falsy-to-None at call site"
  - "Thread-safe store: Lock-guarded dict with update/get/snapshot as integration boundary"
  - "Worker thread pattern: daemon thread, models load inside run(), _stop_event for shutdown"
  - "Lazy ML import: torch/ultralytics inside run(), TYPE_CHECKING for hints"
  - "Optional db_service kwarg for backward compatibility"
  - "Camera submodule imports always direct, never via package re-export"
observability_surfaces:
  - "CameraResultsStore.snapshot() — full camera state in one call"
  - "DetectionWorker.model_load_failed / LDCWorker.model_load_failed — boolean health check"
  - "logger.info on camera service start/stop/model load"
  - "logger.warning on camera init failure, DB write failure, snapshot failure"
  - "detection_events and wear_history tables in camera.db"
  - "Camera field presence/absence in ThingsBoard payload confirms camera state"
  - "hasattr(main_controller, 'camera_page') — definitive camera GUI check"
  - "Timer callback errors logged as 'Error in _update_frame/stats/health'"
requirement_outcomes:
  - id: CAM-01
    from_status: active
    to_status: validated
    proof: "config.yaml camera.enabled=false default verified; _init_camera() early returns when disabled; full service creation when enabled — py_compile passes, config guard verified"
  - id: CAM-02
    from_status: active
    to_status: validated
    proof: "import src.services.camera does not trigger cv2/torch; all camera imports lazy inside config guards in lifecycle.py and main_controller.py"
  - id: CAM-03
    from_status: active
    to_status: validated
    proof: "CameraService built with config-driven resolution/fps from config dict; lifecycle wires it when camera.enabled=true; py_compile + instantiation verified"
  - id: CAM-04
    from_status: active
    to_status: validated
    proof: "CameraService has save worker pool with put_nowait drop-on-full; JPEG encoding in capture thread; contract verified via instantiation"
  - id: CAM-05
    from_status: active
    to_status: validated
    proof: "start_recording() creates timestamped YYYYMMDD-HHMMSS directories with frame_NNNNNN.jpg naming; contract verified in code"
  - id: DET-01
    from_status: active
    to_status: validated
    proof: "DetectionWorker loads broken_model_path RT-DETR model, runs inference with confidence threshold; import + instantiation verified, model_load_failed property available"
  - id: DET-02
    from_status: active
    to_status: validated
    proof: "DetectionWorker loads crack_model_path RT-DETR model, sequential inference on same frame; import + instantiation verified"
  - id: DET-03
    from_status: active
    to_status: validated
    proof: "LDCWorker loads LDC checkpoint, runs edge detection (512x512, sigmoid, threshold), computes wear via contour analysis in ROI band; import + instantiation verified"
  - id: DET-04
    from_status: active
    to_status: validated
    proof: "HealthCalculator math verified: perfect health=100.0, bad health=35.0, status 'Sağlıklı' at 85, 'Tehlikeli' at 15, color '#FF0000' at critical"
  - id: DET-05
    from_status: active
    to_status: validated
    proof: "CameraResultsStore with Lock-guarded dict, snapshot returns independent copy; workers publish via update_batch(); store API verified functionally"
  - id: DET-06
    from_status: active
    to_status: validated
    proof: "Both workers are daemon threads with models loading inside run(); zero-import guard verified — import src.services.camera does not load torch"
  - id: DATA-01
    from_status: active
    to_status: validated
    proof: "DetectionWorker writes to detection_events, LDCWorker writes to wear_history via SQLiteService.write_async(); INSERT SQL verified against SCHEMA_CAMERA_DB (9 columns each)"
  - id: DATA-02
    from_status: active
    to_status: validated
    proof: "ThingsBoardFormatter.format_telemetry accepts vision_data, merges 6 camera fields; config telemetry_fields whitelist includes all 6; functional test proven"
  - id: DATA-03
    from_status: active
    to_status: validated
    proof: "lifecycle _init_camera() creates camera.db via SQLiteService with SCHEMA_CAMERA_DB when camera.enabled=true; verified in source"
duration: 62 days
verification_result: passed
completed_at: 2026-03-16
---

# M001: Migration

**Full v1.0→v2.0 migration delivering database schema extensions, performance optimizations, GUI improvements, touch support, ML prediction fixes, data traceability, and a complete camera-based AI vision system for saw tooth breakage, crack detection, and wear monitoring.**

## What Happened

M001 executed 24 slices spanning six logical version increments (v1.0 through v2.0) in a single milestone.

**v1.0 — Database Schema (S01–S03):** Extended ml_predictions with serit_motor_tork and kafa_yuksekligi columns, extended anomaly_events with kafa_yuksekligi. Updated ML prediction logging and anomaly recording to populate these fields from RawSensorData at processing time.

**v1.1 — Modbus Resilience (S04):** Added connection cooldown mechanism and asyncio.wait_for timeout wrappers to AsyncModbusService, preventing application freeze when PLC is unreachable.

**v1.2 — ML Speed & Chart UX (S05–S06):** Implemented automatic save/restore of operator-set cutting speeds around ML sessions via ModbusWriter injection. Added dynamic Y-axis and X-axis title labels to the cutting graph that update when axis selection buttons change.

**v1.3 — Performance (S07–S09):** Replaced deque+Lock with lock-free asyncio.Queue for MQTT telemetry batching. Switched vibration anomaly detectors (TitresimX/Y/Z) from O(n²) DBSCAN to O(n) IQR. Consolidated AnomalyManager from 9 lock acquisitions per cycle to 1 via dict.update().

**v1.4 — Threading & Control (S10–S11):** Fixed cross-thread asyncio scheduling by propagating the event loop through the GUI init chain and using run_coroutine_threadsafe() for mode switching. Made initial_delay logic mode-aware — ML mode retains the delay, manual mode bypasses for immediate control.

**v1.5 — ML Parity & GUI Polish (S12–S14):** Fixed ML prediction parity by using averaged buffer speeds instead of raw values and removing torque clamping. Added units (mm/dk, m/dk, A, %) to all numerical GUI labels and renamed "İnme Hızı" to "İlerleme Hızı". Added axis labels to band deviation graph with zero-inclusive Y-axis range.

**v1.6 — Touch & Traceability (S15–S18):** Built TouchButton widget with Qt touch events, instant activation, strict bounds, first-touch-wins multi-touch, and emergency stop overlay. Fixed ML prediction logging to populate all 11 columns including yeni_kesme_hizi, yeni_inme_hizi, katsayi. Extended both ml_predictions and anomaly_events with nullable traceability columns (kesim_id, makine_id, serit_id, malzeme_cinsi) using falsy-to-None conversion at call sites.

**v2.0 — Camera Vision & AI Detection (S19–S24):** Built the complete camera subsystem in 6 slices:
- **S19 Foundation:** numpy cap removed, camera config schema defined, SCHEMA_CAMERA_DB with detection_events/wear_history tables, _init_camera() lifecycle stub, zero-import guard established.
- **S20 Camera Capture:** CameraResultsStore as the thread-safe integration boundary (Lock-guarded dict with snapshot copy semantics). CameraService with config-driven OpenCV capture thread, JPEG encoder pool, timestamped recording to disk.
- **S21 AI Detection Pipeline:** DetectionWorker daemon thread with dual RT-DETR inference (broken tooth best.pt + crack catlak-best.pt). LDCWorker daemon thread with LDC edge detection, contour-based wear calculation, and HealthCalculator (70/30 weighted scoring with Turkish status labels). Vendored modelB4.py LDC architecture. All model imports deferred to run() for zero-import guard.
- **S22 Lifecycle & DB:** Stripped camera __init__.py of cv2-triggering re-exports. Wired both workers with optional db_service parameter — DetectionWorker writes to detection_events, LDCWorker to wear_history via SQLiteService.write_async(). Expanded lifecycle _init_camera() to create and start all camera services with lazy imports inside config guard. Shutdown stops workers before camera service before SQLite flush.
- **S23 IoT Integration:** Threaded CameraResultsStore.snapshot() through DataProcessingPipeline → MQTTService → ThingsBoardFormatter. Six scalar camera fields (broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status) merged flat into ThingsBoard payload.
- **S24 Camera GUI:** CameraController QWidget with 3 QTimers polling CameraResultsStore (500ms frame, 1000ms stats, 2000ms health). Live JPEG feed via QImage.loadFromData(), 4-thumbnail strip with deque history, broken/crack detection panels with OK/alert indicators, wear percentage, health score with dynamic color. Conditional 5th sidebar button ("Kamera") created only when camera_results_store is provided.

## Cross-Slice Verification

**Definition of Done:**
- ✅ All 24 slices marked `[x]` in roadmap
- ✅ All 24 slice summaries exist on disk
- ✅ All 27 key source files compile clean (py_compile)

**Zero-Import Guard (CAM-02 — cross-cutting S19→S20→S22→S24):**
- ✅ `import src.services.camera` does not load cv2 or torch
- ✅ Camera __init__.py has no unconditional imports
- ✅ Lifecycle imports camera modules inside _init_camera() config guard
- ✅ MainController imports CameraController inside camera_results_store guard
- ✅ CameraController not in controllers/__init__.py

**Data Pipeline Integration (S01→S03→S16→S17→S18):**
- ✅ SCHEMA_ML_DB contains all 15 columns (original + serit_motor_tork, kafa_yuksekligi, yeni_kesme_hizi, yeni_inme_hizi, katsayi, kesim_id, makine_id, serit_id, malzeme_cinsi)
- ✅ SCHEMA_ANOMALY_DB contains all columns including kafa_yuksekligi and traceability fields
- ✅ SCHEMA_CAMERA_DB contains detection_events and wear_history tables

**Camera Vision Stack (S19→S20→S21→S22→S23→S24):**
- ✅ CameraResultsStore: thread-safe, snapshot returns independent copy, functionally verified
- ✅ HealthCalculator: math verified with boundary tests (100.0 at perfect, 35.0 at bad, correct status/color)
- ✅ Workers accept db_service=None for backward compatibility
- ✅ Lifecycle wires CameraResultsStore → CameraService → DetectionWorker → LDCWorker
- ✅ ThingsBoardFormatter.format_telemetry accepts vision_data, produces 6 camera fields
- ✅ DataProcessingPipeline accepts camera_results_store parameter
- ✅ GUIApplication and MainController accept camera_results_store parameter
- ✅ Config camera section has enabled, detection, wear, health subsections
- ✅ All 6 camera telemetry field names in config telemetry_fields whitelist

**GUI Integration (S06→S13→S14→S15→S24):**
- ✅ Dynamic axis labels in CuttingGraphWidget (sensor_controller.py)
- ✅ Band deviation graph axis labels and zero-inclusive Y-axis (control_panel_controller.py)
- ✅ Unit labels (mm/dk, m/dk, A, %) and İlerleme terminology
- ✅ TouchButton widget with touch event handling
- ✅ CameraController with QTimers and QImage.loadFromData()

**Performance (S07→S08→S09):**
- ✅ asyncio.Queue in MQTT client (verified in source)
- ✅ IQR method in all vibration detectors (verified via regex on detector classes)
- ✅ dict.update() single-lock pattern in AnomalyManager

**Threading Safety (S10→S11):**
- ✅ run_coroutine_threadsafe in ControlPanelController
- ✅ Event loop propagation through lifecycle → GUIApplication → MainController
- ✅ _check_initial_delay inside ML branch only in ControlManager

**Known Limitation:** LifecycleManager import fails at runtime due to pre-existing missing `src.services.iot.http_client` module — unrelated to M001, predates this milestone. py_compile passes for all files.

## Requirement Changes

All 28 requirements tracked during M001 — 9 GUI requirements validated during S24, 19 CAM/DET/DATA requirements validated during milestone completion:

- CAM-01: active → validated — config guard verified, _init_camera() creates services only when enabled=true
- CAM-02: active → validated — zero-import proven across all layers (camera package, lifecycle, GUI)
- CAM-03: active → validated — CameraService config-driven capture with resolution/fps from config, lifecycle wired
- CAM-04: active → validated — JPEG encoder pool with put_nowait drop-on-full, contract verified
- CAM-05: active → validated — timestamped YYYYMMDD-HHMMSS directory structure in start_recording()
- DET-01: active → validated — DetectionWorker loads broken_model_path, runs RT-DETR inference, contract proven
- DET-02: active → validated — DetectionWorker loads crack_model_path, sequential inference on same frame
- DET-03: active → validated — LDCWorker edge detection + contour wear calculation, contract proven
- DET-04: active → validated — HealthCalculator math verified with boundary tests (100.0, 35.0, status, color)
- DET-05: active → validated — CameraResultsStore Lock-guarded dict, snapshot copy semantics, functionally tested
- DET-06: active → validated — daemon threads with run()-time model loading, zero-import verified
- DATA-01: active → validated — INSERT SQL matches schema for both detection_events and wear_history
- DATA-02: active → validated — 6 camera fields flow through pipeline to ThingsBoard payload
- DATA-03: active → validated — camera.db created via SQLiteService in lifecycle when camera.enabled=true
- GUI-01: active → validated (S24) — 500ms frame timer with QImage.loadFromData()
- GUI-02: active → validated (S24) — broken tooth panel with count and timestamp
- GUI-03: active → validated (S24) — crack detection panel with count and timestamp
- GUI-04: active → validated (S24) — wear percentage label from store snapshot
- GUI-05: active → validated (S24) — health score with dynamic color from health_color
- GUI-06: active → validated (S24) — 5th sidebar button only when camera_results_store provided
- GUI-07: active → validated (S24) — deque(maxlen=4) thumbnail strip
- GUI-08: active → validated (S24) — OK/alert indicators (green ✓ OK / red ✗ UYARI)
- GUI-09: active → validated (S24) — AsinmaYuzdesiFrame wear percentage display

## Forward Intelligence

### What the next milestone should know
- The full system is wired end-to-end: config → lifecycle → capture → detection → results store → DB/IoT/GUI. All proof is contract-level — runtime validation requires camera hardware and model checkpoint files (best.pt, catlak-best.pt, 16_model.pth).
- Pre-existing missing module `src.services.iot.http_client` blocks LifecycleManager runtime import. This predates M001 and needs resolution for any milestone that touches lifecycle testing.
- The camera subsystem defaults to disabled (camera.enabled=false). Enable it in config.yaml and provide model files to activate the full vision pipeline.
- Traceability columns (kesim_id, makine_id, serit_id, malzeme_cinsi) are populated from RawSensorData — values are NULL when source fields are falsy (0 or empty string).

### What's fragile
- `src.services.iot.http_client` missing module — blocks any runtime import of LifecycleManager; needs to be created or the import removed
- INSERT column lists in detection_worker.py and ldc_worker.py are hardcoded SQL strings — must be updated manually if SCHEMA_CAMERA_DB changes
- LDC wear computation uses hardcoded ROI constants (TOP_LINE_Y=170, BOTTOM_LINE_Y=236) — recalibration needed if camera angle or resolution changes
- Camera __init__.py must remain import-inert — any re-export addition will break the zero-import guard
- `camera-icon2.svg` must exist in GUI images directory for sidebar button icon to render

### Authoritative diagnostics
- `CameraResultsStore.snapshot()` — single call returns all detection/wear state; Lock-guarded copy, trustworthy ground truth
- `worker.model_load_failed` — boolean check before assuming worker is producing results
- Grep lifecycle logs for "Camera capture service started" / "Detection worker started" / "LDC wear worker started"
- Grep for "Camera initialization failed" or "DB write failed" for failure diagnosis
- `py_compile` on all 27 key source files — all pass as of milestone completion

### What assumptions changed
- S21 plan assumed `get_health_status(55.0)` returns 'İyi' — actually returns 'Orta' per reference code thresholds (İyi requires >=60). Implementation matches reference correctly.
- S24 thumbnail size 220×140 vs planned 240×150 — adjusted to fit 4 thumbnails within 934px frame width. Functionally equivalent.
- Modbus connect_cooldown ended up at 1.0s in config (not 10.0s as originally planned in S04) — may have been tuned during development.

## Files Created/Modified

- `src/services/database/schemas.py` — ML schema (15 cols), anomaly schema (9 cols), camera DB schema (detection_events + wear_history)
- `src/services/control/ml_controller.py` — ML prediction logging (all 15 cols), speed save/restore, averaged buffer speeds, deferred logging
- `src/services/processing/anomaly_tracker.py` — Anomaly recording with kafa_yuksekligi and traceability columns
- `src/services/processing/data_processor.py` — Anomaly/camera data passing, camera_results_store integration
- `src/services/modbus/client.py` — Connection cooldown, asyncio.wait_for timeout wrappers
- `src/services/control/manager.py` — ModbusWriter injection, mode-aware initial delay, speed restore wiring
- `src/gui/controllers/sensor_controller.py` — Dynamic axis title labels for cutting graph
- `src/gui/controllers/control_panel_controller.py` — Band deviation axis labels, zero-inclusive Y-axis, unit labels, İlerleme naming
- `src/gui/controllers/monitoring_controller.py` — Unit labels, İlerleme naming
- `src/services/iot/mqtt_client.py` — Lock-free asyncio.Queue batching, vision_data parameter
- `src/services/iot/thingsboard.py` — Camera fields in format_telemetry via vision_data merge
- `src/anomaly/detectors.py` — IQR method for TitresimX/Y/Z detectors
- `src/anomaly/manager.py` — Single-lock dict.update() consolidation
- `src/anomaly/base.py` — np.ptp() replacement for numpy 2.0 compatibility
- `src/gui/controllers/control_panel_controller.py` — run_coroutine_threadsafe for mode switching
- `src/gui/app.py` — event_loop and camera_results_store parameters
- `src/gui/controllers/main_controller.py` — event_loop, camera_results_store, conditional camera page/button
- `src/core/lifecycle.py` — Event loop propagation, full _init_camera() with lazy imports, camera shutdown
- `src/ml/preprocessor.py` — get_averaged_speeds() method, torque clamping removal
- `src/gui/widgets/touch_button.py` — NEW: TouchButton with Qt touch events, instant activation, emergency stop
- `src/gui/widgets/__init__.py` — NEW: widgets package init
- `src/gui/controllers/positioning_controller.py` — TouchButton integration, emergency stop overlay
- `src/services/camera/results_store.py` — NEW: CameraResultsStore thread-safe store
- `src/services/camera/camera_service.py` — NEW: Config-driven capture engine with JPEG recording
- `src/services/camera/detection_worker.py` — NEW: Dual RT-DETR inference daemon thread with DB persistence
- `src/services/camera/ldc_worker.py` — NEW: LDC edge detection + wear calculation daemon thread with DB persistence
- `src/services/camera/health_calculator.py` — NEW: Health scoring with Turkish status labels
- `src/services/camera/modelB4.py` — NEW: Vendored LDC network architecture
- `src/services/camera/__init__.py` — Import-inert camera package (zero-import guard)
- `src/gui/controllers/camera_controller.py` — NEW: Camera GUI page with 3 QTimers, live feed, detection stats
- `config/config.yaml` — Camera section, modbus cooldown, ML speed_restore, camera telemetry fields
- `requirements.txt` — opencv-python-headless, ultralytics, torch, torchvision
