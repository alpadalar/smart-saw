---
phase: 24
phase_name: Camera GUI
status: draft
created: 2026-03-26
tool: none
framework: PySide6 (Qt6)
design_system: none — programmatic Qt CSS (project-wide pattern)
---

# UI-SPEC: Phase 24 — Camera GUI

## Purpose

Visual and interaction contract for the PySide6 camera page. Consumed by the planner
(task decomposition), executor (implementation source of truth), and auditor
(retroactive conformance check). All design decisions are prescriptive.

---

## 1. Design System

**Tool:** none. This project uses PySide6 with inline Qt stylesheet strings.
No shadcn, no Tailwind, no web component library. Not applicable.

**Component library:** PySide6 6.9.2 — `QWidget`, `QFrame`, `QLabel`,
`QProgressBar`, `QTimer`, `QPixmap`, `QImage`.

**Layout approach:** Programmatic pixel geometry (`setGeometry(x, y, w, h)`).
No `.ui` files. All widgets are children of `QWidget` or `QFrame` parent objects.
Source: RESEARCH.md §Architecture Patterns.

---

## 2. Spacing

**Scale:** 8-point grid where possible. Fixed-pixel positions are dictated by the
existing 1528×1080 content area and the already-deployed panel geometries.
Do not break existing geometry without explicit justification.

| Token | Value | Use |
|-------|-------|-----|
| spacing-xs | 8 px | Inner label margins from frame edge |
| spacing-sm | 10 px | Thumbnail gap between cells |
| spacing-md | 15 px | Standard label x-offset inside frames |
| spacing-lg | 20 px | Frame x/y offset from page edges |
| spacing-xl | 48 px | Camera feed top offset (y=48 for feed inside kamera_frame) |
| touch-target | 110 px height | Sidebar nav buttons (already deployed: h=110) |

Source: Extracted from `camera_controller.py` geometry values; confirmed in
`main_controller.py` sidebar button at `setGeometry(26, 649, 355, 110)`.

---

## 3. Typography

**Font family:** `Plus Jakarta Sans` — all text elements, all weights.
This is the project-wide font; do not introduce any other family.
Source: `_TITLE_STYLE`, `_VALUE_STYLE`, `_SUBTITLE_STYLE`, `_INFO_STYLE`
constants in `camera_controller.py`.

**Sizes (4 levels):**

| Level | Size | Weight | Line-height | Usage |
|-------|------|--------|-------------|-------|
| value | 32 px | bold (700) | 1.2 | Large numeric values (`lbl_wear_value`, `lbl_health_score`, `lbl_health_status`) |
| status | 28 px | bold (700) | 1.2 | OK/alert indicator labels (`lbl_kirik_status`, `lbl_catlak_status`) |
| title | 22 px | bold (700) | 1.3 | Panel section titles (`_TITLE_STYLE`) |
| subtitle | 16 px | medium (500) | 1.5 | Field name labels (`_SUBTITLE_STYLE`) |
| info | 14 px | regular (400) | 1.5 | Timestamps, frame count, recording status (`_INFO_STYLE`) |

Note: 5 levels are used here rather than 4 because the status indicator at 28 px
is a semantically distinct level from the 32 px value display. This is an
existing established pattern — do not consolidate.

**Weights used:** regular (400), medium (500), bold (700). Only 3 are active.
Source: extracted from existing style constants.

---

## 4. Color

### Surface Colors (60/30/10 split)

| Role | Value | Coverage | Notes |
|------|-------|----------|-------|
| dominant (page bg) | `#0A0E1A` | ~60% | Full page background via `self.setStyleSheet("background-color: #0A0E1A;")` |
| secondary (panel frames) | `rgba(6, 11, 38, 240)` → `rgba(26, 31, 55, 0)` gradient | ~30% | All `QFrame` panels — `_FRAME_STYLE` gradient |
| feed/thumb bg | `#1A1F37` | ~10% | Camera label and thumbnail placeholder background |

### Text Colors

| Role | Value | Usage |
|------|-------|-------|
| primary text | `#F4F6FC` | All titles, values, status labels |
| muted text | `rgba(244, 246, 252, 151)` | Subtitle labels (`_SUBTITLE_STYLE`) |
| dim text | `rgba(244, 246, 252, 120)` | Info labels (`_INFO_STYLE`) |
| placeholder text | `rgba(244, 246, 252, 60)` | Thumbnail cell placeholder numbers |
| camera waiting | `rgba(244, 246, 252, 80)` | `camera_label` "Kamera bekleniyor…" text |

