# Phase 22: Lifecycle & DB Integration - Research

**Researched:** 2026-03-26
**Domain:** Application lifecycle integration, SQLite DB writes, daemon thread orchestration
**Confidence:** HIGH

## Summary

Phase 22 connects the camera subsystem (built in Phases 19-21) to the application lifecycle and activates SQLite persistence for detection results. The three core deliverables are: (1) a new VisionService daemon thread that polls testere_durumu from CameraResultsStore and triggers CameraService.start_recording()/stop_recording() on cutting-end transitions, (2) populating the currently-NULL fields in worker DB write_async calls (image_path, edge_pixel_count, traceability fields) by flowing data through CameraResultsStore, and (3) writing testere_durumu and traceability fields from DataProcessingPipeline into CameraResultsStore so VisionService and workers can consume them.

The existing codebase is remarkably well-prepared. Workers already have DB write code with `db_service.write_async()` calls, lifecycle already injects `camera_db_service` into workers, and DataProcessingPipeline already receives `camera_results_store`. The remaining work is: (a) create VisionService, (b) add VisionService to lifecycle startup/shutdown, (c) have DataProcessingPipeline write testere_durumu and traceability fields to CameraResultsStore, (d) update worker DB writes to read traceability/image fields from CameraResultsStore and pass them to write_async instead of None.

**Primary recommendation:** Create VisionService as a daemon thread following the exact DetectionWorker/LDCWorker pattern (threading.Event for stop, daemon=True), add it to _init_camera() and shutdown sequence in lifecycle.py, update DataProcessingPipeline to write testere_durumu/traceability to CameraResultsStore, and update worker DB write calls to fill currently-NULL fields.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** VisionService daemon thread olarak calisir (DetectionWorker, LDCWorker ile ayni pattern). asyncio event loop'u bloklamaz.
- **D-02:** VisionService testere durumunu CameraResultsStore uzerinden okur. DataProcessingPipeline her dongude testere_durumu'nu CameraResultsStore'a yazar, VisionService oradan periyodik polling yapar.
- **D-03:** Recording tetikleme: testere_durumu 3'den (CUTTING) farkli bir degere gectiginde (kesim sonu) start_recording() cagrilir. Testere yuzeyi gorunur hale geldiginde kayit baslar (Phase 20 D-03 ile uyumlu).
- **D-04:** Worker'lardaki mevcut write_async() cagrilari schema ile tam uyumlu -- detection_events ve wear_history tablolarinin tum sutunlari dogru eslestirilmis.
- **D-05:** Traceability alanlari (kesim_id, makine_id, serit_id, malzeme_cinsi) VisionService tarafindan CameraResultsStore'a yazilir, worker'lar oradan okuyup DB'ye kaydeder. DataProcessingPipeline zaten bu degerleri uretiyor.
- **D-06:** image_path ve edge_pixel_count alanlari da Phase 22'de doldurulacak -- worker'lar zaten annotated frame kaydediyor ve edge pixel hesapliyor, bu degerleri DB'ye de yazacaklar.
- **D-07:** VisionService polling/recording hatalarinda: logla ve devam et. Hata loglanir, bir sonraki polling cycle'da tekrar dener. VisionService thread'i olmez, ana dongu etkilenmez.
- **D-08:** Mevcut izolasyon yeterli: _init_camera() try/except ile sarili (baslama hatasi ana uygulamayi durdurmaz), worker DB hatalari loglanip atlaniyor, DataProcessingPipeline kamera koduyla dogrudan temas etmiyor.
- **D-09:** Shutdown sirasi: VisionService once durdurulur (recording tetiklemesi kesilir), sonra DetectionWorker ve LDCWorker (son cycle tamamlanir), sonra CameraService. Orchestrator ustten asagiya kapanir.
- **D-10:** Worker'lar durdurulurken mevcut cycle tamamlanir ve son DB write'lar yapilir (flush sonra dur). SQLiteService kendi shutdown'unda da flush yapiyor -- cift katmanli veri koruma.

