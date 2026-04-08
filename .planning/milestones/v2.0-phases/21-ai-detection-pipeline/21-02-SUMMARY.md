---
phase: 21-ai-detection-pipeline
plan: "02"
subsystem: camera
tags: [ldc, wear-detection, health-calculator, unit-tests, config-driven]

# Dependency graph
requires:
  - phase: 21-ai-detection-pipeline-01
    provides: LDCWorker and HealthCalculator implementations, CameraResultsStore, modelB4.py

provides:
  - Config-driven ROI parameters in config.yaml camera.wear section (D-06)
  - LDCWorker without module-level constants (ROI migrated to self._ attributes)
  - Convention-audited ldc_worker.py with Google-style docstrings
  - Convention-audited health_calculator.py with module docstring
  - 8 unit tests for HealthCalculator covering DET-04 formula, status labels, colors
  - 5 unit tests for LDCWorker covering DET-03, DET-04, DET-05, DET-06, D-04, D-06

affects: [21-03, 22-camera-gui, 24-iot-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "sys.modules patching for lazy ML import mocking (torch/cv2/modelB4 injected only inside run())"
    - "Config-driven ROI: wear_cfg.get() with fallback defaults for all ROI constants"
    - "importlib.reload() in tests to re-import module with sys.modules mocks active"

key-files:
  created:
    - tests/test_health_calculator.py
    - tests/test_ldc_worker.py
  modified:
    - config/config.yaml
    - src/services/camera/ldc_worker.py
    - src/services/camera/health_calculator.py

key-decisions:
  - "Use real numpy in sys.modules mock for ldc_worker tests — mocking numpy causes astype(np.uint8) to break"
  - "Convert _run_ldc_inference and _compute_wear from @staticmethod to instance methods to access self._roi_* attributes"
  - "importlib.reload() inside _mock_ml_libraries context ensures run() picks up mocked torch/cv2 for that test"

patterns-established:
  - "LDC test pattern: sys.modules mock with real numpy + fake cv2/torch/modelB4 + os.path.isfile patch"
  - "fast_stop pattern: patch worker._stop_event.wait to set stop after first iteration"

requirements-completed: [DET-03, DET-04, DET-05, DET-06]

# Metrics
duration: 5min
completed: 2026-03-26
---

# Phase 21 Plan 02: AI Detection Pipeline — LDC Config Migration & Tests Summary

**Wear ROI constants migrated from ldc_worker.py module-level to config.yaml camera.wear, plus 13 new unit tests proving DET-03/04/05/06 for LDCWorker and HealthCalculator**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-25T21:55:51Z
- **Completed:** 2026-03-26T22:00:49Z
- **Tasks:** 2
- **Files modified:** 5 (3 modified + 2 created)

## Accomplishments
- Migrated 7 ROI constants (TOP_LINE_Y, BOTTOM_LINE_Y, _ROI_X_CENTER_N, _ROI_Y_CENTER_N, _ROI_WIDTH_N, _ROI_HEIGHT_N, _BGR_MEAN) from module-level to config.yaml camera.wear section, read via `wear_cfg.get()` in `__init__`
- Converted `_run_ldc_inference` and `_compute_wear` from `@staticmethod` to instance methods, replacing all constant references with `self._*` attributes
- Added Google-style docstrings with Args/Returns to both converted methods; added module docstring to health_calculator.py
- 8 HealthCalculator unit tests: broken percentage (normal/zero-teeth/clamped), saw health formula (perfect/mixed/zero-teeth+wear), Turkish status labels, CSS color codes
- 5 LDCWorker unit tests: lightweight import (DET-06), config ROI loading (D-06), wear+health publishing (DET-03/05), DB guard (D-04), stop lifecycle

## Task Commits

1. **Task 1: Migrate wear ROI constants and audit convention** - `9d37a36` (feat)
2. **Task 2: Write unit tests for LDCWorker and HealthCalculator** - `d05993b` (test)

## Files Created/Modified
- `config/config.yaml` - Added 7 wear ROI keys to camera.wear section
- `src/services/camera/ldc_worker.py` - Removed module constants, added config-driven attrs, converted static methods to instance methods, added docstrings
- `src/services/camera/health_calculator.py` - Added module docstring
- `tests/test_health_calculator.py` - 8 pure unit tests for HealthCalculator formula and labels
- `tests/test_ldc_worker.py` - 5 mock-based unit tests for LDCWorker lifecycle and output

## Decisions Made
- Used real numpy in the sys.modules mock (not a MagicMock): mocking numpy breaks `astype(np.uint8)` inside inference loop
- Used `importlib.reload()` inside `_mock_ml_libraries` context so the `run()` method picks up mocked torch/cv2/modelB4 even after initial module import
- `fast_stop` pattern (set stop after first wait call) reused from test_detection_worker.py for consistent test structure

## Deviations from Plan

None — plan executed exactly as written. The `_ROI_Y_CENTER_N` and `_ROI_HEIGHT_N` constants were also migrated (plan mentioned them in the config spec) even though they weren't explicitly called out in the removal list; their instance attribute counterparts (`self._roi_y_center_n`, `self._roi_height_n`) were added for completeness per the config block.

## Issues Encountered
- First test run for `test_publishes_wear_and_health` failed with `IndexError: list index out of range` in `preds_uint8[-1]` — root cause: mock `torch.sigmoid.return_value` chain wasn't properly set up for `.cpu().detach().numpy()`. Fixed by using a separate `sigmoid_result` MagicMock with the correct chain.
- Real numpy was needed for `mock_np` instead of a `MagicMock()` — discovered when `astype(np.uint8)` returned a MagicMock instead of a uint8 array. Fixed by assigning `mock_np = np`.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- LDCWorker fully tested and config-driven; ready for integration with camera lifecycle (Phase 22)
- HealthCalculator proven correct via 8 formula/label/color tests; safe to consume in GUI (Phase 22) and IoT (Phase 24)
- config.yaml camera.wear section complete with all ROI parameters; any deployment with different camera geometry can override without code changes

---
*Phase: 21-ai-detection-pipeline*
*Completed: 2026-03-26*
