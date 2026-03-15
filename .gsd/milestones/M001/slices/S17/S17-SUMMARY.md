---
id: S17
parent: M001
milestone: M001
provides:
  - SCHEMA_ML_DB with 4 traceability columns (kesim_id, makine_id, serit_id, malzeme_cinsi) and kesim_id index
  - _log_ml_prediction method accepting and inserting 4 new Optional traceability parameters
  - calculate_speeds call site passing processed_data.cutting_session_id and raw_data fields
requires: []
affects: []
key_files:
  - "src/services/database/schemas.py"
  - "src/services/control/ml_controller.py"
key_decisions:
  - "NULL defaults for new columns — preserves existing records without migration"
  - "Falsy-to-None conversion at call site — store NULL when source is 0 or empty string"
  - "Index only on kesim_id — low cardinality on makine_id/serit_id/malzeme_cinsi"
patterns_established:
  - "Traceability columns pattern: append kesim_id/makine_id/serit_id/malzeme_cinsi as nullable columns"
observability_surfaces: []
drill_down_paths: []
duration: 2min
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---
# S17: ML DB Schema Update

**Extended ml_predictions table with 4 nullable traceability columns (kesim_id, makine_id, serit_id, malzeme_cinsi) and updated _log_ml_prediction to insert them from ProcessedData/RawSensorData at cut time.**

## What Happened

Added traceability columns to the ML predictions database to enable historical analysis linking predictions to cut sessions, machines, blades, and materials.

## Accomplishments

- SCHEMA_ML_DB updated from 11 to 15 columns with 4 nullable traceability fields and idx_ml_kesim_id index
- _log_ml_prediction extended with 4 Optional parameters and 15-column INSERT SQL
- calculate_speeds call site now passes processed_data.cutting_session_id and raw_data fields

## Files Changed

- `src/services/database/schemas.py` — Added 4 traceability columns and index
- `src/services/control/ml_controller.py` — Extended logging method and call site

## Commits

1. **ccbdb5f** — feat: add traceability columns to SCHEMA_ML_DB and kesim_id index
2. **0f49512** — feat: extend _log_ml_prediction to accept and INSERT traceability fields

---
*Completed: 2026-03-16*
