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
