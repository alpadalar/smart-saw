---
phase: 17-ml-db-schema-update
plan: 01
subsystem: database
tags: [sqlite, ml-predictions, schema, traceability, ml-controller]

# Dependency graph
requires:
  - phase: 16-ml-db-none-values-investigation
    provides: Root cause analysis confirming missing traceability columns and fix strategy
provides:
  - SCHEMA_ML_DB with 4 traceability columns (kesim_id, makine_id, serit_id, malzeme_cinsi) and kesim_id index
  - _log_ml_prediction method accepting and inserting 4 new Optional traceability parameters
  - calculate_speeds call site passing processed_data.cutting_session_id and raw_data fields
affects: [future-ml-analysis, historical-cut-session-queries, anomaly-reporting]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Nullable traceability columns: all new columns omit NOT NULL and DEFAULT — NULL backward-compatible with existing records"
    - "Falsy-to-None conversion at call site: `raw_data.field if raw_data.field else None` converts 0/empty-string to NULL for DB storage"
    - "Optional parameters with defaults: new _log_ml_prediction params default to None — existing call sites not broken"

key-files:
  created: []
  modified:
    - src/services/database/schemas.py
    - src/services/control/ml_controller.py

key-decisions:
  - "NULL defaults for new columns — no NOT NULL, no DEFAULT — preserves all existing ml_predictions records without migration"
  - "Falsy-to-None conversion at call site: store NULL when source value is 0 or empty string, consistent with user decision"
  - "kesim_id index added (idx_ml_kesim_id), no indexes on makine_id/serit_id/malzeme_cinsi (low cardinality on single-machine deployment)"
  - "Optional parameters appended to _log_ml_prediction signature — backward compatible, existing callers not broken"

patterns-established:
  - "Traceability columns pattern: append kesim_id/makine_id/serit_id/malzeme_cinsi as nullable columns to any event/prediction table"

requirements-completed: [MLDB-01, MLDB-02, MLDB-03, MLDB-04]

# Metrics
duration: 2min
completed: 2026-03-16
---

# Phase 17 Plan 01: ML DB Schema Update Summary

**Extended ml_predictions table with 4 nullable traceability columns (kesim_id, makine_id, serit_id, malzeme_cinsi) and updated _log_ml_prediction to insert them from ProcessedData/RawSensorData at cut time.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-15T21:15:21Z
- **Completed:** 2026-03-15T21:17:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- SCHEMA_ML_DB updated from 11 to 15 columns with 4 nullable traceability fields and idx_ml_kesim_id index
- _log_ml_prediction extended with 4 Optional parameters and 15-column INSERT SQL (was 11)
- calculate_speeds call site now passes processed_data.cutting_session_id and raw_data.makine_id/serit_id/malzeme_cinsi
- SQLite validated: schema creates correct 16-column table (id + 15 data columns)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add traceability columns to SCHEMA_ML_DB and kesim_id index** - `ccbdb5f` (feat)
2. **Task 2: Extend _log_ml_prediction to accept and INSERT traceability fields** - `0f49512` (feat)

**Plan metadata:** (docs commit pending)

## Files Created/Modified

- `src/services/database/schemas.py` - Added kesim_id INTEGER, makine_id INTEGER, serit_id INTEGER, malzeme_cinsi TEXT columns and idx_ml_kesim_id index to SCHEMA_ML_DB
- `src/services/control/ml_controller.py` - Extended _log_ml_prediction signature and INSERT SQL; updated calculate_speeds call site to pass traceability values

## Decisions Made

- NULL defaults for new columns — no NOT NULL, no DEFAULT — preserves all existing ml_predictions records without migration
- Falsy-to-None conversion at call site: `raw_data.field if raw_data.field else None` converts 0/empty-string to NULL
- Index only on kesim_id (query anchor for cut session analysis); no indexes on makine_id/serit_id/malzeme_cinsi
- Optional parameters with defaults appended to _log_ml_prediction — backward compatible

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Schema updated; new columns will be populated starting from next application run
- Existing ml_predictions records are unaffected (all new columns are nullable)
- Historical analysis queries linking ML predictions to cut sessions, machines, blades, and materials are now possible
- Phase 17 complete — ready for Phase 18

---
*Phase: 17-ml-db-schema-update*
*Completed: 2026-03-16*
