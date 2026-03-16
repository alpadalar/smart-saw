---
id: T01
parent: S23
milestone: M001
provides:
  - Camera vision fields (broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status) wired through IoT telemetry pipeline
key_files:
  - src/services/iot/thingsboard.py
  - src/services/iot/mqtt_client.py
  - src/services/processing/data_processor.py
  - src/core/lifecycle.py
  - config/config.yaml
key_decisions:
  - Camera fields merged into existing field_mapping dict rather than a separate telemetry object — keeps ThingsBoard payload flat
  - Snapshot extraction explicitly whitelists 6 scalar fields, excluding latest_frame (binary) by design
patterns_established:
  - vision_data=None optional parameter threaded through queue_telemetry → format_telemetry chain
  - Camera snapshot try/except with warning log in processing loop — non-fatal, continues without vision data
observability_surfaces:
  - "Camera snapshot failed" warning log in data_processor processing loop
duration: 15m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Wire camera telemetry through IoT pipeline

**Threaded CameraResultsStore vision data through formatter → mqtt → pipeline → lifecycle with full backward compatibility**

## What Happened

Added `vision_data=None` parameter to `ThingsBoardFormatter.format_telemetry()` — when provided, merges 6 camera fields (broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status) into the existing field_mapping dict before the telemetry_fields whitelist filter runs. Added matching `vision_data=None` to `MQTTService.queue_telemetry()` which forwards to the formatter. Extended `DataProcessingPipeline.__init__()` with `camera_results_store=None`, and in the processing loop step 6, calls `snapshot()` on the store to extract vision data each cycle (with try/except + warning log). Lifecycle's `_init_data_pipeline()` now passes `self.camera_results_store` to the pipeline constructor. Added all 6 camera field names to `config/config.yaml` telemetry_fields under a "# Camera vision" group.

## Verification

- `py_compile` — all 4 Python files compile clean
- Import checks — `ThingsBoardFormatter`, `MQTTService`, `DataProcessingPipeline` all import successfully
- Signature grep — `format_telemetry(self, processed_data, vision_data=None)`, `queue_telemetry(self, processed_data, vision_data=None)`, `camera_results_store=None` all confirmed
- Lifecycle grep — `camera_results_store=self.camera_results_store` present in `_init_data_pipeline()`
- Config grep — all 6 camera field names present in telemetry_fields
- Backward compat test — `format_telemetry(pd)` without vision_data produces no camera keys in output
- Vision merge test — `format_telemetry(pd, vision_data={...})` includes all 6 camera fields with correct values in output

### Slice-level verification status (all pass — single-task slice)

- [x] py_compile all 4 modified Python files
- [x] Import check: ThingsBoardFormatter
- [x] Import check: MQTTService
- [x] Import check: DataProcessingPipeline
- [x] Backward compat: format_telemetry(processed_data) without vision_data still works
- [x] Vision merge: format_telemetry with vision_data includes all 6 fields
- [x] Config: camera field names present in telemetry_fields
- [x] Lifecycle: _init_data_pipeline passes self.camera_results_store

## Diagnostics

- Grep `"Camera snapshot failed"` in logs to detect camera↔pipeline integration issues at runtime
- Camera fields in ThingsBoard payload values dict confirm end-to-end flow; their absence confirms camera is disabled/None
- No new status endpoints — uses existing MQTT stats for transport-level monitoring

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/services/iot/thingsboard.py` — Added `vision_data=None` param to `format_telemetry()`, merges 6 camera fields into field_mapping
- `src/services/iot/mqtt_client.py` — Added `vision_data=None` param to `queue_telemetry()`, forwards to formatter
- `src/services/processing/data_processor.py` — Added `camera_results_store=None` to constructor, snapshot extraction in processing loop step 6
- `src/core/lifecycle.py` — Passes `camera_results_store=self.camera_results_store` to DataProcessingPipeline
- `config/config.yaml` — Added 6 camera field names to telemetry_fields list