### Claude's Discretion
- VisionService polling intervali (testere_durumu kontrol sikligi)
- CameraResultsStore'a testere_durumu yazma yeri (DataProcessingPipeline'in hangi noktasinda)
- Recording durdurma zamanlama mantigi (kesim sonu gecisinden kac saniye sonra stop)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | Tespit sonuclarinin (kirik, catlak, asinma) SQLite veritabanina kaydedilmesi (camera.db) | Workers already have write_async calls with correct SQL; need to fill NULL traceability fields and image_path/edge_pixel_count |
| DATA-03 | Kamera veritabani semasinin lifecycle'da config-driven olusturulmasi | ALREADY COMPLETE in Phase 19 -- camera.db created in _init_camera() with SCHEMA_CAMERA_DB |
</phase_requirements>

## Architecture Patterns

### Current System Architecture (Relevant Components)

```
ApplicationLifecycle (lifecycle.py)
  |
  +-- _init_camera()  [line 383-450]
  |     +-- SQLiteService("camera.db")  --> self.db_services['camera']
  |     +-- CameraResultsStore()        --> self.camera_results_store
  |     +-- CameraService(config, store) --> self.camera_service
  |     +-- DetectionWorker(config, store, camera_svc, db_service) --> self.detection_worker
  |     +-- LDCWorker(config, store, camera_svc, db_service) --> self.ldc_worker
  |     +-- [NEW] VisionService(config, store, camera_svc) --> self.vision_service
  |
  +-- _init_data_pipeline() [line 452-470]
  |     +-- DataProcessingPipeline(config, ..., camera_results_store)
  |           |
  |           +-- _processing_loop() [10 Hz]
  |                 +-- [NEW] Write testere_durumu + traceability to CameraResultsStore
  |
  +-- stop() [line 150-231]
        +-- [NEW] VisionService.stop() FIRST
        +-- DetectionWorker.stop() + join
        +-- LDCWorker.stop() + join
        +-- CameraService.stop()
        +-- ... (data pipeline, IoT, SQLite flush)
```

### Data Flow Pattern (Phase 22 Addition)

```
DataProcessingPipeline (10 Hz async loop)
  |
  |-- (existing) Read Modbus --> raw_data.testere_durumu, raw_data.makine_id, etc.
  |-- (existing) CuttingTracker.update() --> kesim_id
  |-- [NEW] CameraResultsStore.update_batch({
  |           "testere_durumu": raw_data.testere_durumu,
  |           "kesim_id": kesim_id,
  |           "makine_id": raw_data.makine_id,
  |           "serit_id": raw_data.serit_id,
  |           "malzeme_cinsi": raw_data.malzeme_cinsi
  |         })
  |
  v
CameraResultsStore (thread-safe dict)
  |
  +-- VisionService reads "testere_durumu" (polling)
  |     |-- Detects CUTTING -> non-CUTTING transition
  |     |-- Calls camera_service.start_recording()
  |     |-- After delay, calls camera_service.stop_recording()
  |
  +-- DetectionWorker reads traceability fields for DB writes
  |     |-- "kesim_id", "makine_id", "serit_id", "malzeme_cinsi"
  |     |-- Writes to detection_events with actual values (not None)
  |
  +-- LDCWorker reads traceability fields for DB writes
        |-- "kesim_id", "makine_id", "serit_id", "malzeme_cinsi"
        |-- Writes to wear_history with actual values (not None)
```

### Pattern 1: Daemon Thread Worker (Established Pattern)

**What:** VisionService follows the exact same daemon thread pattern as DetectionWorker and LDCWorker.
**When to use:** For any long-running background task that must not block the asyncio event loop.

```python
# Source: src/services/camera/detection_worker.py (lines 29-70)
class VisionService(threading.Thread):
    def __init__(self, config, results_store, camera_service):
        super().__init__(daemon=True, name="vision-service")
        self._stop_event = threading.Event()
        # ... config, store, service refs

    def run(self):
        while not self._stop_event.is_set():
            try:
                # poll testere_durumu from store
                # trigger recording on state transition
            except Exception:
                logger.warning("VisionService error — continuing", exc_info=True)
            self._stop_event.wait(self._polling_interval)

    def stop(self):
        self._stop_event.set()
```

### Pattern 2: CameraResultsStore Bridge (Established Pattern)

**What:** Data flows between components ONLY through CameraResultsStore. No direct cross-thread references.
**When to use:** Always, for any inter-thread data sharing in the camera subsystem.

