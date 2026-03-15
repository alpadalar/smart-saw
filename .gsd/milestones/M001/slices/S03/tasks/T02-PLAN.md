# T02: 03-data-population 02

**Slice:** S03 — **Milestone:** M001

## Description

Update anomaly event logging to include kafa_yuksekligi (head height) value.

Purpose: Record head height at time of anomaly detection for historical analysis - knowing where the saw head was when an anomaly occurred provides context for diagnosing cutting issues.
Output: Anomaly events now include kafa_yuksekligi value when logged to database.

## Files

- `src/services/processing/anomaly_tracker.py`
- `src/services/processing/data_processor.py`
