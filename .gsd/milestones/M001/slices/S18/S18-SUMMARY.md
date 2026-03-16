---
id: S18
parent: M001
milestone: M001
provides:
  - anomaly_events table with makine_id, serit_id, malzeme_cinsi traceability columns
  - record_anomaly accepting all three traceability parameters
  - _save_anomaly_to_db inserting 9 columns including traceability
requires: []
affects: []
key_files:
  - "src/services/database/schemas.py"
  - "src/services/processing/anomaly_tracker.py"
  - "src/services/processing/data_processor.py"
key_decisions:
  - "NULL defaults — preserves existing records"
  - "Falsy-to-None conversion at call site (matches Phase 17 ML pattern)"
  - "No indexes on traceability columns (low cardinality)"
patterns_established:
  - "Traceability pattern: add makine_id/serit_id/malzeme_cinsi as nullable, falsy-to-None at call site"
observability_surfaces: []
drill_down_paths: []
duration: 2min
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---
# S18: Anomaly DB Schema Update

**anomaly_events table extended with makine_id, serit_id, malzeme_cinsi nullable traceability columns; record_anomaly and INSERT updated to 9-column write; call site passes raw_data fields with falsy-to-None conversion**

## What Happened

Added traceability columns to anomaly events database, symmetrically matching the ML DB schema update in S17.

## Accomplishments

- Added 3 nullable traceability columns to anomaly_events table schema
- Extended record_anomaly and _save_anomaly_to_db signatures for new fields
- Updated INSERT SQL from 6 to 9 columns
- Updated data_processor.py call site with falsy-to-None conversion

## Files Changed

- `src/services/database/schemas.py` — Added 3 nullable columns
- `src/services/processing/anomaly_tracker.py` — Extended signatures and INSERT
- `src/services/processing/data_processor.py` — Added traceability args to call site

## Commits

1. **aaff49b** — feat: add traceability columns to SCHEMA_ANOMALY_DB
2. **f68ca37** — feat: extend record_anomaly and call site with traceability parameters

---
*Completed: 2026-03-16*