### Semantic / Accent Colors

The 10% accent budget is reserved exclusively for:

| Accent | Value | Reserved For |
|--------|-------|--------------|
| ok-green | `#22C55E` | `_set_ok_style()` — status indicator when no detections (`✓ OK`) |
| alert-red | `#EF4444` | `_set_alert_style()` — status indicator when detections present (`✗ UYARI`); also the "high wear" end of the wear progress bar gradient |
| warn-yellow | `#EAB308` | Mid-stop of both progress bar gradients |
| health-green | `#22C55E` | "High health" end of health progress bar gradient (same token as ok-green) |

### Progress Bar Gradient Stops

**Wear bar** (low wear = good, high wear = bad — left to right):

```
stop:0   #22C55E   (0% — green, low wear, good)
stop:0.5 #EAB308   (50% — yellow, moderate)
stop:1   #EF4444   (100% — red, high wear, bad)
```

**Health bar** (low health = bad, high health = good — left to right, inverse):

```
stop:0   #EF4444   (0% — red, low health, bad)
stop:0.5 #EAB308   (50% — yellow, moderate)
stop:1   #22C55E   (100% — green, high health, good)
```

Source: CONTEXT.md D-04, D-05; RESEARCH.md Pattern 1.

### HealthCalculator Color Thresholds (status text only)

These colors are used for `lbl_health_status` text color only, via
`HealthCalculator.get_health_color()`. They are NOT used in progress bar gradients.

| Score range | CSS color | Turkish label |
|-------------|-----------|---------------|
| >= 80 | `#00FF00` | Sağlıklı |
| >= 60 | `#90EE90` | İyi |
| >= 40 | `#FFFF00` | Orta |
| >= 20 | `#FFA500` | Kritik |
| < 20 | `#FF0000` | Tehlikeli |

Source: `health_calculator.py` — `get_health_color()`, `get_health_status()`.

---

## 5. Page Layout

**Canvas:** 1528 × 1080 px (content area, child of `stackedWidget` at x=392).
**Sidebar:** 392 px wide — handled by MainController, not CameraController.

### Panel Grid

| Panel | Widget | x | y | w | h | Purpose |
|-------|--------|---|---|---|---|---------|
| kamera_frame | QFrame | 20 | 20 | 934 | 525 | Live camera feed |
| sirali_frame | QFrame | 20 | 555 | 934 | 170 | Sequential thumbnails (4 cells) |
| kirik_frame | QFrame | 970 | 20 | 538 | 350 | Broken-tooth detection |
| catlak_frame | QFrame | 970 | 385 | 538 | 350 | Crack detection |
| asinma_frame | QFrame | 20 | 740 | 300 | 120 | Wear percentage + progress bar |
| saglik_frame | QFrame | 340 | 740 | 300 | 120 | Health score + progress bar |
| durum_frame | QFrame | 660 | 740 | 300 | 120 | Health status text |

Source: `camera_controller.py` `_setup_ui()` — all geometries verified.

---

## 6. Component Specifications

### 6.1 Live Feed Label (`camera_label`)

- Parent: `kamera_frame`
- Geometry: `(10, 48, 914, 467)`
- Alignment: `Qt.AlignCenter`
- Waiting state text: `"Kamera bekleniyor…"` at `rgba(244,246,252,80)`, 16 px
- Waiting state bg: `#1A1F37`, border-radius 10 px
- Active state: pixmap scaled to label size with `Qt.KeepAspectRatio` + `Qt.SmoothTransformation`
- Frame source: `annotated_frame` key from store (preferred); fallback to `latest_frame`
- Update interval: 500 ms (`_frame_timer`)

### 6.2 Thumbnail Strip (`thumbnail_labels[]`)

- Count: 4 cells
- Cell size: 220 × 140 px
- Cell spacing: 10 px between cells
- Cell x-start: 20 px inside `sirali_frame`
- Cell y: 40 px inside `sirali_frame`
- Cell bg: `#1A1F37`, border-radius 8 px
- Empty state: cell shows its 1-based index number in `rgba(244,246,252,60)`, 12 px
- Source: live feed frames added at 500 ms rate via `_thumb_pixmaps` deque (maxlen=4)
- Ordering: deque position 0 = oldest, position 3 = most recent

### 6.3 Broken-Tooth Panel (`kirik_frame`)

Sub-labels (all inside kirik_frame):

