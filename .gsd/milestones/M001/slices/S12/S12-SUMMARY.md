---
id: S12
parent: M001
milestone: M001
provides:
  - ML speed calculations using averaged buffer values (parity with old code)
  - torque_to_current without clamping (parity with old code)
requires: []
affects: []
key_files: []
key_decisions:
  - "Use averaged speeds from buffers instead of raw current values for percentage calculations"
  - "Remove torque clamping to match old code polynomial behavior"
patterns_established:
  - "get_averaged_speeds() returns (avg_kesme_hizi, avg_inme_hizi) from buffers"
observability_surfaces: []
drill_down_paths: []
duration: 1min
verification_result: passed
completed_at: 2026-01-28
blocker_discovered: false
---
# S12: Ml Prediction Parity

**# Phase 12 Plan 01: ML Prediction Parity Fix Summary**

## What Happened

# Phase 12 Plan 01: ML Prediction Parity Fix Summary

**Aligned ML speed calculation logic with old codebase by using averaged buffer values instead of raw current values**

## Performance

- **Duration:** 1 min
- **Started:** 2026-01-28T09:20:38Z
- **Completed:** 2026-01-28T09:21:54Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Added get_averaged_speeds() method to preprocessor for buffer-averaged speed values
- Modified ml_controller to use averaged speeds for percentage calculations (matches old code)
- Removed torque percentage clamping in torque_to_current() (matches old code behavior)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add method to get averaged speeds from preprocessor** - `d8c2db1` (feat)
2. **Task 2: Modify _calculate_new_speeds to use averaged speeds** - `81645da` (feat)
3. **Task 3: Remove torque percentage clamping** - `db72b1a` (fix)

## Files Created/Modified

- `src/ml/preprocessor.py` - Added get_averaged_speeds() method, removed torque clamping
- `src/services/control/ml_controller.py` - Uses averaged speeds from preprocessor buffers

## Decisions Made

1. **Use averaged speeds from buffers**: The old code used `_get_buffer_averages()` to get averaged kesme_hizi and inme_hizi before calculating speed changes. The new code was incorrectly using `raw_data.serit_kesme_hizi` directly.

2. **Remove torque clamping**: The old code passed torque values directly to the polynomial without clamping to [0, 100]. The new code had added clamping which caused different behavior.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- ML speed calculations now match old codebase behavior exactly
- Ready for testing to verify prediction parity
- No blockers for next plan

---
*Phase: 12-ml-prediction-parity*
*Completed: 2026-01-28*
