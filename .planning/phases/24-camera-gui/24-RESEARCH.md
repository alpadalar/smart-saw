# Phase 24: Camera GUI - Research

**Researched:** 2026-03-26
**Domain:** PySide6 Qt6 GUI — camera page completion (live feed, detection panels, progress bars, thumbnails, sidebar)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** Live feed area (`camera_label`) shows annotated frame (kirik dis: red, catlak: blue bounding boxes). Raw frame is NOT shown.
**D-02:** DetectionWorker must write annotated JPEG bytes to CameraResultsStore under key `annotated_frame`. CameraController reads `annotated_frame` first; falls back to `latest_frame` if absent.
**D-03:** LDC edge detection overlay (wear ROI lines) is NOT shown — only broken/crack bounding boxes appear.
**D-04:** Wear percentage: color-gradient horizontal progress bar green (low wear = good) → yellow → red (high wear = bad). Within existing 300x120 `asinma_frame` alongside `lbl_wear_value`.
**D-05:** Health score: color-gradient horizontal progress bar red (low score = bad) → yellow → green (high score = good). Inverse direction from wear. Within existing 300x120 `saglik_frame` alongside `lbl_health_score`.
**D-06:** Existing numeric labels (`lbl_wear_value`, `lbl_health_score`) are KEPT — progress bar is added as supplementary visual.
**D-07:** Full convention audit of existing CameraController code: CameraResultsStore key compatibility, edge case handling, docstring format, logging pattern, type hints.
**D-08:** MainController camera integration (conditional import, sidebar button, stacked widget) is also in audit scope.
**D-09:** No unit tests for CameraController. Visual verification only. Existing 45 mock-based tests cover backend.

### Claude's Discretion

- Progress bar QFrame width and animation details
- Annotated frame fallback timing logic (when annotated not yet available)
- Scope of specific fixes during convention audit

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GUI-01 | Live camera feed on camera page (QTimer periodic update) | _update_frame() already exists at 500 ms; needs `annotated_frame` fallback |
| GUI-02 | Broken tooth detection results displayed (count, timestamp) | `lbl_broken_count`, `lbl_kirik_ts` widgets exist; `_update_stats()` already reads store |
| GUI-03 | Crack detection results displayed (count, timestamp) | `lbl_crack_count`, `lbl_catlak_ts` widgets exist; `_update_stats()` already reads store |
| GUI-04 | Wear percentage displayed on camera page | `lbl_wear_value` exists; progress bar widget to be added |
| GUI-05 | Saw health status displayed (percentage + status text + color) | `lbl_health_score`, `lbl_health_status` exist; progress bar and HealthCalculator color to be added |
| GUI-06 | Sidebar 5th nav button only when camera.enabled=true | Already implemented in main_controller.py:212-220; audit for correctness |
| GUI-07 | Last 4 saved frames displayed as thumbnails | `thumbnail_labels[]` and `_thumb_pixmaps` deque exist; wired to live frame, needs audit |
| GUI-08 | OK/alert icons per detection category | `lbl_kirik_status`, `lbl_catlak_status` with `_set_ok_style`/`_set_alert_style` exist |
| GUI-09 | Wear measurement visualization (overlay) | Progress bar IS the visualization per D-04/D-05; no additional overlay (D-03 bans LDC lines) |
</phase_requirements>

---

## Summary

Phase 24 completes a camera GUI that is already ~80% implemented. The existing `CameraController` (480 lines, `camera_controller.py`) has all structural elements: live feed label, thumbnail strip, broken/crack panels with OK/alert indicators, wear and health frames with numeric labels, and three QTimers (500/1000/2000 ms). The code reads from `CameraResultsStore.snapshot()` exclusively — no direct thread state.

Two concrete additions are required. First, DetectionWorker must write annotated JPEG bytes under `annotated_frame` key to the store, and CameraController's `_update_frame()` must prefer `annotated_frame` over `latest_frame`. Second, color-gradient progress bars must be added inside the existing `asinma_frame` (300x120) and `saglik_frame` (300x120) frames — wear bar goes green→yellow→red, health bar goes red→yellow→green.

A full convention audit (D-07/D-08) is the third deliverable: ensuring CameraResultsStore key names match what workers actually write, edge case handling (no camera, empty store), docstrings, logging patterns, and type hints conform to project conventions.

