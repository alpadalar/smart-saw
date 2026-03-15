---
id: S16
parent: M001
milestone: M001
provides:
  - ML prediction logging with all 11 columns populated
  - Complete ML decision traceability
requires: []
affects: []
key_files:
  - "src/services/control/ml_controller.py"
key_decisions:
  - "Log calculated speeds, not threshold-dependent targets"
  - "Log self.katsayi directly (ml_output already has katsayi applied)"
  - "Return tuple from _predict_coefficient() to preserve input_df for logging"
  - "Deferred logging pattern: log after all computed values available, not during computation"
patterns_established:
  - "Deferred logging: log after all computed values available, not during computation"
observability_surfaces: []
drill_down_paths: []
duration: 3min
verification_result: passed
completed_at: 2026-02-04
blocker_discovered: false
---
# S16: ML DB None Values Investigation

**Fixed ML prediction logging to populate yeni_kesme_hizi, yeni_inme_hizi, katsayi fields by moving logging after speed calculation and updating INSERT statement to include all 11 columns**

## What Happened

Fixed schema-code mismatch where INSERT only wrote 8 of 11 columns. Moved `_log_ml_prediction()` call from `_predict_coefficient()` to after `_calculate_new_speeds()` in `calculate_speeds()`.

## Accomplishments

- Fixed INSERT statement to write all 11 columns (was 8)
- Moved logging call to after speed calculation for complete data
- Changed `_predict_coefficient()` return type to `Tuple[float, DataFrame]` to preserve `input_df`
- Created investigation report documenting root cause

## Files Changed

- `src/services/control/ml_controller.py` — Updated signature, INSERT statement, moved logging call
- `.planning/phases/16-ml-db-none-values-investigation/16-INVESTIGATION.md` — Root cause analysis

## Commits

1. **7d3bd29** — fix: refactor ML prediction logging to include missing fields
2. **ec35596** — docs: document root cause and fix in investigation report

---
*Completed: 2026-02-04*
