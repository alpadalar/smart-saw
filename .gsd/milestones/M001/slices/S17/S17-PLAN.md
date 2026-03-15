# S17: ML DB Schema Update

**Goal:** Add kesim_id, makine_id, serit_id, malzeme_cinsi traceability columns to ml_predictions table for historical cut session analysis.
**Demo:** ML predictions include traceability fields; historical analysis queries can join on kesim_id.

## Must-Haves


## Tasks


## Files Likely Touched

- `src/services/database/schemas.py`
- `src/services/control/ml_controller.py`