**Primary recommendation:** Implement annotated_frame pipeline, add progress bars using QProgressBar with setStyleSheet color-stop technique, then audit. No new widgets needed beyond progress bars — everything else is already wired.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | 6.9.2 | Qt6 widget framework | Already used project-wide; verified installed |
| PySide6.QtWidgets.QProgressBar | 6.9.2 | Gradient progress bar | Native Qt widget; no custom drawing needed |
| PySide6.QtCore.QTimer | 6.9.2 | Periodic polling (500/1000/2000 ms) | Already in use; pattern established |
| PySide6.QtGui.QImage / QPixmap | 6.9.2 | JPEG decode → pixmap display | Already in use in `_update_frame()` |
| cv2 (opencv-python-headless) | existing | Annotated frame drawing in DetectionWorker | Already used; headless variant avoids Qt symbol conflict |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| collections.deque | stdlib | Thumbnail ring buffer (maxlen=4) | Already in use for `_thumb_pixmaps` |
| logging | stdlib | Module-level logger | Per CONVENTIONS.md; already wired |

**No new packages required.** All dependencies are already installed and imported.

---

## Architecture Patterns

### Existing Project Structure (camera domain)
```
src/
├── gui/
│   ├── controllers/
│   │   ├── camera_controller.py     # Phase 24: audit + extend (480 lines)
│   │   └── main_controller.py       # Phase 24: audit conditional camera block
│   └── images/
│       ├── camera-icon2.svg         # Already exists — sidebar button icon
│       └── camera-icon-active.svg   # Active state icon
├── services/
│   └── camera/
│       ├── results_store.py         # snapshot() source of truth
│       ├── detection_worker.py      # Phase 24: add annotated_frame write
│       ├── ldc_worker.py            # No changes needed
│       └── health_calculator.py     # get_health_color() used by progress bar
```

### Pattern 1: QProgressBar with CSS Color Stops (Gradient Progress Bar)
**What:** QProgressBar styled with `::chunk` pseudo-element to create gradient-filled bars.
**When to use:** Wear percentage and health score visual indicators.
**Example:**
```python
# Wear bar: low wear = green (good), high wear = red (bad)
wear_bar = QProgressBar(self.asinma_frame)
wear_bar.setGeometry(15, 75, 270, 18)
wear_bar.setRange(0, 100)
wear_bar.setValue(0)
wear_bar.setTextVisible(False)
wear_bar.setStyleSheet("""
    QProgressBar {
        background-color: rgba(255, 255, 255, 20);
        border-radius: 9px;
        border: none;
    }
    QProgressBar::chunk {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 #22C55E,
            stop:0.5 #EAB308,
            stop:1 #EF4444
        );
        border-radius: 9px;
    }
""")
# Health bar: low health = red (bad), high health = green (good) — INVERSE
health_bar = QProgressBar(self.saglik_frame)
health_bar.setGeometry(15, 75, 270, 18)
health_bar.setRange(0, 100)
health_bar.setValue(0)
health_bar.setTextVisible(False)
health_bar.setStyleSheet("""
    QProgressBar {
        background-color: rgba(255, 255, 255, 20);
        border-radius: 9px;
        border: none;
    }
    QProgressBar::chunk {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 #EF4444,
            stop:0.5 #EAB308,
            stop:1 #22C55E
        );
        border-radius: 9px;
    }
""")
```
Update in `_update_health()`:
```python
if wear is not None:
    self.wear_bar.setValue(int(float(wear)))
if score is not None:
    self.health_bar.setValue(int(float(score)))
```

### Pattern 2: Annotated Frame Pipeline (DetectionWorker → CameraResultsStore → CameraController)
**What:** DetectionWorker draws bounding boxes with cv2, encodes as JPEG bytes, writes to store under `annotated_frame`. CameraController prefers `annotated_frame`, falls back to `latest_frame`.
**When to use:** Live feed display — enables real-time detection visualization.
**Example in DetectionWorker._save_annotated_frame() extension:**
```python
# After drawing annotated frame, also publish to store as JPEG bytes
import cv2
ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
if ok:
    self._results_store.update("annotated_frame", buf.tobytes())
```
**CameraController._update_frame() fallback:**
```python
snapshot = self.results_store.snapshot()
jpeg_bytes = snapshot.get("annotated_frame") or snapshot.get("latest_frame")
if not jpeg_bytes:
    return
```

### Pattern 3: QTimer Polling from CameraResultsStore
**What:** Three independent QTimers poll `results_store.snapshot()` at different rates. Each timer callback is try/except wrapped and logs errors with `exc_info=True`.
**Rates:**
- 500 ms — frame + thumbnails (`_update_frame`)
- 1000 ms — detection stats (`_update_stats`)
- 2000 ms — health/wear (`_update_health`)

