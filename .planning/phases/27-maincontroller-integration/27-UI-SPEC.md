---
phase: 27
phase_name: MainController Integration
status: draft
created: 2026-04-09
design_system: PySide6 Qt stylesheets (no shadcn — desktop application)
---

# UI-SPEC: Phase 27 — MainController Integration

## Overview

This phase adds one sidebar navigation button ("Otomatik Kesim") at index 1, shifts
four existing buttons down 121px, introduces a `PageIndex` IntEnum, and updates all
page-switching lambdas and closeEvent cleanup to use named constants. The deliverable
is visual and interaction parity with existing sidebar buttons — no new visual language.

**Design constraint:** All values below are extracted directly from the live codebase
(`src/gui/controllers/main_controller.py`) and locked decisions in CONTEXT.md. Every
field is pre-populated. No open design questions remain for this phase.

---

## 1. Design System

| Property | Value | Source |
|----------|-------|--------|
| Tool | None (PySide6 Qt stylesheets) | RESEARCH.md — not a web project |
| Framework | PySide6 >= 6.6.0 | pyproject.toml |
| Layout model | Absolute coordinates (setGeometry) | main_controller.py pattern |
| shadcn | Not applicable | Desktop application |
| Registry safety gate | Not applicable | No third-party component registry |

---

## 2. Spacing

The project uses pixel-exact absolute geometry. The established sidebar button grid
is 121px vertical pitch starting at y=165.

| Element | Value | Source |
|---------|-------|--------|
| Sidebar button height | 110px | main_controller.py line 171 |
| Sidebar button width | 355px | main_controller.py line 171 |
| Sidebar button left margin | 26px | main_controller.py line 171 |
| Vertical pitch between buttons | 121px | CONTEXT.md D-01, D-02 |
| Button internal padding | 12px top/bottom, 10px right, 25px left | nav_btn_style line 157 |
| Button border-radius | 10px | nav_btn_style line 159 |
| Sidebar frame width | 392px | main_controller.py line 96 |

**Button y-coordinates after Phase 27:**

| Button | y | Index |
|--------|---|-------|
| Kontrol Paneli | 165 | 0 |
| Otomatik Kesim (NEW) | 286 | 1 |
| Konumlandirma | 407 | 2 |
| Sensor Verileri | 528 | 3 |
| Izleme | 649 | 4 |
| Kamera (conditional) | 770 | 5 |

---

## 3. Typography

Sidebar uses a single font family throughout. No new typography is introduced.

| Role | Font Family | Weight | Size | Line Height | Element |
|------|-------------|--------|------|-------------|---------|
| Nav button label | Plus Jakarta Sans | medium (500) | 26px | implicit Qt default | All sidebar buttons |
| Logo primary | Plus Jakarta Sans | bold (700) | 58px | implicit | labelSmart |
| Logo secondary | Plus Jakarta Sans | 100 | 58px | implicit | labelSaw |
| Notification date/time | Plus Jakarta Sans | 300 | 24px | implicit | labelDate, labelTime |
| Status text | Plus Jakarta Sans | 400 | 20px | implicit | labelSystemStatusInfo |

**Rule:** The new "Otomatik Kesim" button uses font-size 26px, weight medium — identical
to all other nav buttons. Source: `nav_btn_style` variable, main_controller.py line 148-167.

---

## 4. Color

No new colors are introduced. The new button reuses `nav_btn_style` verbatim.

| Role | Value | Usage |
|------|-------|-------|
| Dominant surface | rgba(6, 11, 38, 240) — rgba(26, 31, 55, 0) gradient | Sidebar frame background |
| Nav button default | transparent | Button background (unselected) |
| Nav button hover | rgba(255, 255, 255, 0.05) | Button hover state |
| Nav button checked/active | rgba(26, 31, 55, 128) | Active page button |
| Label text | #F4F6FC | All sidebar labels and buttons |
| Notification bar | rgba(26, 31, 55, 77) | notificationFrame background |
| Content area | transparent | stackedWidget background |