```python
# Source: src/services/camera/results_store.py
# WRITER (DataProcessingPipeline, in asyncio thread):
self.camera_results_store.update_batch({
    "testere_durumu": raw_data.testere_durumu,
    "kesim_id": kesim_id,
    "makine_id": raw_data.makine_id,
    "serit_id": raw_data.serit_id,
    "malzeme_cinsi": raw_data.malzeme_cinsi,
})

# READER (VisionService, in daemon thread):
testere_durumu = self._results_store.get("testere_durumu", 0)

# READER (DetectionWorker, in daemon thread):
kesim_id = self._results_store.get("kesim_id")
makine_id = self._results_store.get("makine_id")
```

### Pattern 3: SQLiteService write_async (Established Pattern)

**What:** Non-blocking DB writes via a queue. Returns True if queued, False if queue full.
**When to use:** All DB writes from background threads.

```python
# Source: src/services/database/sqlite_service.py (lines 333-360)
# Worker writes detection event:
ok = self._db_service.write_async(
    "INSERT INTO detection_events "
    "(timestamp, event_type, confidence, count, image_path, "
    "kesim_id, makine_id, serit_id, malzeme_cinsi) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (now, "broken_tooth", confidence, count,
     image_path, kesim_id, makine_id, serit_id, malzeme_cinsi),
)
if not ok:
    logger.warning("DB write failed -- event dropped")
```

### Anti-Patterns to Avoid
- **Direct cross-thread field access:** Never read another thread's instance variables directly. Always go through CameraResultsStore.
- **Blocking the asyncio loop:** VisionService must be a daemon thread, NOT an asyncio task.
- **Silent failure in lifecycle:** _init_camera() already wraps in try/except; do not add additional exception swallowing that would hide real errors.

## VisionService Design Research

### Polling Interval (Claude's Discretion)

**Recommendation: 0.5 seconds (2 Hz)**

Rationale:
- DataProcessingPipeline runs at 10 Hz, so testere_durumu updates every 100ms
- VisionService only needs to detect state *transitions* (CUTTING -> non-CUTTING)
- A cutting session typically lasts minutes; 0.5s latency for recording trigger is negligible
- Lower CPU overhead than matching the 10 Hz pipeline rate
- Same order of magnitude as DetectionWorker's 2.0s interval

### Recording Trigger Logic (D-03)

Per D-03: "testere_durumu 3'den farkli bir degere gectiginde (kesim sonu) start_recording() cagrilir"

The state machine:
```
TesereDurumu enum:
  BOSTA = 0
  HIDROLIK_AKTIF = 1
  SERIT_MOTOR = 2
  KESIYOR = 3          <-- CUTTING state
  KESIM_BITTI = 4      <-- Cutting completed (transition target)
  SERIT_YUKARI = 5     <-- Saw moving up (blade surface visible)
  MALZEME_BESLEME = 6
```

Transition detection:
```python
prev_durumu = self._prev_testere_durumu
curr_durumu = self._results_store.get("testere_durumu", 0)

# Cutting ended -> start recording (blade surface visible)
if prev_durumu == 3 and curr_durumu != 3:
    self._camera_service.start_recording()
    self._recording_start_time = time.monotonic()
```

### Recording Stop Timing (Claude's Discretion)

**Recommendation: 10 seconds after recording starts**

Rationale:
- Recording captures blade surface after cutting ends (D-03)
- DetectionWorker runs every 2s, LDCWorker every 5s
- 10 seconds ensures at least 5 detection cycles and 2 LDC cycles complete
- Matches the "record then detect" pattern from REQUIREMENTS.md Out of Scope section
- Simple timer approach, no complex state tracking needed

```python
# In VisionService run loop:
if self._is_recording:
    elapsed = time.monotonic() - self._recording_start_time
    if elapsed >= self._recording_duration:
        self._camera_service.stop_recording()
        self._is_recording = False
```

### Traceability Field Flow (D-05)

**DataProcessingPipeline writes to CameraResultsStore:**

Where in the pipeline: After `_process_raw_data()` returns `processed_data`, before `_save_to_databases()`. This is the ideal point because:
1. `raw_data` has all sensor values including `testere_durumu`, `makine_id`, `serit_id`, `malzeme_cinsi`
2. `processed_data.cutting_session_id` (kesim_id) is already calculated by CuttingTracker
3. It's inside the same try/except as the rest of the processing loop