### Pattern 4: Conditional Camera Integration in MainController
**What:** Camera button and page added to `nav_buttons[]` and `stackedWidget` ONLY when `camera_results_store is not None`. Import of `CameraController` is deferred inside the `if` block.
**Location:** `main_controller.py:211-220` (button), `main_controller.py:297-303` (page).
**Verified:** `camera-icon2.svg` exists at `src/gui/images/camera-icon2.svg`. Sidebar button at y=649 is the 5th button (after 165, 286, 407, 528).

### Anti-Patterns to Avoid
- **Direct thread field access:** Never read camera service fields directly. All data flows through `results_store.snapshot()`.
- **Calling cv2 or numpy inside the GUI thread:** Frame encoding for `annotated_frame` must happen inside DetectionWorker (background thread), not in CameraController.
- **Creating QTimer in wrong thread:** QTimers must be created in the GUI thread. `_setup_timers()` is called from `__init__()` which runs in the GUI thread — correct.
- **Using opencv-python (full):** Project requires `opencv-python-headless` to avoid Qt5/Qt6 symbol conflicts on Linux.
- **Using `.ui` file:** This project uses programmatic layout only. No `.ui` files.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Color gradient progress bar | Custom QPainter widget | QProgressBar + `::chunk` CSS gradient | Qt's native gradient stylesheet works perfectly |
| JPEG decode to pixmap | Manual byte manipulation | `QImage.loadFromData()` → `QPixmap.fromImage()` | Already in use; handles all JPEG edge cases |
| Thread-safe store reads | Direct dict access | `results_store.snapshot()` | Returns shallow copy; prevents race conditions |
| Health color logic | Inline if/elif chain | `HealthCalculator.get_health_color()` | Already implemented, tested, Turkish labels ready |

**Key insight:** The existing 480-line CameraController already implements the GUI structure correctly. This phase is about extending what exists, not rebuilding.

---

## Runtime State Inventory

> Not a rename/refactor/migration phase. This section is NOT applicable.

---

## Common Pitfalls

### Pitfall 1: `annotated_frame` Not Yet Written to Store
**What goes wrong:** `_update_frame()` reads `annotated_frame` from the store but DetectionWorker never writes it — live feed shows nothing (or falls back to undecorated `latest_frame` indefinitely).
**Why it happens:** `_save_annotated_frame()` currently saves to disk but does NOT call `self._results_store.update("annotated_frame", ...)`.
**How to avoid:** Add `cv2.imencode()` + `results_store.update("annotated_frame", ...)` inside `_save_annotated_frame()` unconditionally (not only when recording is active). The disk save can remain recording-gated; the store write should happen every detection cycle.
**Warning signs:** Camera label shows raw feed (no bounding boxes) despite detections being logged.

### Pitfall 2: 300x120 Frame Too Small for Both Label and Bar
**What goes wrong:** `lbl_wear_value` occupies y=45..100 (55px height). Adding an 18px bar below with margin leaves only ~5px — bar clips or overlaps label.
**Why it happens:** `asinma_frame` is 300x120 px; `lbl_wear_value` is at y=45, h=55. Bottom of label is y=100. Bar must fit between y=100 and y=115 (frame bottom with 5px margin).
**How to avoid:** Resize `lbl_wear_value` height from 55 → 35 px (keep y=45, h=35, so bottom = y=80). Place bar at y=82, h=18. Verify total is 82+18=100 < 120. Same math for `saglik_frame`.
**Warning signs:** Bar rendered outside parent frame boundary (invisible or clipping).

### Pitfall 3: Progress Bar Integer Truncation for Fractional Values
**What goes wrong:** `wear_percentage` from store is a float (e.g., 47.3). `QProgressBar.setValue()` takes int — calling `setValue(47.3)` raises TypeError.
**Why it happens:** Python strict int/float type enforcement.
**How to avoid:** Always `int(round(float(value)))` before `setValue()`. Keep numeric label showing the float with one decimal (`f"{float(wear):.1f}%"`).

### Pitfall 4: Timers Not Stopped on Window Close
**What goes wrong:** Linux segfault: "Timers cannot be stopped from another thread" when Python GC tries to clean up QTimer from wrong thread.
**Why it happens:** If `stop_timers()` is not called in `closeEvent()`, GC may destroy timers from the GC thread, not the GUI thread.
**How to avoid:** `stop_timers()` is already called in `main_controller.py:416-417`. Audit confirms it uses `hasattr` guard correctly.

### Pitfall 5: Sidebar Button Index Mismatch
**What goes wrong:** `_switch_page(4)` raises IndexError if `nav_buttons[4]` doesn't exist (camera disabled) or page index 4 is not in stackedWidget.
**Why it happens:** Both button and page are conditionally added — they must be added together or not at all.
**How to avoid:** The existing guard `if self.camera_results_store is not None` covers both button (line 212) and page (line 297). Audit confirms correct pairing.

