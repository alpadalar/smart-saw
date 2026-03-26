---
phase: 24-camera-gui
plan: 01
subsystem: ui
tags: [pyside6, camera, qprogressbar, detection, opencv, cv2]

# Dependency graph
requires:
  - phase: 21-ai-detection-pipeline
    provides: DetectionWorker with _save_annotated_frame(), CameraResultsStore store keys
  - phase: 20-camera-capture
    provides: CameraService, CameraResultsStore, latest_frame store key
provides:
  - DetectionWorker writes annotated_frame JPEG bytes to CameraResultsStore unconditionally each cycle
  - CameraController displays annotated_frame (fallback to latest_frame) in live feed
  - Wear progress bar (green-to-red gradient) inside asinma_frame
  - Health progress bar (red-to-green gradient) inside saglik_frame
  - Convention-audited CameraController (22px status, 400-weight subtitle, 8px thumb spacing, 16px x-offsets)
affects: [camera-gui-verification, live-feed-display, sidebar-navigation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "QProgressBar with qlineargradient stylesheet for wear/health visualization"
    - "annotated_frame store key as primary live feed source with latest_frame fallback"
    - "cv2.imencode unconditional + recording-gated cv2.imwrite separation"

key-files:
  created: []
  modified:
    - src/services/camera/detection_worker.py
    - src/gui/controllers/camera_controller.py
    - tests/test_detection_worker.py

key-decisions:
  - "annotated_frame store write is unconditional — bounding boxes always visible in live feed regardless of recording state (D-02)"
  - "Disk save remains recording-gated — annotated JPEG to disk only when recording_path set"
  - "QProgressBar gradients: wear green-to-red (low=good), health red-to-green (low=bad) per D-04/D-05"
  - "lbl_wear_value and lbl_health_score height reduced 55->35 to fit progress bar at y=83 within 120px frame height"
  - "test_detection_worker.py mock cv2 updated to return (True, MagicMock()) from imencode — required by new tuple unpack"

patterns-established:
  - "Pattern: cv2.imencode returns (ok, buf) — tests must mock return value as tuple, not MagicMock()"

issues-created: []

# Metrics
duration: 10min
completed: 2026-03-26
---

# Phase 24 Plan 01: Camera GUI Annotated Frame + Progress Bars Summary

**DetectionWorker now writes bounding-box-annotated JPEG frames to CameraResultsStore unconditionally; CameraController displays annotated feed with fallback and adds wear/health QProgressBar widgets with correct gradient directions per UI-SPEC**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-26T07:40:00Z
- **Completed:** 2026-03-26T07:51:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- DetectionWorker `_save_annotated_frame()` restructured: bbox drawing and store write moved before recording_path check, enabling live annotated feed without active recording
- CameraController updated with two QProgressBar widgets (wear: green-to-red, health: red-to-green) in their respective frames
- Full convention audit applied: 28px status font corrected to 22px, medium weight corrected to 400, thumb spacing 10px→8px, sub-label x-offsets 15/20px→16px throughout

## Task Commits

Each task was committed atomically:

1. **Task 1: Add annotated_frame store write to DetectionWorker** - `6f4b938` (feat)
2. **Task 2: CameraController — annotated frame fallback, progress bars, convention audit** - `f37efd0` (feat)

## Files Created/Modified

- `src/services/camera/detection_worker.py` — Restructured `_save_annotated_frame()`: unconditional bbox draw + store write, recording-gated disk write
- `src/gui/controllers/camera_controller.py` — Added QProgressBar import, _STATUS_STYLE constant, wear_bar + health_bar widgets, annotated_frame fallback, convention audit fixes
- `tests/test_detection_worker.py` — Fixed mock cv2 to return `(True, MagicMock())` tuple from `imencode` (required by new store write path)

## Decisions Made

- Unconditional annotated_frame store write: even without recording, GUI always gets bounding-box frame (per D-02 decision from CONTEXT.md)
- Progress bar geometry: lbl_wear_value/lbl_health_score height reduced from 55px to 35px to accommodate bar at y=83 within 120px frame height — clean 19px bottom margin
- No new architectural changes — all changes are within the existing CameraController widget and DetectionWorker thread boundaries

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_detection_worker.py cv2 mock for imencode return value**
- **Found during:** Task 1 (Add annotated_frame store write)
- **Issue:** Existing tests mocked cv2 as `MagicMock()` with no return value configured for `imencode`. When `_save_annotated_frame` was updated to call `ok_enc, buf = cv2.imencode(...)`, tests failed with `ValueError: not enough values to unpack (expected 2, got 0)` — the MagicMock returned a single object, not a 2-tuple.
- **Fix:** Set `mock_cv2.imencode.return_value = (True, MagicMock())` in both `test_save_annotated_frame_returns_path_when_recording` and `test_save_annotated_frame_returns_none_without_recording`. Also added `mock_cv2.IMWRITE_JPEG_QUALITY = 1` and `mock_cv2.FONT_HERSHEY_SIMPLEX = 0` for completeness.
- **Files modified:** `tests/test_detection_worker.py`
- **Verification:** All 9 tests pass (`python -m pytest tests/test_detection_worker.py`)
- **Committed in:** `6f4b938` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug in test mock), 0 deferred
**Impact on plan:** Auto-fix necessary for test suite to remain passing. No scope creep — test-only change.

## Issues Encountered

None — both tasks executed cleanly after test mock fix.

## Known Stubs

None — all data paths are wired. `wear_bar` and `health_bar` receive values from `CameraResultsStore.snapshot()` in `_update_health()`. `annotated_frame` is written unconditionally by `DetectionWorker` and read in `_update_frame()`.

## Next Phase Readiness

- DetectionWorker and CameraController are fully wired for annotated live feed and progress bar display
- Remaining Phase 24 work: sidebar camera button in MainController (GUI-07/GUI-08), if applicable
- All 9 detection worker tests pass; camera controller import is clean

## Self-Check: PASSED

- FOUND: `.planning/phases/24-camera-gui/24-01-SUMMARY.md`
- FOUND: `src/services/camera/detection_worker.py`
- FOUND: `src/gui/controllers/camera_controller.py`
- FOUND commit: `6f4b938` (Task 1)
- FOUND commit: `f37efd0` (Task 2)

---
*Phase: 24-camera-gui*
*Completed: 2026-03-26*