```python
# In DataProcessingPipeline._processing_loop(), after line ~177:
# Store for GUI access
self._last_processed_data = processed_data

# [NEW] Write camera-relevant fields to CameraResultsStore
if self.camera_results_store is not None:
    try:
        self.camera_results_store.update_batch({
            "testere_durumu": raw_data.testere_durumu,
            "kesim_id": processed_data.cutting_session_id,
            "makine_id": raw_data.makine_id,
            "serit_id": raw_data.serit_id,
            "malzeme_cinsi": raw_data.malzeme_cinsi,
        })
    except Exception as e:
        logger.warning(f"CameraResultsStore update failed: {e}")
```

## DB Write Integration Research

### Current Worker DB Write Calls (D-04, D-06)

**DetectionWorker** (detection_worker.py, lines 210-233):
```python
# Currently writes:
(now, "broken_tooth", broken_confidence, broken_count,
 None,  # image_path -- NEEDS FILLING
 None,  # kesim_id -- NEEDS FILLING
 None,  # makine_id -- NEEDS FILLING
 None,  # serit_id -- NEEDS FILLING
 None)  # malzeme_cinsi -- NEEDS FILLING
```

**LDCWorker** (ldc_worker.py, lines 158-168):
```python
# Currently writes:
(now, wear_percentage, health_score,
 None,  # edge_pixel_count -- NEEDS FILLING
 None,  # image_path -- NEEDS FILLING
 None,  # kesim_id -- NEEDS FILLING
 None,  # makine_id -- NEEDS FILLING
 None,  # serit_id -- NEEDS FILLING
 None)  # malzeme_cinsi -- NEEDS FILLING
```

### Fields to Fill

| Field | Source | Implementation |
|-------|--------|----------------|
| `kesim_id` | CameraResultsStore.get("kesim_id") | Read from store before DB write |
| `makine_id` | CameraResultsStore.get("makine_id") | Read from store before DB write |
| `serit_id` | CameraResultsStore.get("serit_id") | Read from store before DB write |
| `malzeme_cinsi` | CameraResultsStore.get("malzeme_cinsi") | Read from store before DB write |
| `image_path` (DetectionWorker) | `_save_annotated_frame()` return value | Modify _save_annotated_frame to return path |
| `image_path` (LDCWorker) | Recording path + "ldc/" subdirectory | Save edge image to recording dir, return path |
| `edge_pixel_count` (LDCWorker) | Contour analysis in `_compute_wear()` | Return edge pixel count from contour ys array |

### image_path Population (D-06)

**DetectionWorker:** The `_save_annotated_frame()` method already saves annotated frames to `recording_path/detected/det_YYYYMMDD_HHMMSS_ffffff.jpg`. Currently it returns None. Change it to return the saved path, and use that path in the DB write.

```python
# In DetectionWorker, modify _save_annotated_frame to return path:
def _save_annotated_frame(self, frame, broken_results, crack_results) -> str | None:
    # ... existing save logic ...
    try:
        cv2.imwrite(out_path, annotated)
        return out_path  # NEW: return the path
    except Exception:
        return None

# Then in the DB write:
image_path = self._save_annotated_frame(frame, broken_results, crack_results)
```

**LDCWorker:** Currently does not save edge images. Add a similar save mechanism to the recording directory.

### edge_pixel_count Population (D-06)

The `_compute_wear()` method in LDCWorker already computes contour Y coordinates. The `edge_pixel_count` can be derived from the total contour point count:

```python
# In _compute_wear(), before returning wear percentage:
ys = [pt[0][1] for c in contours for pt in c]
edge_pixel_count = len(ys)  # total edge pixels found
# Store or return this alongside wear_percentage
```

### Schema Compatibility Verification (D-04)

**detection_events table** (schemas.py, lines 265-278):
```sql
(timestamp TEXT, event_type TEXT, confidence REAL, count INTEGER,
 image_path TEXT, kesim_id INTEGER, makine_id INTEGER, serit_id INTEGER, malzeme_cinsi TEXT)
```

**DetectionWorker SQL** (detection_worker.py, lines 213-217):
```sql
INSERT INTO detection_events
(timestamp, event_type, confidence, count, image_path, kesim_id, makine_id, serit_id, malzeme_cinsi)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
```
**Result: EXACT MATCH** -- column names and order align perfectly.

