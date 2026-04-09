---
phase: 26-otomatik-kesim-controller
plan: 02
subsystem: ui
tags: [pyside6, qwidget, numpad, touchscreen, otomatik-kesim, plc, machine-control, parameter-input]

requires:
  - 26-01 (OtomatikKesimController scaffold, NumpadDialog allow_decimal)
provides:
  - All 5 param frame click handlers (_handle_p/x/l/c/s_frame_click)
  - START validation + PLC write sequence (_handle_start_click, _validate_params)
  - IPTAL cancel + full UI reset (_handle_iptal_click)
  - Validation error display with 3s auto-dismiss (_show_validation_error)
  - _get_target() helper returning P*X
affects:
  - 26-03 (RESET hold animation, D2056 polling, ML mode sync — builds on same file)

tech-stack:
  added: []
  patterns:
    - "mousePressEvent override via attribute assignment (frame.mousePressEvent = handler)"
    - "Value clamping per param: P max(1,9999), X max(1,999), L round(max(1,99999),1), C/S max(0,500)"
    - "C and S write to PLC immediately on acceptance (not deferred to START)"
    - "START writes all registers BEFORE start_auto_cutting() — Pitfall 6 mitigation"
    - "QTimer.singleShot(3000) for auto-dismiss validation error label"

key-files:
  created: []
  modified:
    - src/gui/controllers/otomatik_kesim_controller.py

key-decisions:
  - "NumpadDialog imported with try/except fallback to QDialog to avoid hard ImportError at module load time"
  - "QDialog added to PySide6 import tuple at module level (needed for QDialog.Accepted comparison)"
  - "C and S immediately write to PLC on acceptance rather than only at START — matches D-07 spec; avoids stale speed values if operator adjusts mid-session"
  - "L value stored as str(float) e.g. '1000.0' for reliable float() parsing; display strips .0 for whole numbers"
  - "_validate_params checks P then L then X order (matching Turkish UI message priority)"

requirements-completed:
  - PARAM-01
  - PARAM-03
  - PARAM-04
  - PARAM-05

duration: 20min
completed: 2026-04-09
---

# Phase 26 Plan 02: Parameter Handlers + START/IPTAL Wiring Summary

**All 5 parameter frame click handlers wired with NumpadDialog, value clamping, and PLC writes; START validation + PLC sequence and IPTAL cancel/reset fully implemented in OtomatikKesimController.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-04-09
- **Tasks:** 2 (committed atomically — both tasks modify same file)
- **Files modified:** 1

## Accomplishments

- Added NumpadDialog import with try/except fallback; added QDialog to PySide6 import tuple
- Wired `mousePressEvent` for all 5 param frames in `_setup_ui()` after frame creation
- Wired `btnStart.clicked` and `btnIptal.clicked` connections in `_setup_ui()`
- `_handle_p_frame_click`: opens NumpadDialog, parses as int, clamps 1-9999, updates label + calls `_update_total_label()`
- `_handle_x_frame_click`: same pattern, clamps 1-999, also calls `_update_total_label()`
- `_handle_l_frame_click`: opens NumpadDialog with `allow_decimal=True`, parses float, clamps 1.0-99999.0, rounds to 1dp, displays without trailing .0 for whole numbers
- `_handle_c_frame_click`: parses as int, clamps 0-500, immediately calls `write_cutting_speed(value)`
- `_handle_s_frame_click`: parses as int, clamps 0-500, immediately calls `write_descent_speed(float(value))`
- All 5 handlers guarded by `if not self._params_enabled: return` (T-26-05 mitigation)
- `_validate_params()`: checks P, L, X mandatory; returns Turkish error string or None
- `_show_validation_error()`: sets label text, makes visible, QTimer.singleShot(3000) to hide
- `_handle_start_click()`: validates, writes `write_target_adet`, `write_target_uzunluk`, optionally C/S speeds, then `start_auto_cutting()` — PLC registers written BEFORE start (T-26-04/Pitfall 6)
- `_handle_iptal_click()`: calls `cancel_auto_cutting()`, re-enables params, resets btnStart, labelCounter, progressWidget, labelComplete, stops polling timer
- `_get_target()`: returns P*X or 0 safely with try/except
- 58 existing tests pass — no regressions; ruff exits clean

## Task Commits

1. **Task 1 + Task 2: Wire all param handlers, START validation, IPTAL reset** — `f743676` (feat)

(Both tasks implemented atomically in one file write; single commit covers complete plan deliverables.)

## Files Modified

- `src/gui/controllers/otomatik_kesim_controller.py` — Added NumpadDialog import, QDialog to imports, mousePressEvent wiring, btnStart/btnIptal connections, 5 param click handlers, _validate_params, _show_validation_error, _handle_start_click, _handle_iptal_click, _get_target (211 lines added)

## Decisions Made

- NumpadDialog imported under try/except so module loads even in headless/test environments without PySide6 GUI (matches existing pattern in control_panel_controller.py)
- `QDialog` added to PySide6 imports tuple (needed for `QDialog.Accepted` comparison in handlers)
- C and S write to PLC immediately on dialog acceptance, not deferred to START — per D-07; prevents stale register values if operator re-adjusts speeds between sessions
- L value stored as `str(float)` (e.g. `"1000.0"`) internally; display strips `.0` for whole numbers to match touchscreen UX convention

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all handlers wire to real NumpadDialog and real MachineControl calls. The `machine_control` guard (`if self.machine_control:`) prevents crashes when PLC is not connected (offline/dev environment), which is correct behavior.

## Threat Mitigations Applied

| Threat ID | Mitigation | Location |
|-----------|-----------|----------|
| T-26-03 | Value clamping in every frame handler | _handle_p/x/l/c/s_frame_click |
| T-26-04 | _validate_params blocks START if P/L/X not set; PLC writes before start | _handle_start_click |
| T-26-05 | Python-level guard `if not self._params_enabled: return` in all 5 handlers | All frame click handlers |

## Next Phase Readiness

- Plan 03 can wire `_polling_timer.timeout` to a `_poll_cut_count()` method that reads D2056 and updates `labelCounter` + `progressWidget`
- Plan 03 can wire `btnReset` pressed/released for RESET hold animation using `_reset_tick_timer`
- Plan 03 can implement ML mode toggle (`btnManual`/`btnAI` clicked) and `_previous_count` ML detection logic
- `_get_target()` is available for polling to calculate progress ratio (current / target)

---
*Phase: 26-otomatik-kesim-controller*
*Completed: 2026-04-09*

## Self-Check: PASSED

- `src/gui/controllers/otomatik_kesim_controller.py` — FOUND (769 lines)
- Commit `f743676` — FOUND (feat(26-02): wire param handlers, START validation, and IPTAL reset)
- All 5 param handlers: FOUND via import check
- All START/IPTAL handlers: FOUND via import check
- ruff: CLEAN
- 58 tests: PASSED
