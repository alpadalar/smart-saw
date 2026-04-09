---
phase: 27-maincontroller-integration
plan: 01
subsystem: gui
tags: [navigation, sidebar, page-index, otomatik-kesim, main-controller]
dependency_graph:
  requires:
    - phase-26: OtomatikKesimController (src/gui/controllers/otomatik_kesim_controller.py)
  provides:
    - PageIndex IntEnum (src/gui/page_index.py)
    - Otomatik Kesim sidebar button in MainController
    - Type-safe page switching via PageIndex enum
  affects:
    - src/gui/controllers/main_controller.py (sidebar navigation, stackedWidget order)
tech_stack:
  added: []
  patterns:
    - IntEnum for type-safe QStackedWidget page indices
    - __new__ + manual attribute injection for GUI controller unit tests
key_files:
  created:
    - src/gui/page_index.py
    - tests/test_page_index.py
    - tests/test_main_controller_integration.py
  modified:
    - src/gui/controllers/main_controller.py
decisions:
  - "PageIndex IntEnum over plain int constants: compile-time type safety, IDE navigation, eliminates magic numbers"
  - "OtomatikKesimController imported unconditionally (not lazy): page is always present, unlike CameraController"
  - "closeEvent stop_timers loop extended to 5 pages: includes otomatik_kesim_page for timer cleanup on exit"
metrics:
  duration: "3m 15s"
  completed: "2026-04-09"
  tasks_completed: 2
  files_changed: 4
---

# Phase 27 Plan 01: MainController Integration Summary

PageIndex IntEnum with 6 named constants + OtomatikKesimController wired into MainController sidebar at position 2 (y=286), with all hardcoded `_switch_page(N)` integers replaced by PageIndex enum calls.

## What Was Built

**`src/gui/page_index.py`** — New `PageIndex(IntEnum)` with 6 named page index constants:
- `KONTROL_PANELI = 0`, `OTOMATIK_KESIM = 1`, `KONUMLANDIRMA = 2`, `SENSOR = 3`, `IZLEME = 4`, `KAMERA = 5`

**`src/gui/controllers/main_controller.py`** — 6 targeted change points:
1. Added `OtomatikKesimController` and `PageIndex` imports
2. Added `btnOtomatikKesim` at y=286 with `cutting-start-icon.svg`, shifted existing buttons +121px (Positioning→407, Sensor→528, Tracking→649, Camera→770), updated all lambdas to PageIndex enum
3. Updated `nav_buttons` list to 5 items (OtomatikKesim at index 1), camera remains conditional
4. Instantiated `OtomatikKesimController` page after `control_panel_page`
5. Updated `stackedWidget.addWidget` order: otomatik_kesim at index 1, camera at index 5
6. Extended `closeEvent` stop_timers loop to include `otomatik_kesim_page`

**`tests/test_page_index.py`** — 3 tests verifying enum values, int subclass behavior, member count.

**`tests/test_main_controller_integration.py`** — 5 integration tests using `__new__` injection: nav_buttons count, identity of btnOtomatikKesim at index 1, `_switch_page` PageIndex behavior, `closeEvent` timer cleanup.

## Test Results

| Suite | Result |
|-------|--------|
| tests/test_page_index.py | 3 passed |
| tests/test_main_controller_integration.py | 5 passed |
| tests/test_otomatik_kesim_controller.py | 20 passed (Phase 26 regression: clean) |
| tests/ (excluding pre-existing failure) | 87 passed |

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 (TDD RED+GREEN) | b5ed69d | PageIndex IntEnum and test scaffolding |
| Task 2 (MainController update) | 43f9300 | 6-point MainController integration |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all navigation wiring is fully functional. `btnOtomatikKesim` connects to a real `OtomatikKesimController` page instance with working `stop_timers()`.

## Threat Flags

None — GUI-only sidebar navigation wiring with no trust boundaries crossed (per plan threat model).

## Out-of-Scope Issue Deferred

**Pre-existing test failure:** `tests/test_machine_control_auto_cutting.py::test_write_double_word_fc16` — fails with `AttributeError: 'MachineControl' object has no attribute '_write_double_word'`. This failure was present before Phase 27 changes (confirmed via `git stash` verification). It is a Phase 25/26 regression unrelated to this plan's scope. Not fixed per deviation scope rules.

## Self-Check: PASSED

| Item | Status |
|------|--------|
| src/gui/page_index.py | FOUND |
| tests/test_page_index.py | FOUND |
| tests/test_main_controller_integration.py | FOUND |
| 27-01-SUMMARY.md | FOUND |
| commit b5ed69d | FOUND |
| commit 43f9300 | FOUND |
| hardcoded _switch_page(N) calls | 0 (PASS) |