**wear_history table** (schemas.py, lines 285-298):
```sql
(timestamp TEXT, wear_percentage REAL, health_score REAL, edge_pixel_count INTEGER,
 image_path TEXT, kesim_id INTEGER, makine_id INTEGER, serit_id INTEGER, malzeme_cinsi TEXT)
```

**LDCWorker SQL** (ldc_worker.py, lines 159-164):
```sql
INSERT INTO wear_history
(timestamp, wear_percentage, health_score, edge_pixel_count, image_path, kesim_id, makine_id, serit_id, malzeme_cinsi)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
```
**Result: EXACT MATCH** -- column names and order align perfectly.

## Lifecycle Integration Research

### Current _init_camera() (lifecycle.py, lines 383-450)

The current initialization already:
1. Checks `camera.enabled` config guard (line 393-395)
2. Creates camera.db SQLiteService (lines 401-410)
3. Creates CameraResultsStore (line 419)
4. Creates CameraService and calls start() (lines 422-424)
5. Creates DetectionWorker with db_service (lines 427-435)
6. Creates LDCWorker with db_service (lines 437-446)
7. Wraps everything in try/except (lines 448-450)

**What needs to be added:**
```python
# After LDCWorker creation (line 446), add:
from src.services.camera.vision_service import VisionService
self.vision_service = VisionService(
    camera_config, self.camera_results_store, self.camera_service
)
self.vision_service.start()  # Thread.start()
logger.info("  Vision service started")
```

### Current Shutdown Sequence (lifecycle.py, lines 150-231)

Current order (lines 181-193):
```python
# 0.5. Stop camera threads
if self.detection_worker:
    self.detection_worker.stop()
    self.detection_worker.join(timeout)
if self.ldc_worker:
    self.ldc_worker.stop()
    self.ldc_worker.join(timeout)
if self.camera_service:
    await self.camera_service.stop()
```

**Per D-09, VisionService must stop FIRST:**
```python
# 0.5. Stop camera threads (top-down: orchestrator first)
if self.vision_service:      # NEW
    self.vision_service.stop()
    self.vision_service.join(timeout)
if self.detection_worker:
    self.detection_worker.stop()
    self.detection_worker.join(timeout)
if self.ldc_worker:
    self.ldc_worker.stop()
    self.ldc_worker.join(timeout)
if self.camera_service:
    await self.camera_service.stop()
```

### Instance Variable Registration

In `__init__()` (line 87-90), add:
```python
self.vision_service = None  # NEW
```

## Error Isolation Research (D-07, D-08)

### Existing Isolation Layers

1. **_init_camera() try/except** (lifecycle.py, line 448): Catches any exception during camera initialization. If VisionService creation fails, application continues.

2. **Worker DB write guard** (detection_worker.py, line 211): `if self._db_service:` -- only writes when db_service is provided.

3. **write_async queue full** (sqlite_service.py, line 355-360): Returns False when queue is full, logs warning. Caller checks return and logs but continues.

4. **DataProcessingPipeline isolation** (data_processor.py, line 238-241): Main processing loop has try/except that catches all exceptions, logs them, increments error counter, and continues.

5. **CameraResultsStore thread safety** (results_store.py): All operations under `threading.Lock()`. Even if one thread crashes, the store remains consistent.

### VisionService Error Pattern

```python
def run(self):
    while not self._stop_event.is_set():
        try:
            # ... polling and recording logic ...
        except Exception:
            logger.warning("VisionService cycle error", exc_info=True)
            # D-07: log and continue, don't die
        self._stop_event.wait(self._polling_interval)
```

This matches the existing pattern in DetectionWorker/LDCWorker where the main loop wraps each cycle in try/except and continues on error.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Thread-safe state sharing | Custom locks per field | CameraResultsStore | Already built, battle-tested, used by all camera components |
| Async DB writes | Direct sqlite3 calls from threads | SQLiteService.write_async() | Handles WAL mode, batch commits, queue overflow, schema migration |
| State transition detection | Complex state machine | Simple prev/curr comparison | Only one transition matters (CUTTING -> non-CUTTING) |
| Daemon thread lifecycle | Custom thread management | threading.Thread(daemon=True) + Event | Established project pattern, works with ApplicationLifecycle.stop() |

## Common Pitfalls

### Pitfall 1: Race Condition Between VisionService and CameraService

