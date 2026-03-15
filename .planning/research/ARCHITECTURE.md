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