**60/30/10 mapping for sidebar:**
- 60% dominant: dark navy gradient (#060B26 family)
- 30% secondary: semi-transparent overlays (checked state, notification bar)
- 10% accent: #F4F6FC text only (no distinct accent color — monochromatic palette)

---

## 5. Icon

| Property | Value | Source |
|----------|-------|--------|
| Icon file | `cutting-start-icon.svg` | CONTEXT.md D-06; src/gui/images/ |
| Icon size | QSize(80, 80) | RESEARCH.md A1 resolution: majority pattern (3 of 4 existing buttons use 80x80; btnControlPanel uses 70x70 which is a historical deviation) |
| Icon loading method | `self._icon("cutting-start-icon.svg")` | main_controller.py line 71-74 |

---

## 6. Interaction Contract

### 6.1 New Button: btnOtomatikKesim

| Property | Value |
|----------|-------|
| Widget type | QPushButton |
| Parent | self.sidebarFrame |
| Label | "  Otomatik Kesim" (two leading spaces — matches existing button padding pattern) |
| Geometry | setGeometry(26, 286, 355, 110) |
| Icon | self._icon("cutting-start-icon.svg") |
| Icon size | QSize(80, 80) |
| Style | nav_btn_style (same variable, no override) |
| Checkable | setCheckable(True) |
| Default checked | False (only Kontrol Paneli starts checked) |
| Click action | lambda: self._switch_page(PageIndex.OTOMATIK_KESIM) |

### 6.2 Shifted Buttons (y-coordinate updates only)

| Button | Old y | New y | Lambda update |
|--------|-------|-------|---------------|
| btnPositioning | 286 | 407 | PageIndex.KONUMLANDIRMA |
| btnSensor | 407 | 528 | PageIndex.SENSOR |
| btnTracking | 528 | 649 | PageIndex.IZLEME |
| btnCamera (conditional) | 649 | 770 | PageIndex.KAMERA |

### 6.3 Page Switching Behavior

`_switch_page(index)` behavior is unchanged:
1. Uncheck all buttons in nav_buttons list.
2. Set nav_buttons[index].setChecked(True).
3. Call stackedWidget.setCurrentIndex(index).

IntEnum passthrough: PageIndex extends int, so `_switch_page(PageIndex.OTOMATIK_KESIM)`
passes int value 1 directly — no type conversion needed.

### 6.4 nav_buttons List (after update)

```
self.nav_buttons = [
    self.btnControlPanel,    # index 0 — PageIndex.KONTROL_PANELI
    self.btnOtomatikKesim,   # index 1 — PageIndex.OTOMATIK_KESIM (NEW)
    self.btnPositioning,     # index 2 — PageIndex.KONUMLANDIRMA
    self.btnSensor,          # index 3 — PageIndex.SENSOR
    self.btnTracking         # index 4 — PageIndex.IZLEME
]
# Conditional: self.nav_buttons.append(self.btnCamera)  # index 5 — PageIndex.KAMERA
```

### 6.5 stackedWidget Insertion Order

```
addWidget(self.control_panel_page)    # Index 0
addWidget(self.otomatik_kesim_page)   # Index 1 (NEW — inserted between control_panel and positioning)
addWidget(self.positioning_page)      # Index 2
addWidget(self.sensor_page)           # Index 3
addWidget(self.monitoring_page)       # Index 4
# Conditional: addWidget(self.camera_page)  # Index 5
```

### 6.6 closeEvent Cleanup

The `otomatik_kesim_page` is added to the unconditional stop_timers loop:

```
for page in [self.control_panel_page, self.otomatik_kesim_page,
             self.positioning_page, self.sensor_page, self.monitoring_page]:
    if page and hasattr(page, 'stop_timers'):
        page.stop_timers()
```

Camera page conditional block is unchanged.

**Rationale:** OtomatikKesimController has two active timers (`_polling_timer` at 500ms
and `_reset_tick_timer`). Linux segfault prevention requires explicit GUI-thread stop
before window destruction. Source: app.py comment, RESEARCH.md Pitfall 4.

---

## 7. Copywriting

| Element | Text | Notes |
|---------|------|-------|
| Sidebar button label | "  Otomatik Kesim" | Two leading spaces, same as all other nav buttons (source: D-05) |
| Empty state | N/A | Page already implemented in Phase 26 |
| Error state | N/A | No new error states introduced in this phase |
| Destructive actions | None | This phase has no destructive user actions |
| Window title | "Smart Band Saw Control System" | Unchanged — main_controller.py line 79 |

---

## 8. PageIndex Enum Contract

New file: `src/gui/page_index.py`

```python
from enum import IntEnum

class PageIndex(IntEnum):
    KONTROL_PANELI = 0
    OTOMATIK_KESIM = 1
    KONUMLANDIRMA  = 2
    SENSOR         = 3
    IZLEME         = 4
    KAMERA         = 5
```

This enum is the single source of truth for all page-switching references in
`main_controller.py`. Hardcoded integer literals 0–4 are fully replaced.

Import in main_controller.py: `from ..page_index import PageIndex`

---

## 9. States

### Sidebar Button States

| State | Visual | Trigger |
|-------|--------|---------|
| Default (unselected) | background: transparent | Not active page |
| Hover | background: rgba(255,255,255,0.05) | Mouse hover |
| Active (checked) | background: rgba(26,31,55,128) | Current page is this button's page |

All states already defined in `nav_btn_style`. New button applies the same style
without modification.

### OtomatikKesimController Page States

Already defined and implemented in Phase 26. This phase only wires navigation —
no new page states are introduced.

---

## 10. Component Inventory

| Component | Action | File |
|-----------|--------|------|
| `PageIndex` IntEnum | CREATE | `src/gui/page_index.py` |
| `btnOtomatikKesim` QPushButton | CREATE | `src/gui/controllers/main_controller.py` |
| `otomatik_kesim_page` OtomatikKesimController | CREATE (instantiate) | `src/gui/controllers/main_controller.py` |
| `btnPositioning` y-coordinate | UPDATE 286 -> 407 | `src/gui/controllers/main_controller.py` |
| `btnSensor` y-coordinate | UPDATE 407 -> 528 | `src/gui/controllers/main_controller.py` |
| `btnTracking` y-coordinate | UPDATE 528 -> 649 | `src/gui/controllers/main_controller.py` |
| `btnCamera` y-coordinate (conditional) | UPDATE 649 -> 770 | `src/gui/controllers/main_controller.py` |
| All `_switch_page` lambdas | UPDATE int literals -> PageIndex | `src/gui/controllers/main_controller.py` |
| `nav_buttons` list | UPDATE insert at index 1 | `src/gui/controllers/main_controller.py` |
| `stackedWidget.addWidget` sequence | UPDATE insert at index 1 | `src/gui/controllers/main_controller.py` |
| `closeEvent` stop_timers loop | UPDATE add otomatik_kesim_page | `src/gui/controllers/main_controller.py` |
| `OtomatikKesimController` import | CREATE | `src/gui/controllers/main_controller.py` |
| `PageIndex` import | CREATE | `src/gui/controllers/main_controller.py` |

---

## 11. Pre-Population Sources

| Source | Decisions Used |
|--------|----------------|
| CONTEXT.md | 8 locked decisions (D-01 through D-08): button position, label, icon, index, y-coords, unconditional display, closeEvent |
| RESEARCH.md | Standard stack (PySide6 + IntEnum), all 6 change points in main_controller.py, icon size resolution (80x80 majority), constructor signature |
| main_controller.py (live code) | nav_btn_style verbatim, button geometry pattern, existing y-coordinates, nav_buttons list, addWidget sequence, closeEvent loop |
| User input | 0 (all questions answered by upstream artifacts) |

---

## 12. Out of Scope

Per CONTEXT.md deferred section and REQUIREMENTS.md out-of-scope:

- No new visual style or color introduced
- No new page UI (OtomatikKesimController is complete from Phase 26)
- No progress bar, cutting history log, automatic speed optimization, or multi-job queue
- No conditional display logic for Otomatik Kesim button (always visible — D-07)

---

*Phase: 27-maincontroller-integration*
*UI-SPEC created: 2026-04-09*
*Status: draft — ready for checker validation*
