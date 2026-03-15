# S01: Ml Schema Update

**Goal:** Update ML predictions database schema to include torque and head height fields.
**Demo:** Update ML predictions database schema to include torque and head height fields.

## Must-Haves


## Tasks

- [x] **T01: 01-ml-schema-update 01** `est:1min`
  - Update ML predictions database schema to include torque and head height fields.

Purpose: Enable historical analysis of torque and head height data alongside ML predictions.
Output: Updated SCHEMA_ML_DB with serit_motor_tork and kafa_yuksekligi columns.

## Files Likely Touched

- `src/services/database/schemas.py`