**What goes wrong:** VisionService calls start_recording() but CameraService.start() hasn't completed yet (not running).
**Why it happens:** Startup order within _init_camera() -- CameraService.start() is async and might not fully initialize before VisionService begins polling.
**How to avoid:** CameraService.start_recording() already returns False when `not self._is_running` (camera_service.py, line 375-376). VisionService should check return value and log but not crash.
**Warning signs:** Recording never starts despite state transitions occurring.

### Pitfall 2: Stale Traceability Data in CameraResultsStore

**What goes wrong:** Worker reads kesim_id/makine_id from CameraResultsStore, but DataProcessingPipeline hasn't written yet (first cycle, or pipeline stopped).
**Why it happens:** Workers and pipeline run on different threads at different rates. Store might have stale or None values.
**How to avoid:** Workers should treat None traceability values as acceptable (schema allows NULLs). Do not crash on None -- pass it through to the INSERT as-is.
**Warning signs:** First few DB entries after startup have NULL traceability fields.

### Pitfall 3: Recording Stop Race with Shutdown

**What goes wrong:** VisionService is in the middle of a recording when shutdown begins. D-09 says VisionService stops first, but recording might not be flushed.
**Why it happens:** VisionService.stop() sets the event, but stop_recording() call might not happen before thread exits.
**How to avoid:** In VisionService.stop() or run() cleanup, check if recording is active and call stop_recording() before exiting.
**Warning signs:** Incomplete recordings (partial frame sets) in recordings directory.

### Pitfall 4: DataProcessingPipeline CameraResultsStore Write Overhead

**What goes wrong:** Writing to CameraResultsStore at 10 Hz adds lock contention.
**Why it happens:** CameraResultsStore uses a single threading.Lock for all operations. 10 Hz writes from pipeline + reads from 3 camera threads = potential contention.
**How to avoid:** Use update_batch() for all fields in a single lock acquisition (already the recommended pattern). Lock duration is microseconds for dict update -- 10 Hz is well within tolerance.
**Warning signs:** Pipeline cycle time warnings exceeding target interval.

### Pitfall 5: Shutdown Order SQLiteService Flush

**What goes wrong:** Workers write final DB entries during shutdown, but SQLiteService is already stopped.
**Why it happens:** Current shutdown order stops workers (line 182-189) BEFORE SQLiteService (line 215-217). This is actually correct -- workers flush during their join(), and SQLiteService does final batch commit in _writer_loop() before exiting.
**How to avoid:** No change needed. Current order is correct: workers stop -> final write_async calls enter queue -> SQLiteService stop -> final batch flush -> close.
**Warning signs:** Lost DB entries from final detection/wear cycles.

## Code Examples

### VisionService Core Structure

```python
# Source: Following established pattern from detection_worker.py + ldc_worker.py
class VisionService(threading.Thread):
    """Orchestrates camera recording based on testere_durumu state transitions.

    Polls CameraResultsStore for testere_durumu changes. When cutting
    ends (KESIYOR -> any other state), triggers start_recording() on
    CameraService. After a configurable duration, stops recording.
    """

    def __init__(self, config, results_store, camera_service):
        super().__init__(daemon=True, name="vision-service")
        self._results_store = results_store
        self._camera_service = camera_service
        self._stop_event = threading.Event()

        # Config
        self._polling_interval = 0.5  # 2 Hz polling
        self._recording_duration = 10.0  # seconds after cutting ends

        # State
        self._prev_testere_durumu = 0
        self._is_recording = False
        self._recording_start_time = 0.0

    def run(self):
        logger.info("VisionService started -- polling_interval=%.1fs", self._polling_interval)

        while not self._stop_event.is_set():
            try:
                self._poll_cycle()
            except Exception:
                logger.warning("VisionService cycle error", exc_info=True)

            self._stop_event.wait(self._polling_interval)

        # Cleanup: stop any active recording
        if self._is_recording:
            try:
                self._camera_service.stop_recording()
            except Exception:
                logger.warning("VisionService cleanup recording stop failed", exc_info=True)

    def _poll_cycle(self):
        curr = self._results_store.get("testere_durumu", 0)

        # Detect cutting-end transition (D-03)
        if self._prev_testere_durumu == 3 and curr != 3:
            if self._camera_service.start_recording():
                self._is_recording = True
                self._recording_start_time = time.monotonic()
                logger.info("Recording started -- cutting ended (durumu %d -> %d)", 3, curr)

        # Stop recording after duration
        if self._is_recording:
            elapsed = time.monotonic() - self._recording_start_time
            if elapsed >= self._recording_duration:
                self._camera_service.stop_recording()
                self._is_recording = False
                logger.info("Recording stopped -- duration %.1fs elapsed", elapsed)

        self._prev_testere_durumu = curr

    def stop(self):
        self._stop_event.set()
```