### Pitfall 6: Convention Audit Scope Creep
**What goes wrong:** Audit touches more code than needed, breaking working functionality.
**Why it happens:** "Full audit" is open-ended.
**How to avoid:** Scope the audit to: (a) CameraResultsStore key names (store key vs. code key match), (b) edge case guards (None checks), (c) docstring format, (d) logging uses `%s` not f-string format for lazy evaluation. Do not rewrite working logic.

---

## Code Examples

Verified patterns from project codebase:

### Annotated Frame Encode and Store Publish (DetectionWorker)
```python
# Source: detection_worker.py _save_annotated_frame() — ADD this block
# After drawing bboxes onto `annotated` numpy array:
ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
if ok:
    self._results_store.update("annotated_frame", buf.tobytes())
```

### Annotated Frame Fallback in CameraController
```python
# Source: camera_controller.py _update_frame() — REPLACE the snapshot read
def _update_frame(self):
    """Poll latest/annotated frame from the store; update camera label + thumbnails."""
    try:
        snapshot = self.results_store.snapshot()
        jpeg_bytes = snapshot.get("annotated_frame") or snapshot.get("latest_frame")
        if not jpeg_bytes:
            return
        # ... rest of method unchanged ...
```

### Progress Bar Geometry Fitting in 300x120 Frame
```python
# Shrink existing value label: y=45, h=35 (was h=55)
self.lbl_wear_value.setGeometry(15, 45, 270, 35)

# Add bar below: y=83, h=18
self.wear_bar = QProgressBar(self.asinma_frame)
self.wear_bar.setGeometry(15, 83, 270, 18)
self.wear_bar.setRange(0, 100)
self.wear_bar.setValue(0)
self.wear_bar.setTextVisible(False)
```

### Store Keys Written by Backend Workers
```
CameraResultsStore key          Writer
-------------------------------------
latest_frame        bytes | None    CameraService (capture thread)
frame_count         int             CameraService
is_recording        bool            CameraService
recording_path      str | None      CameraService
fps_actual          float           CameraService
broken_count        int             DetectionWorker
broken_confidence   float           DetectionWorker
tooth_count         int             DetectionWorker
crack_count         int             DetectionWorker
crack_confidence    float           DetectionWorker
last_detection_ts   str (ISO)       DetectionWorker
annotated_frame     bytes | None    DetectionWorker (MISSING — to be added)
wear_percentage     float | None    LDCWorker
health_score        float           LDCWorker
health_status       str             LDCWorker
health_color        str (CSS hex)   LDCWorker
last_wear_ts        str (ISO)       LDCWorker
kesim_id            any             VisionService (via DataProcessingPipeline)
makine_id           any             VisionService
serit_id            any             VisionService
malzeme_cinsi       any             VisionService
testere_durumu      any             DataProcessingPipeline
```

