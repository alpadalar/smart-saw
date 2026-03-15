# T01: 02-anomaly-schema-update 01

**Slice:** S02 — **Milestone:** M001

## Description

Add kafa_yuksekligi (head height) field to anomaly_events table schema.

Purpose: Record head height at time of anomaly detection for historical analysis - knowing where the saw head was when an anomaly occurred provides context for diagnosing cutting issues.
Output: Updated SCHEMA_ANOMALY_DB with kafa_yuksekligi column in anomaly_events table.

## Files

- `src/services/database/schemas.py`