### DataProcessingPipeline CameraResultsStore Update

```python
# Source: data_processor.py, after line 177 (self._last_processed_data = processed_data)
# Write camera-relevant fields for VisionService and worker DB writes
if self.camera_results_store is not None:
    try:
        self.camera_results_store.update_batch({
            "testere_durumu": raw_data.testere_durumu,
            "kesim_id": processed_data.cutting_session_id,
            "makine_id": raw_data.makine_id,
            "serit_id": raw_data.serit_id,
            "malzeme_cinsi": raw_data.malzeme_cinsi,
        })
    except Exception as e:
        logger.warning(f"CameraResultsStore update failed: {e}")
```

### DetectionWorker DB Write Update (Filling NULLs)

```python
# Source: detection_worker.py, replacing lines 210-233
# Read traceability from store (D-05)
kesim_id = self._results_store.get("kesim_id")
makine_id = self._results_store.get("makine_id")
serit_id = self._results_store.get("serit_id")
malzeme_cinsi = self._results_store.get("malzeme_cinsi")

# Save annotated frame and get path (D-06)
image_path = self._save_annotated_frame(frame, broken_results, crack_results)

if self._db_service:
    if broken_count > 0:
        ok = self._db_service.write_async(
            "INSERT INTO detection_events "
            "(timestamp, event_type, confidence, count, image_path, "
            "kesim_id, makine_id, serit_id, malzeme_cinsi) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (now, "broken_tooth", broken_confidence, broken_count,
             image_path, kesim_id, makine_id, serit_id, malzeme_cinsi),
        )
```

### LDCWorker DB Write Update (Filling NULLs)

```python
# Source: ldc_worker.py, replacing lines 157-168
# Read traceability from store (D-05)
kesim_id = self._results_store.get("kesim_id")
makine_id = self._results_store.get("makine_id")
serit_id = self._results_store.get("serit_id")
malzeme_cinsi = self._results_store.get("malzeme_cinsi")

# D-06: edge_pixel_count from contour analysis
# (computed earlier in _compute_wear, returned alongside wear_percentage)

if self._db_service and wear_percentage is not None:
    ok = self._db_service.write_async(
        "INSERT INTO wear_history "
        "(timestamp, wear_percentage, health_score, edge_pixel_count, "
        "image_path, kesim_id, makine_id, serit_id, malzeme_cinsi) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (now, wear_percentage, health_score, edge_pixel_count,
         image_path, kesim_id, makine_id, serit_id, malzeme_cinsi),
    )
```

## Lifecycle _init_camera() Changes Summary