### Convention Audit Checklist (D-07/D-08)
```
camera_controller.py:
  [ ] snapshot.get("latest_frame") → update to prefer "annotated_frame"
  [ ] Docstring format: Google-style with Args/Returns for public methods
  [ ] Logging: uses f-string inline; check if %s lazy format required
  [ ] Type hints: _thumb_pixmaps typed as deque[QPixmap] — already done
  [ ] Edge case: results_store is None guard? (passed in constructor, always set)
  [ ] Edge case: jpeg_bytes is empty bytes (not None) — `if not jpeg_bytes` handles both

main_controller.py:
  [ ] camera_results_store guard at line 212 and 297 — correct pairing
  [ ] closeEvent at 416-417 calls camera_page.stop_timers() with hasattr guard
  [ ] nav_buttons[4] indexing in _switch_page(4) — confirmed button appended at 220
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw frame display in live feed | Annotated frame (bboxes drawn by DetectionWorker) | Phase 24 | Operator sees detections in real time |
| Text-only wear/health display | Numeric label + color progress bar | Phase 24 | Faster visual health assessment |

**No deprecated patterns in this phase.** All existing patterns (QTimer polling, QFrame layout, style constants) are the current standard for this project.

---

## Open Questions

1. **Annotated frame when recording is off**
   - What we know: `_save_annotated_frame()` currently only saves to disk when `recording_path` is set.
   - What's unclear: Should `annotated_frame` be written to the store even when NOT recording?
   - Recommendation: YES — write to store unconditionally every detection cycle. The store write is cheap (bytes copy). Disk write stays recording-gated. Operator needs the visual regardless of recording state.

2. **Thumbnail source: live feed vs. recorded frames**
   - What we know: Current `_update_frame()` adds the current live frame to `_thumb_pixmaps` at 500 ms. This shows frames from the live feed, not from the recorded/detected directory.
   - What's unclear: GUI-07 says "son kaydedilen frame thumbnail" — "last recorded frames." Should thumbnails come from the `detected/` directory (disk), or the live feed?
   - Recommendation: Keep current behavior (live feed thumbnails). Reading from disk adds filesystem I/O to the 500 ms timer callback. If the operator wants disk thumbnails, that is a future feature. D-07 covers this in audit scope.

3. **Frame size for asinma_frame / saglik_frame**
   - What we know: Both frames are 300x120. Label heights need reduction to fit progress bar.
   - What's unclear: Whether the 300x120 is user-facing fixed or can be expanded.
   - Recommendation: Keep 300x120. Resize `lbl_wear_value` from h=55 to h=35. Bar at y=83, h=18. This fits cleanly.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PySide6 | GUI framework | Yes | 6.9.2 | — |
| PySide6.QtWidgets.QProgressBar | Progress bars | Yes | 6.9.2 (verified) | — |
| opencv-python-headless | Annotated frame encoding | Yes (inferred from prior phases) | existing | — |
| pytest | Test verification | Yes | 9.0.2 | — |

**No missing dependencies.** All required components are installed and verified.

---

## Validation Architecture

> `workflow.nyquist_validation` key absent from config.json — treating as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml (inferred from project conventions) |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GUI-01 | Live feed prefers `annotated_frame` key | manual-only | — | N/A |
| GUI-02 | Broken count/timestamp displayed | manual-only | — | N/A |
| GUI-03 | Crack count/timestamp displayed | manual-only | — | N/A |
| GUI-04 | Wear bar renders with correct color direction | manual-only | — | N/A |
| GUI-05 | Health bar renders with inverse color direction | manual-only | — | N/A |
| GUI-06 | Sidebar button conditional on camera.enabled | manual-only | — | N/A |
| GUI-07 | 4 thumbnails visible | manual-only | — | N/A |
| GUI-08 | OK/alert icon changes on detection | manual-only | — | N/A |
| GUI-09 | Wear visualization (progress bar) visible | manual-only | — | N/A |
| D-02 backend | DetectionWorker writes `annotated_frame` to store | unit | `python -m pytest tests/test_detection_worker.py -x -q` | Yes (existing, needs extension) |

**Per D-09:** No new GUI unit tests. Existing backend tests cover camera pipeline.

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_detection_worker.py -x -q` (for annotated_frame change)
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green + visual inspection before `/gsd:verify-work`

### Wave 0 Gaps
None — existing test infrastructure covers all automated test requirements. GUI portions are visual-only per D-09.

---

## Sources

### Primary (HIGH confidence)
- `src/gui/controllers/camera_controller.py` — Full implementation read; 480 lines; exact widget geometry, timer intervals, store keys confirmed
- `src/gui/controllers/main_controller.py` — Full implementation read; conditional camera block at lines 212-220, 297-303, 416-417 confirmed
- `src/services/camera/results_store.py` — Full API read; `snapshot()`, `update()`, `update_batch()`, `get()` confirmed
- `src/services/camera/detection_worker.py` — Full implementation read; `_save_annotated_frame()` confirmed does NOT write to store; `annotated_frame` key absent
- `src/services/camera/ldc_worker.py` — Full implementation read; publishes `wear_percentage`, `health_score`, `health_status`, `health_color`
- `src/services/camera/health_calculator.py` — Full implementation read; `get_health_color()`, `get_health_status()` thresholds confirmed
- `.planning/codebase/CONVENTIONS.md` — Naming, docstring, logging conventions confirmed
- `.planning/codebase/ARCHITECTURE.md` — Concurrency model confirmed

### Secondary (MEDIUM confidence)
- `src/gui/controllers/control_panel_controller.py` — QProgressBar import pattern confirmed; QFrame/QLabel layout pattern confirmed
- `.planning/phases/24-camera-gui/24-CONTEXT.md` — All locked decisions; geometry constraints from existing code

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PySide6 6.9.2 verified installed; QProgressBar confirmed available
- Architecture: HIGH — All source files read directly; exact line numbers confirmed
- Pitfalls: HIGH — Identified from reading actual code; annotated_frame gap confirmed by grep
- Convention audit scope: MEDIUM — Based on conventions doc; actual violations require code reading at implementation time

**Research date:** 2026-03-26
**Valid until:** 2026-04-25 (stable PySide6 API; project conventions stable)
