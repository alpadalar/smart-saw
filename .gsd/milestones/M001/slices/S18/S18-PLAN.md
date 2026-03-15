# S18: Anomaly DB Schema Update

**Goal:** Add makine_id, serit_id, malzeme_cinsi traceability columns to anomaly_events table, matching ML DB traceability pattern from S17.
**Demo:** Anomaly events include machine/blade/material context; historical analysis across both ML and anomaly databases possible.

## Must-Haves


## Tasks


## Files Likely Touched

- `src/services/database/schemas.py`
- `src/services/processing/anomaly_tracker.py`
- `src/services/processing/data_processor.py`