```python
# Source: lifecycle.py _init_camera() -- additions marked with [NEW]

async def _init_camera(self):
    # ... existing camera.enabled check ...
    # ... existing camera.db creation ...
    # ... existing CameraResultsStore creation ...
    # ... existing CameraService creation and start ...
    # ... existing DetectionWorker creation and start ...
    # ... existing LDCWorker creation and start ...

    # [NEW] VisionService orchestrator
    from src.services.camera.vision_service import VisionService
    self.vision_service = VisionService(
        camera_config, self.camera_results_store, self.camera_service
    )
    self.vision_service.start()  # Thread.start()
    logger.info("  Vision service started")
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | none (default discovery) |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01.1 | VisionService daemon thread lifecycle (start/stop) | unit | `pytest tests/test_vision_service.py -x` | Wave 0 |
| DATA-01.2 | VisionService detects cutting-end transition and triggers recording | unit | `pytest tests/test_vision_service.py::test_cutting_end_triggers_recording -x` | Wave 0 |
| DATA-01.3 | VisionService stops recording after duration | unit | `pytest tests/test_vision_service.py::test_recording_stops_after_duration -x` | Wave 0 |
| DATA-01.4 | DetectionWorker fills traceability fields from store | unit | `pytest tests/test_detection_worker.py::test_db_write_with_traceability -x` | Wave 0 |
| DATA-01.5 | LDCWorker fills traceability and edge_pixel_count from store | unit | `pytest tests/test_ldc_worker.py::test_db_write_with_traceability -x` | Wave 0 |
| DATA-01.6 | DataProcessingPipeline writes testere_durumu to CameraResultsStore | unit | `pytest tests/test_data_processor_camera.py -x` | Wave 0 |
| DATA-01.7 | camera.enabled=false skips all camera initialization | integration | `pytest tests/test_lifecycle_camera.py -x` | Wave 0 |
| DATA-01.8 | VisionService error does not crash (D-07) | unit | `pytest tests/test_vision_service.py::test_error_isolation -x` | Wave 0 |
| DATA-01.9 | Shutdown order: VisionService -> Workers -> CameraService (D-09) | unit | `pytest tests/test_lifecycle_camera.py::test_shutdown_order -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_vision_service.py tests/test_detection_worker.py tests/test_ldc_worker.py -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_vision_service.py` -- covers DATA-01.1, DATA-01.2, DATA-01.3, DATA-01.8
- [ ] `tests/test_data_processor_camera.py` -- covers DATA-01.6
- [ ] `tests/test_lifecycle_camera.py` -- covers DATA-01.7, DATA-01.9
- [ ] Update `tests/test_detection_worker.py` -- add test_db_write_with_traceability (DATA-01.4)
- [ ] Update `tests/test_ldc_worker.py` -- add test_db_write_with_traceability (DATA-01.5)

## Open Questions

1. **VisionService recording_duration configurability**
   - What we know: 10 seconds is a reasonable default based on worker cycle times
   - What's unclear: Whether this should be in config.yaml or hardcoded
   - Recommendation: Hardcode as class constant initially (like _RETRY_DURATION in CameraService). Can be moved to config if users need to tune it.

2. **edge_pixel_count computation scope**
   - What we know: _compute_wear() in LDCWorker already computes contour Y coordinates (`ys` array)
   - What's unclear: Whether edge_pixel_count should be `len(ys)` (total contour points) or total non-zero pixels in the edge image
   - Recommendation: Use `len(ys)` (total contour points used in wear calculation) since that directly relates to the measurement quality.

3. **LDCWorker image_path saving**
   - What we know: DetectionWorker saves annotated frames; LDCWorker does not currently save edge images
   - What's unclear: Whether LDC edge images should be saved to `recording_path/ldc/` similar to `recording_path/detected/`
   - Recommendation: Save edge images to `recording_path/ldc/` during recording. Follow same pattern as DetectionWorker's _save_annotated_frame.

## Sources

### Primary (HIGH confidence)
- `src/core/lifecycle.py` -- direct reading of _init_camera() and stop() methods
- `src/services/camera/detection_worker.py` -- direct reading of DB write_async calls and thread pattern
- `src/services/camera/ldc_worker.py` -- direct reading of DB write_async calls and wear computation
- `src/services/camera/camera_service.py` -- direct reading of start_recording/stop_recording API
- `src/services/camera/results_store.py` -- direct reading of thread-safe store API
- `src/services/database/schemas.py` -- direct reading of SCHEMA_CAMERA_DB table definitions
- `src/services/processing/data_processor.py` -- direct reading of pipeline loop and camera_results_store usage
- `src/domain/enums.py` -- direct reading of TesereDurumu enum values
- `config/config.yaml` -- direct reading of camera configuration section
- `.planning/phases/22-lifecycle-db-integration/22-CONTEXT.md` -- phase decisions

### Secondary (MEDIUM confidence)
- `.planning/phases/19-foundation/19-CONTEXT.md` -- Phase 19 decisions about camera.db creation
- `.planning/phases/20-camera-capture/20-CONTEXT.md` -- Phase 20 decisions about recording API
- `.planning/phases/21-ai-detection-pipeline/21-CONTEXT.md` -- Phase 21 decisions about worker DB writes

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all components are existing project libraries (threading, sqlite3, existing services)
- Architecture: HIGH -- following established patterns from DetectionWorker/LDCWorker, direct code reading
- Pitfalls: HIGH -- identified from direct code analysis of existing error handling patterns
- VisionService design: HIGH -- simple state machine following established project patterns

**Research date:** 2026-03-26
**Valid until:** 2026-04-25 (stable -- internal project patterns, no external dependency changes)