| Widget | Geometry | Style | Content |
|--------|----------|-------|---------|
| lbl_kirik_title | (20, 15, 300, 30) | `_TITLE_STYLE` | "Kırık Diş Tespiti" |
| lbl_broken_name | (20, 60, 200, 22) | `_SUBTITLE_STYLE` | "Kırık Diş Sayısı" |
| lbl_broken_count | (20, 85, 200, 45) | `_VALUE_STYLE` | integer string, default "0" |
| lbl_tooth_name | (20, 140, 200, 22) | `_SUBTITLE_STYLE` | "Toplam Diş Sayısı" |
| lbl_tooth_count | (20, 165, 200, 45) | `_VALUE_STYLE` | integer or "—", default "—" |
| lbl_kirik_ts_name | (20, 225, 200, 22) | `_SUBTITLE_STYLE` | "Son Tespit" |
| lbl_kirik_ts | (20, 250, 300, 30) | `_INFO_STYLE` | ISO timestamp or "—" |
| lbl_kirik_status | (20, 290, 200, 40) | dynamic | "✓ OK" or "✗ UYARI" |

Status indicator colors: ok-green (`#22C55E`) when `broken_count == 0`; alert-red (`#EF4444`) when `broken_count > 0`.

Update interval: 1000 ms (`_stats_timer`).

### 6.4 Crack Detection Panel (`catlak_frame`)

| Widget | Geometry | Style | Content |
|--------|----------|-------|---------|
| lbl_catlak_title | (20, 15, 300, 30) | `_TITLE_STYLE` | "Çatlak Tespiti" |
| lbl_crack_name | (20, 60, 200, 22) | `_SUBTITLE_STYLE` | "Çatlak Sayısı" |
| lbl_crack_count | (20, 85, 200, 45) | `_VALUE_STYLE` | integer string, default "0" |
| lbl_catlak_ts_name | (20, 145, 200, 22) | `_SUBTITLE_STYLE` | "Son Tespit" |
| lbl_catlak_ts | (20, 170, 300, 30) | `_INFO_STYLE` | ISO timestamp or "—" |
| lbl_catlak_status | (20, 220, 200, 40) | dynamic | "✓ OK" or "✗ UYARI" |

Status logic: ok-green when `crack_count == 0`; alert-red when `crack_count > 0`.

Update interval: 1000 ms (`_stats_timer`).

### 6.5 Wear Percentage Frame (`asinma_frame`) — EXTENDED

| Widget | Geometry | Style | Content |
|--------|----------|-------|---------|
| lbl_asinma_title | (15, 10, 270, 26) | `_TITLE_STYLE` | "Aşınma Yüzdesi" |
| lbl_wear_value | (15, 45, 270, **35**) | `_VALUE_STYLE` + AlignCenter | `f"{float(wear):.1f}%"` or "—" |
| wear_bar (NEW) | (15, **83**, 270, 18) | see below | QProgressBar, range 0–100 |

`lbl_wear_value` height is REDUCED from 55 px to 35 px to make room for the bar.
Bottom of label = y 45 + 35 = 80. Bar starts at y=83. Bar bottom = 83+18=101. Frame height=120. Margin=19 px. Fits cleanly.

**wear_bar stylesheet:**
```
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
```

`setTextVisible(False)`. Update: `wear_bar.setValue(int(round(float(wear))))`.

Update interval: 2000 ms (`_health_timer`).

### 6.6 Health Score Frame (`saglik_frame`) — EXTENDED

| Widget | Geometry | Style | Content |
|--------|----------|-------|---------|
| lbl_saglik_title | (15, 10, 270, 26) | `_TITLE_STYLE` | "Testere Sağlığı" |
| lbl_health_score | (15, 45, 270, **35**) | `_VALUE_STYLE` + AlignCenter | `f"{float(score):.1f}%"` or "—" |
| health_bar (NEW) | (15, **83**, 270, 18) | see below | QProgressBar, range 0–100 |

`lbl_health_score` height is REDUCED from 55 px to 35 px. Same math as wear frame.

**health_bar stylesheet:**
```
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
```

`setTextVisible(False)`. Update: `health_bar.setValue(int(round(float(score))))`.

Update interval: 2000 ms (`_health_timer`).

### 6.7 Health Status Frame (`durum_frame`)

Unchanged from existing implementation. `lbl_health_status` text color is
set dynamically from `HealthCalculator.get_health_color()` result (CSS hex string).
No progress bar in this frame.

### 6.8 Sidebar Camera Button

