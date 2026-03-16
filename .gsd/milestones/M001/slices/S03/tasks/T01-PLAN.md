# T01: 03-data-population 01

**Slice:** S03 — **Milestone:** M001

## Description

Update ML prediction logging to include serit_motor_tork and kafa_yuksekligi values.

Purpose: Populate the new ML schema columns with actual sensor data for historical torque and head height analysis.
Output: ML predictions now include torque and head height values when logged to database.

## Files

- `src/services/control/ml_controller.py`
