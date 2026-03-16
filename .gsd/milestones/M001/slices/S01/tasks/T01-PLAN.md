# T01: 01-ml-schema-update 01

**Slice:** S01 — **Milestone:** M001

## Description

Update ML predictions database schema to include torque and head height fields.

Purpose: Enable historical analysis of torque and head height data alongside ML predictions.
Output: Updated SCHEMA_ML_DB with serit_motor_tork and kafa_yuksekligi columns.

## Files

- `src/services/database/schemas.py`
