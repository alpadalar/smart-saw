---
phase: 26-otomatik-kesim-controller
plan: 03
subsystem: gui-controllers
tags: [reset-hold, polling-timer, ml-mode, unit-tests, touchbutton]
dependency_graph:
  requires: [26-01, 26-02]
  provides: [fully-wired-otomatik-kesim-controller, phase-26-unit-tests]
  affects: [src/gui/controllers/otomatik_kesim_controller.py, tests/test_otomatik_kesim_controller.py]
tech_stack:
  patterns:
    - TouchButton 4-signal hold-delay pattern (pressed/released + touch_pressed/touch_released)
    - asyncio.run_coroutine_threadsafe for GUI->async thread boundary
    - QPainter overlay paintEvent override for progress animation
    - __new__ + manual attribute injection for QWidget unit tests without QApplication
key_files:
  modified:
    - src/gui/controllers/otomatik_kesim_controller.py
  created:
    - tests/test_otomatik_kesim_controller.py
decisions:
  - "_set_params_enabled mocked at fixture level to avoid _frame_style dependency in unit tests — tests that assert on it re-assign with a fresh MagicMock()"
  - "control_manager.set_mode returns real coroutine (_noop_coro) via side_effect to satisfy asyncio.run_coroutine_threadsafe type check"
  - "_trigger_ml_state_reset guarded by count > 0 to avoid spurious ML reset when PLC idle-resets D2056 to zero"
metrics:
  duration: "~25 minutes"
  completed: "2026-04-09"
  tasks_completed: 2
  files_modified: 1
  files_created: 1
---

# Phase 26 Plan 03: RESET Hold-Delay, D2056 Polling, ML Toggle, and Unit Tests Summary

**One-liner:** RESET 1500ms hold with QPainter progress overlay, 500ms D2056 polling with completion detection, ML mode two-way sync, and 20 unit tests covering all Phase 26 requirements.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Wire RESET hold-delay and ML mode toggle | ced900b | src/gui/controllers/otomatik_kesim_controller.py |
| 1-fix | Restore files lost in git reset | 3f4241e | src/services/control/machine_control.py, src/gui/numpad.py, tests/test_machine_control_auto_cutting.py |
| 2 | D2056 polling + unit tests | 900451c | tests/test_otomatik_kesim_controller.py |

## What Was Built

### Task 1: RESET Hold-Delay + ML Mode Toggle

**RESET Hold-Delay (D-11, T-26-06, T-26-08):**
- Wired all 4 TouchButton signals in `_setup_ui()`: `pressed`, `released`, `touch_pressed`, `touch_released` — all route to `_on_reset_press` / `_on_reset_release`
- `_on_reset_press`: double-fire guard via `_reset_in_progress` flag (Pitfall 1 / T-26-06: touchscreen fires both pressed and touch_pressed)
- `_on_reset_tick`: 50ms tick timer updates `_reset_progress = min(1.0, elapsed / 1.5)`, calls `reset_auto_cutting(True)` at 1500ms
- `_on_reset_release`: always calls `reset_auto_cutting(False)` to clear bit 20.14 regardless of elapsed time (T-26-08: stuck bit prevention)
- `_paint_reset_progress`: QPainter overlay with `QColor(149, 9, 82, 120)` fill, left-to-right proportional to `_reset_progress`, painted over `btnReset`'s original paintEvent

**ML Mode Toggle (D-16, D-17):**
- `btnManual.clicked` → `_switch_to_mode(ControlMode.MANUAL)`
- `btnAI.clicked` → `_switch_to_mode(ControlMode.ML)`
- `_switch_to_mode`: sets button checked states, schedules `control_manager.set_mode(mode)` via `asyncio.run_coroutine_threadsafe` (T-26-09)
- `_sync_ml_mode`: reads `control_manager.current_mode` on page open, sets button states — called at end of `__init__`

**D2056 Polling Wiring:**
- `_polling_timer.timeout.connect(self._on_polling_timer)` in `_setup_timers()`
- `_reset_tick_timer.timeout.connect(self._on_reset_tick)` in `_setup_timers()`

### Task 2: D2056 Polling + Completion + ML Reset + Unit Tests

**`_on_polling_timer` (D-13, D-14, D-15, D-18):**
- Calls `machine_control.read_kesilmis_adet()`, skips if `None` or `machine_control` is None
- Updates `labelCounter.setText(f"{count} / {target}")`
- Updates `progressWidget._progress` and `_complete`
- D-18: detects `count < _previous_count and count > 0` → calls `_trigger_ml_state_reset()` (Pitfall 4: skips when `_previous_count is None`)
- D-15: calls `_on_cutting_complete()` when `count >= target > 0`
- D-14: calls `_set_params_enabled(False)` when `count > 0`, `_set_params_enabled(True)` when `count == 0`