- Parent: `sidebarFrame` (in MainController)
- Geometry: `(26, 649, 355, 110)`
- Label: `"  Kamera"` (two leading spaces for icon separation)
- Icon: `camera-icon2.svg` at 80×80 px
- Active icon: `camera-icon-active.svg` (already exists)
- Style: same `nav_btn_style` as other 4 sidebar buttons
- Visibility: ONLY added when `camera_results_store is not None`
- Stack index: 4 (after control=0, positioning=1, sensor=2, tracking=3)

Source: `main_controller.py` lines 212–220, 297–303.

### 6.9 Frame/FPS Info Bar (bottom-right, unchanged)

| Widget | Geometry | Style | Content |
|--------|----------|-------|---------|
| lbl_frame_count | (1300, 1040, 200, 20) | `_INFO_STYLE` + AlignRight | `f"Kare: {frame_count}"` |
| lbl_recording | (1300, 1060, 200, 20) | `_INFO_STYLE` + AlignRight | `"Kayıt: Aktif"` or `"Kayıt: —"` |

---

## 7. Interaction Contracts

### 7.1 Frame Display States

| Store key | Condition | Displayed |
|-----------|-----------|-----------|
| `annotated_frame` key present and non-empty | Normal detection running | Annotated JPEG (bounding boxes visible) |
| `annotated_frame` absent or empty, `latest_frame` present | Detection not yet run | Raw JPEG (no boxes) |
| Both absent or empty | Camera not connected | "Kamera bekleniyor…" placeholder text |

Fallback logic (exact implementation):
```python
jpeg_bytes = snapshot.get("annotated_frame") or snapshot.get("latest_frame")
if not jpeg_bytes:
    return
```

### 7.2 Status Indicator State Machine

Each detection panel (broken, crack) has two states:

| State | Condition | Label text | Color |
|-------|-----------|------------|-------|
| OK | count == 0 or None | "✓ OK" | `#22C55E` (ok-green) |
| ALERT | count > 0 | "✗ UYARI" | `#EF4444` (alert-red) |

Transition: evaluated every 1000 ms in `_update_stats()`.

### 7.3 Progress Bar Value Updates

Both bars use `int(round(float(value)))` before `setValue()`. Null guard:
update bar only when value is not None.

```python
if wear is not None:
    self.wear_bar.setValue(int(round(float(wear))))
if score is not None:
    self.health_bar.setValue(int(round(float(score))))
```

### 7.4 Annotated Frame Write (DetectionWorker)

The executor must add this to `_save_annotated_frame()` in `detection_worker.py`,
executed unconditionally every detection cycle (not only when recording is active):

```python
ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
if ok:
    self._results_store.update("annotated_frame", buf.tobytes())
```

Disk write remains recording-gated. Store write is unconditional.

### 7.5 Timer Lifecycle

All three timers are stopped in `closeEvent` via `stop_timers()`.
Guard pattern: `hasattr(self, "_frame_timer") and self._frame_timer`.
This is already implemented at `main_controller.py:416-417` — audit confirms.

### 7.6 Sidebar Navigation

Page switching uses `_switch_page(4)`. This method unchecks all buttons, checks
`nav_buttons[index]`, and calls `stackedWidget.setCurrentIndex(index)`.
Camera button at `nav_buttons[4]` is only appended when camera is enabled —
index 4 is safe only in that code path.

---

## 8. Copywriting Contract

All copy is Turkish per project-wide convention.

### Panel Titles

| Panel | Title text |
|-------|-----------|
| Camera feed | "Kamera Görüntüsü" |
| Thumbnail strip | "Sıralı Görüntüler" |
| Broken-tooth | "Kırık Diş Tespiti" |
| Crack | "Çatlak Tespiti" |
| Wear | "Aşınma Yüzdesi" |
| Health score | "Testere Sağlığı" |
| Health status | "Testere Durumu" |
| Sidebar button | "  Kamera" |

### Field Labels

| Field | Label text |
|-------|-----------|
| Broken tooth count | "Kırık Diş Sayısı" |
| Total tooth count | "Toplam Diş Sayısı" |
| Last detection (both panels) | "Son Tespit" |
| Crack count | "Çatlak Sayısı" |

### State Copy

| State | Copy | Element |
|-------|------|---------|
| No detections | "✓ OK" | `lbl_kirik_status`, `lbl_catlak_status` |
| Detections found | "✗ UYARI" | `lbl_kirik_status`, `lbl_catlak_status` |
| Camera waiting | "Kamera bekleniyor…" | `camera_label` placeholder |
| No value yet | "—" | All numeric/timestamp labels when store is empty |
| Active recording | "Kayıt: Aktif" | `lbl_recording` |
| Not recording | "Kayıt: —" | `lbl_recording` |

### Health Status Labels (from HealthCalculator — do not change)

