---
phase: 26-otomatik-kesim-controller
plan: 01
subsystem: ui
tags: [pyside6, qwidget, numpad, touchscreen, otomatik-kesim, absolute-layout]

requires: []
provides:
  - NumpadDialog with allow_decimal=True support and double-decimal guard
  - OtomatikKesimController QWidget scaffold with full two-column layout
  - _ProgressBar custom painted QWidget inner class
  - stop_timers() method for MainController.closeEvent contract
  - _set_params_enabled() and _update_total_label() helpers
affects:
  - 26-02 (param click handlers, START, IPTAL behavior wiring)
  - 26-03 (RESET hold animation, D2056 polling, ML mode sync)

tech-stack:
  added: []
  patterns:
    - "Absolute coordinate layout (no QLayout managers) — project-wide convention"
    - "_create_param_frame() helper reduces repetition for 5 identical frame structures"
    - "Style strings stored as instance attributes (_frame_style, _button_default_style, etc.)"
    - "QWidget paintEvent override for custom progress bar (no third-party chart library)"
    - "Unused imports removed for ruff compliance (NumpadDialog and ControlMode imported in Plan 02/03)"

key-files:
  created:
    - src/gui/controllers/otomatik_kesim_controller.py
  modified:
    - src/gui/numpad.py

key-decisions:
  - "decimalButton hidden by default (hide()) in Ui_Dialog.setupUi — shown only when allow_decimal=True"
  - "Bottom row rearranged when allow_decimal=True: [.][backspace][0][enter] layout"
  - "Imports for NumpadDialog and ControlMode removed from controller (unused in scaffold; Plan 02/03 will re-add)"
  - "_create_param_frame() helper used for all 5 param frames to avoid 100+ lines of duplication"

patterns-established:
  - "Param frame creation via _create_param_frame(parent, x, y, w, h, title, hint, attr_prefix)"
  - "Custom progress bar as inner QWidget subclass (_ProgressBar) with paintEvent"
  - "Timer created in _setup_timers but NOT started — connection deferred to behavior plans"

requirements-completed:
  - PARAM-02

duration: 25min
completed: 2026-04-09
---

# Phase 26 Plan 01: OtomatikKesimController Scaffold Summary

**NumpadDialog decimal support added and OtomatikKesimController QWidget scaffold created with full two-column absolute layout, 5 param frames, counter/progress bar, START/RESET/IPTAL controls, and ML mode toggles.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-04-09T01:00:00Z
- **Completed:** 2026-04-09T01:23:17Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- NumpadDialog extended with `allow_decimal=False` parameter — shows "." button and rearranges bottom row when True; double-decimal guard and auto "0" prefix in add_digit
- OtomatikKesimController QWidget scaffold created at 559 lines with all layout elements at exact UI-SPEC coordinates
- Custom `_ProgressBar` QWidget with QPainter rendering (accent color fill, success green when complete)
- All state attributes initialized: `_params_enabled`, `_previous_count`, `_reset_in_progress` (Pitfall 1/4 guards)
- 69 existing tests pass — no regressions

## Task Commits

1. **Task 1: Add allow_decimal support to NumpadDialog** — `485c8f3` (feat)
2. **Task 2: Create OtomatikKesimController widget scaffold** — `ae28053` (feat)

## Files Created/Modified

- `src/gui/numpad.py` — Added `decimalButton` QPushButton, `allow_decimal` parameter, bottom-row rearrangement, decimal connection, double-decimal guard in add_digit
- `src/gui/controllers/otomatik_kesim_controller.py` — New file: complete OtomatikKesimController with two-column layout, all frames/labels/buttons, stop_timers, helper methods

## Decisions Made

- Decimal button placed at same geometry as backspace in Ui_Dialog (hidden by default). When allow_decimal=True, geometries are reassigned to split bottom row into 4 segments — avoids any z-order issues and keeps Ui_Dialog clean.
- `NumpadDialog` and `ControlMode` imports removed from controller scaffold to satisfy ruff lint (F401 unused import). Plan 02 will re-add them when click handlers are wired.
- `_create_param_frame()` helper used for all 5 param frames, storing attributes via `setattr(self, f"frame{attr_prefix}", frame)` — eliminates ~100 lines of repetitive code while keeping attribute naming identical to what Plans 02/03 expect.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused imports to pass ruff lint**
- **Found during:** Task 2 (ruff check after file creation)
- **Issue:** `NumpadDialog`, `ControlMode`, and `time` were imported but unused in the scaffold; ruff F401 lint error
- **Fix:** Removed `time`, `NumpadDialog`, and `ControlMode` imports; they will be re-added in Plan 02/03 when behavior is wired
- **Files modified:** src/gui/controllers/otomatik_kesim_controller.py
- **Verification:** `ruff check` exits 0
- **Committed in:** ae28053 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (lint cleanup)
**Impact on plan:** No scope change. Imports will be restored in Plans 02/03 when actually used.

## Issues Encountered

- Verification command in the plan runs with `cd /media/workspace/smart-saw` which imports from the main workspace, not the worktree. Ran verification from the worktree working directory instead — all checks passed.

## Known Stubs

None — this plan creates structural scaffold only. Labels display "—" em dash for empty param values and "0 / 0" for the counter. These are correct idle-state values, not placeholder stubs. Data will be wired in Plans 02/03.

## Next Phase Readiness

- Plan 02 can immediately wire `frameP.mousePressEvent`, `frameX.mousePressEvent`, `frameL.mousePressEvent`, `frameC.mousePressEvent`, `frameS.mousePressEvent` — all frames exist at correct coordinates
- Plan 02 can wire `btnStart.clicked`, `btnIptal.clicked` — buttons exist
- Plan 03 can wire `btnReset` (TouchButton) pressed/released/touch_pressed/touch_released signals, `_polling_timer.timeout`, `_reset_tick_timer.timeout`
- `NumpadDialog(parent, initial_value=str, allow_decimal=True)` ready for L field in Plan 02

---
*Phase: 26-otomatik-kesim-controller*
*Completed: 2026-04-09*
