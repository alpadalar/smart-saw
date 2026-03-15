# S03: Data Population

**Goal:** Update ML prediction logging to include serit_motor_tork and kafa_yuksekligi values.
**Demo:** Update ML prediction logging to include serit_motor_tork and kafa_yuksekligi values.

## Must-Haves


## Tasks

- [x] **T01: 03-data-population 01** `est:2min`
  - Update ML prediction logging to include serit_motor_tork and kafa_yuksekligi values.

Purpose: Populate the new ML schema columns with actual sensor data for historical torque and head height analysis.
Output: ML predictions now include torque and head height values when logged to database.
- [x] **T02: 03-data-population 02** `est:1min`
  - Update anomaly event logging to include kafa_yuksekligi (head height) value.

Purpose: Record head height at time of anomaly detection for historical analysis - knowing where the saw head was when an anomaly occurred provides context for diagnosing cutting issues.
Output: Anomaly events now include kafa_yuksekligi value when logged to database.

## Files Likely Touched

- `src/services/control/ml_controller.py`
- `src/services/processing/anomaly_tracker.py`
- `src/services/processing/data_processor.py`
