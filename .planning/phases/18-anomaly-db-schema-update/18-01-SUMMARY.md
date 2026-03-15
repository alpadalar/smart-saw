---
phase: 18-anomaly-db-schema-update
plan: 01
subsystem: database
tags: [sqlite, anomaly-detection, traceability, schema]

# Dependency graph
requires:
  - phase: 17-ml-db-schema-update
    provides: falsy-to-None conversion pattern and traceability column design decisions
provides:
  - anomaly_events table with makine_id, serit_id, malzeme_cinsi traceability columns
  - record_anomaly accepting all three traceability parameters
  - _save_anomaly_to_db inserting 9 columns including traceability
  - call site passing raw_data traceability fields with falsy-to-None conversion
affects: [historical-analysis, anomaly-reporting, data-traceability]

# Tech tracking
tech-stack:
  added: []
  patterns: [falsy-to-None conversion at call site (matches Phase 17 ML pattern), nullable traceability columns with no indexes (low cardinality)]

key-files:
  created: []
  modified:
    - src/services/database/schemas.py
    - src/services/processing/anomaly_tracker.py
    - src/services/processing/data_processor.py

key-decisions:
  - "Anomaly traceability: NULL defaults — no NOT NULL, no DEFAULT — preserves existing records"
  - "Anomaly traceability: Falsy-to-None conversion at call site — store NULL when source is 0 or empty string"
  - "Anomaly traceability: No indexes on makine_id/serit_id/malzeme_cinsi (low cardinality, consistent with Phase 17)"

patterns-established:
  - "Traceability pattern: Add makine_id/serit_id/malzeme_cinsi as nullable columns, propagate through function signatures, convert falsy to None at call site"

requirements-completed: [ANDB-01, ANDB-02, ANDB-03]

# Metrics
duration: 2min
completed: 2026-03-16
---

# Phase 18 Plan 01: Anomaly DB Schema Update Summary

**anomaly_events table extended with makine_id, serit_id, malzeme_cinsi nullable traceability columns; record_anomaly and INSERT updated to 9-column write; call site passes raw_data fields with falsy-to-None conversion**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-16T21:36:33Z
- **Completed:** 2026-03-16T21:37:47Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added three nullable traceability columns to anomaly_events table schema (makine_id, serit_id, malzeme_cinsi)
- Extended record_anomaly and _save_anomaly_to_db signatures to accept and store all three new fields
- Updated INSERT SQL from 6 to 9 columns with matching placeholders and params tuple
- Updated data_processor.py call site to pass raw_data traceability fields with falsy-to-None conversion (matching Phase 17 ML pattern)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add traceability columns to SCHEMA_ANOMALY_DB** - `aaff49b` (feat)
2. **Task 2: Extend record_anomaly and call site with traceability parameters** - `f68ca37` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/services/database/schemas.py` - Added 3 nullable traceability columns to anomaly_events CREATE TABLE
- `src/services/processing/anomaly_tracker.py` - Extended record_anomaly and _save_anomaly_to_db signatures; updated INSERT to 9 columns
- `src/services/processing/data_processor.py` - Added 3 keyword args to record_anomaly call with falsy-to-None conversion

## Decisions Made
None beyond what was already captured in v1.6 decisions from Phase 17 — the same design decisions (nullable columns, no indexes, falsy-to-None) applied symmetrically to anomaly traceability.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 18 complete: v1.6 data traceability is now fully implemented across both ML predictions and anomaly events
- Both anomaly.db and ml.db now record machine/blade/material context for every event
- Historical analysis queries can join on makine_id, serit_id, or malzeme_cinsi in either database

---
*Phase: 18-anomaly-db-schema-update*
*Completed: 2026-03-16*