**`_on_cutting_complete` (D-15):**
- Sets `labelCounter` color to `#22C55E` (semantic-success green)
- Shows `labelComplete` ("Tamamlandi!")
- Re-enables params and START button
- Stops polling timer

**`_trigger_ml_state_reset` (D-18):**
- Calls `asyncio.run_coroutine_threadsafe(control_manager.set_mode(ControlMode.ML), event_loop)`
- Syncs button states: `btnManual.setChecked(False)`, `btnAI.setChecked(True)`

**Unit Tests (20 tests):**
- 4 validation tests (missing P/L/X, valid case)
- 6 polling/counter tests (format, param disable/enable, completion, early-exit guards)
- 6 ML mode tests (toggle MANUAL/ML, reset on decrease, no reset on first poll/increase/zero)
- 4 helper tests (total label, get_target variants)

## Verification Results

1. `python -m pytest tests/test_otomatik_kesim_controller.py -v` — **20 passed**
2. `python -m pytest tests/ -x -q` — **89 passed, 0 failures** (no regressions)
3. `ruff check src/gui/controllers/otomatik_kesim_controller.py` — **clean**
4. `ruff check tests/test_otomatik_kesim_controller.py` — **clean**
5. `python -c "from src.gui.controllers.otomatik_kesim_controller import OtomatikKesimController"` — **import clean**
6. `grep -c "def test_" tests/test_otomatik_kesim_controller.py` — **20** (> 13 minimum)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Restored files accidentally deleted by git reset --soft**
- **Found during:** Task 1 commit
- **Issue:** `git reset --soft` to base commit left staged deletions in the index; `git add src/gui/controllers/otomatik_kesim_controller.py && git commit` inadvertently included those staged deletions, removing `src/services/control/machine_control.py` auto-cutting methods, `src/gui/numpad.py` allow_decimal additions, and `tests/test_machine_control_auto_cutting.py`
- **Fix:** Restored all three files from `fb6ef86` (base commit) via `git show fb6ef86:path > path`, then committed the restoration as `fix(26-03)`
- **Files modified:** `src/services/control/machine_control.py`, `src/gui/numpad.py`, `tests/test_machine_control_auto_cutting.py`
- **Commit:** 3f4241e

**2. [Rule 2 - Missing Critical] Fixture-level _set_params_enabled mock**
- **Found during:** Task 2 (TDD RED phase)
- **Issue:** `_set_params_enabled` accesses `self._frame_style` Qt style string which doesn't exist in the test fixture; tests calling `_on_polling_timer` with non-zero counts failed
- **Fix:** Added `_set_params_enabled = MagicMock(side_effect=...)` at fixture level; tests that assert on it re-assign a fresh MagicMock
- **Files modified:** `tests/test_otomatik_kesim_controller.py`

**3. [Rule 2 - Missing Critical] Coroutine mock for asyncio.run_coroutine_threadsafe**
- **Found during:** Task 2 (TDD RED phase)
- **Issue:** `MagicMock().set_mode()` returns a `MagicMock`, not a coroutine; `asyncio.run_coroutine_threadsafe` raises `TypeError: A coroutine object is required`
- **Fix:** `ctrl.control_manager.set_mode.side_effect = lambda mode: _noop_coro(mode)` where `_noop_coro` is an async def returning None
- **Files modified:** `tests/test_otomatik_kesim_controller.py`

## Known Stubs

None — all methods are fully wired. The controller is complete for Phase 26. Navigation integration (Phase 27) will add the page to QStackedWidget and sidebar.

## Threat Flags

No new network endpoints, auth paths, file access patterns, or schema changes introduced. All STRIDE threats from the plan were mitigated as designed:

| Threat | Mitigation Applied |
|--------|-------------------|
| T-26-06 (RESET double-fire) | `_reset_in_progress` guard in `_on_reset_press` |
| T-26-07 (spurious ML reset) | `_previous_count is None` guard skips first poll |
| T-26-08 (stuck bit 20.14) | `_on_reset_release` always calls `reset_auto_cutting(False)` |
| T-26-09 (GUI->async thread) | `asyncio.run_coroutine_threadsafe` is the standard safe bridge |

## Self-Check

Files exist:
- `src/gui/controllers/otomatik_kesim_controller.py` — FOUND (967 lines)
- `tests/test_otomatik_kesim_controller.py` — FOUND (285 lines, 20 tests)

Commits exist:
- ced900b (feat Task 1) — FOUND
- 3f4241e (fix restore) — FOUND
- 900451c (test Task 2) — FOUND

## Self-Check: PASSED
