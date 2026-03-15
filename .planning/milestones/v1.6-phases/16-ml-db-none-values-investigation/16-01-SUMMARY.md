---
phase: 16-ml-db-none-values-investigation
plan: 01
subsystem: database
tags: [sqlite, ml, logging, data-integrity]

# Dependency graph
requires:
  - phase: 01-ml-schema-update
    provides: ml_predictions table schema with yeni_kesme_hizi, yeni_inme_hizi, katsayi columns
provides:
  - ML prediction logging with all 11 columns populated
  - Complete ML decision traceability
affects: [ml-analysis, data-analysis, debugging]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Deferred logging pattern (log after calculation, not before)
    - Tuple return for preserving intermediate values

key-files:
  created:
    - .planning/phases/16-ml-db-none-values-investigation/16-INVESTIGATION.md
  modified:
    - src/services/control/ml_controller.py

key-decisions:
  - "Log speed_changes values (calculated), not *_target values (threshold-dependent)"
  - "Log self.katsayi directly (ml_output already has katsayi applied)"
  - "Return tuple from _predict_coefficient() to preserve input_df for logging"

patterns-established:
  - "Deferred logging: log after all computed values available, not during computation"

# Metrics
duration: 3min
completed: 2026-02-04
---

# Phase 16 Plan 01: ML DB None Values Fix Summary

**Fixed ML prediction logging to populate yeni_kesme_hizi, yeni_inme_hizi, katsayi fields by moving logging after speed calculation and updating INSERT statement to include all 11 columns**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-04
- **Completed:** 2026-02-04
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Fixed schema-code mismatch where INSERT only wrote 8 of 11 columns
- Moved `_log_ml_prediction()` call from `_predict_coefficient()` to after `_calculate_new_speeds()` in `calculate_speeds()`
- New ML prediction records will now have complete data for analysis
- Created investigation report documenting root cause and fix

## Task Commits

Each task was committed atomically:

1. **Task 1: Refactor ML prediction logging to include missing fields** - `7d3bd29` (fix)
2. **Task 2: Document root cause and fix in investigation report** - `ec35596` (docs)

## Files Created/Modified

- `src/services/control/ml_controller.py` - Updated `_log_ml_prediction()` signature, INSERT statement, moved logging call, modified `_predict_coefficient()` return type
- `.planning/phases/16-ml-db-none-values-investigation/16-INVESTIGATION.md` - Root cause analysis, fix details, verification method

## Decisions Made

- **Log calculated speeds, not threshold-dependent targets:** `speed_changes['kesme_hizi']` and `speed_changes['inme_hizi']` capture all ML decisions, not just ones that exceeded write threshold
- **Return tuple from _predict_coefficient():** Changed return from `float` to `Tuple[float, DataFrame]` to preserve `input_df` for logging at the new call site
- **Log self.katsayi directly:** The `ml_output` column already has katsayi applied (coefficient * katsayi), so `katsayi` column stores the raw multiplier value

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- ML prediction logging now complete with all fields
- Historical records retain NULL values (cannot be reconstructed)
- New records will have numeric values in all three columns
- Verification query: `SELECT yeni_kesme_hizi, yeni_inme_hizi, katsayi FROM ml_predictions ORDER BY id DESC LIMIT 10;`

---
*Phase: 16-ml-db-none-values-investigation*
*Completed: 2026-02-04*
