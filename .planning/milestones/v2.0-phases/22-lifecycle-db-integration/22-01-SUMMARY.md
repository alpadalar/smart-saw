---
phase: 22-lifecycle-db-integration
plan: "01"
subsystem: camera
tags: [vision-service, lifecycle, traceability, sqlite, threading]
dependency_graph:
  requires: [phase-21-ai-detection-pipeline]
  provides: [vision-service, lifecycle-camera-integration, camera-db-traceability]
  affects: [lifecycle.py, data_processor.py, detection_worker.py, ldc_worker.py]
tech_stack:
  added: []
  patterns: [daemon-thread, stop-event, lazy-import, traceability-fields]
key_files:
  created:
    - src/services/camera/vision_service.py
    - tests/test_vision_service.py
  modified:
    - src/core/lifecycle.py
    - src/services/processing/data_processor.py
    - src/services/camera/detection_worker.py
    - src/services/camera/ldc_worker.py
    - tests/test_detection_worker.py
    - tests/test_ldc_worker.py
decisions:
  - "VisionService polls at 0.5s (2 Hz) interval by default — configurable via vision.polling_interval"
  - "DataProcessingPipeline writes testere_durumu after _last_processed_data = processed_data — both values available"
  - "recording_duration defaults to 10s — configurable via vision.recording_duration"
  - "_compute_wear returns (percent, edge_pixel_count) tuple — backward-compatible since only called internally"
metrics:
  duration_seconds: 328
  completed_date: "2026-03-26"
  tasks_completed: 2
  files_modified: 8
---

# Phase 22 Plan 01: Lifecycle & DB Integration Summary

VisionService daemon thread with CUTTING→non-CUTTING recording trigger, lifecycle integration, and full traceability field population in camera.db writes.

## What Was Built

**Task 1: VisionService + DataProcessingPipeline bridge**

Created `src/services/camera/vision_service.py` — a daemon thread following the exact DetectionWorker/LDCWorker pattern:
- `polling_interval` (default 0.5s) and `recording_duration` (default 10s) configurable via `vision.*` config keys
- `_poll_once()` method extracts polling logic for testability — called in `run()` loop
- CUTTING(3) → non-CUTTING transition detection triggers `start_recording()`
- After `recording_duration` seconds, calls `stop_recording()`
- D-07 compliant: all exceptions caught and logged, thread never dies

Modified `src/services/processing/data_processor.py` — `_processing_loop()` now writes `testere_durumu`, `kesim_id`, `makine_id`, `serit_id`, `malzeme_cinsi` to `CameraResultsStore` via `update_batch` after each cycle. Guarded by `if self.camera_results_store is not None:` so camera.enabled=false path is zero-cost.

11 unit tests cover: transition detection, no-duplicate guard, duration-based stop, error isolation (D-07), stop event, prev_testere_durumu tracking, DataProcessingPipeline integration.

**Task 2: Lifecycle integration + worker DB field population**

`src/core/lifecycle.py`:
- `self.vision_service = None` added to `__init__`
- VisionService created and started after LDCWorker in `_init_camera()` (lazy import)
- `stop()` stops VisionService FIRST (per D-09 shutdown order), then DetectionWorker, LDCWorker, CameraService

`src/services/camera/detection_worker.py`:
- `_save_annotated_frame` changed from `-> None` to `-> str | None`, returns saved file path
- DB writes now read `kesim_id`, `makine_id`, `serit_id`, `malzeme_cinsi` from CameraResultsStore
- DB write params now include real `image_path` from `_save_annotated_frame` return value

`src/services/camera/ldc_worker.py`:
- `_compute_wear` changed to return `tuple[float | None, int | None]` — `(wear_percentage, edge_pixel_count)`
- Saves LDC edge image to `recording_path/ldc/ldc_{ts}.jpg` when recording is active
- DB writes now include `edge_pixel_count`, `image_path`, and traceability fields from CameraResultsStore

Updated `tests/test_detection_worker.py` and `tests/test_ldc_worker.py` with 8 new tests covering traceability field verification, `_save_annotated_frame` path return, and `_compute_wear` tuple return.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1    | 2943925 | feat(22-01): VisionService + DataProcessingPipeline camera bridge |
| 2    | 885db25 | feat(22-01): Lifecycle integration + worker DB traceability |

## Test Results

All 45 camera-related tests pass:
- `test_vision_service.py`: 11 tests (new)
- `test_detection_worker.py`: 9 tests (6 existing + 3 new)
- `test_ldc_worker.py`: 8 tests (5 existing + 3 new)
- `test_camera_results_store.py`: 8 tests (unchanged)
- `test_camera_service.py`: 9 tests (unchanged)

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| VisionService polling at 0.5s (2 Hz) | Fast enough to detect testere_durumu transitions without CPU overhead |
| recording_duration defaults to 10s | Consistent with plan spec; configurable via config |
| DataProcessingPipeline update after `_last_processed_data = processed_data` | Both raw_data and processed_data available, cutting_session_id is filled |
| `_compute_wear` returns tuple | Only called internally, no API break; edge_pixel_count captured where computed |
| LDC edge image saved inline in run() | cv2 is already imported there — no extra import needed |

## Deviations from Plan

None — plan executed exactly as written.

The test for DataProcessingPipeline traceability writes was implemented using async test pattern (asyncio.run) to exercise the actual `_processing_loop` code path rather than manually calling `update_batch` in the test. This gives stronger test coverage.

## Known Stubs

None — all DB write fields are populated with real values from CameraResultsStore.

## Self-Check: PASSED