| Range | Turkish label |
|-------|--------------|
| >= 80 | "Sağlıklı" |
| >= 60 | "İyi" |
| >= 40 | "Orta" |
| >= 20 | "Kritik" |
| < 20 | "Tehlikeli" |

### Destructive Actions

None in this phase. The camera page is read-only (display only).
No confirmation dialogs required.

---

## 9. Bounding Box Rendering Contract

Bounding boxes are drawn by DetectionWorker using OpenCV before encoding to JPEG.
The camera_label renders the pre-annotated JPEG — no Qt painting of boxes.

| Detection type | Box color (BGR for cv2) | Notes |
|---------------|------------------------|-------|
| Broken tooth (kirik dis) | Red — `(0, 0, 255)` | D-01 from CONTEXT.md |
| Crack (catlak) | Blue — `(255, 0, 0)` | D-01 from CONTEXT.md |
| LDC wear ROI lines | NOT shown | D-03 from CONTEXT.md — explicitly excluded |

The executor must verify `detection_worker.py` draws boxes with these specific BGR
color values when encoding the annotated frame.

---

## 10. Convention Audit Scope

Per D-07 and D-08, the executor must audit (not rewrite) the following:

### camera_controller.py

| Check | Action |
|-------|--------|
| `snapshot.get("latest_frame")` in `_update_frame()` | Replace with annotated-frame fallback pattern (section 7.1) |
| Docstrings on public methods | Ensure Google-style with Args/Returns sections |
| Logging format strings | Replace f-string inline with `%s` lazy format where possible |
| Type hints completeness | Verify `_thumb_pixmaps: deque[QPixmap]` present (already exists) |
| Edge case: `jpeg_bytes` is empty bytes | `if not jpeg_bytes: return` handles both None and `b""` — confirm |
| `lbl_wear_value` height | Resize from 55 to 35 px (geometry change, not a logic change) |
| `lbl_health_score` height | Resize from 55 to 35 px |
| Add `wear_bar` QProgressBar | Insert after lbl_wear_value in `_setup_ui()` |
| Add `health_bar` QProgressBar | Insert after lbl_health_score in `_setup_ui()` |
| Update `_update_health()` | Add `self.wear_bar.setValue(...)` and `self.health_bar.setValue(...)` |

### main_controller.py

| Check | Action |
|-------|--------|
| `if self.camera_results_store is not None` guard at line 212 and 297 | Confirm correct pairing — both button and page must be in same guard |
| `closeEvent` at 416-417 | Confirm `hasattr` guard and `stop_timers()` call |
| `nav_buttons[4]` access in `_switch_page(4)` | Confirm only reachable when camera is enabled |

---

## 11. Registry Safety

**Not applicable.** This project uses no shadcn registry, no npm packages, no
third-party component registries. All UI is PySide6 stdlib + project-internal styles.

---

## 12. Pre-Population Sources

| Decision | Source |
|----------|--------|
| All panel geometry values | `camera_controller.py` — read directly |
| Font family: Plus Jakarta Sans | `_TITLE_STYLE`, `_VALUE_STYLE` etc. in `camera_controller.py` |
| Font sizes: 14/16/22/28/32 px | Extracted from style constants |
| Color palette: `#0A0E1A`, `#1A1F37`, `#F4F6FC` etc. | Extracted from style constants |
| Progress bar direction (D-04, D-05) | CONTEXT.md locked decisions |
| Annotated frame fallback (D-01, D-02) | CONTEXT.md locked decisions |
| No LDC overlay (D-03) | CONTEXT.md locked decision |
| No GUI unit tests (D-09) | CONTEXT.md locked decision |
| Gradient stop colors (#22C55E, #EAB308, #EF4444) | RESEARCH.md Pattern 1 |
| Progress bar geometry fit (lbl h=35, bar y=83 h=18) | RESEARCH.md Pitfall 2 |
| HealthCalculator thresholds | `health_calculator.py` — read directly |
| Sidebar geometry (y=649, w=355, h=110) | `main_controller.py` line 214 |
| camera-icon2.svg existence | `src/gui/images/` directory listing |
| Timer intervals (500/1000/2000 ms) | `camera_controller.py` `_setup_timers()` |
| Store key names | RESEARCH.md Store Keys Inventory |

No user questions were required. All design contract decisions were derivable from
upstream artifacts (CONTEXT.md, RESEARCH.md) and direct codebase reading.

---

*Phase: 24-camera-gui*
*UI-SPEC created: 2026-03-26*
*Status: draft — awaiting checker validation*
