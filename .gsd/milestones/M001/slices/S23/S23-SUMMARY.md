---
id: S23
parent: M001
milestone: M001
provides:
  - Camera vision telemetry fields (broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status) in ThingsBoard IoT payload
requires:
  - slice: S22
    provides: CameraResultsStore lifecycle wiring, camera_results_store attribute on lifecycle
  - slice: S21
    provides: CameraResultsStore.snapshot() API with detection/wear data
affects:
  - S24
key_files:
  - src/services/iot/thingsboard.py
  - src/services/iot/mqtt_client.py
  - src/services/processing/data_processor.py
  - src/core/lifecycle.py
  - config/config.yaml
key_decisions:
  - Camera fields merged into existing field_mapping dict rather than a separate telemetry object — keeps ThingsBoard payload flat
  - Snapshot extraction explicitly whitelists 6 scalar fields, excluding latest_frame (binary) by design
  - vision_data=None optional parameter threaded through queue_telemetry → format_telemetry chain — full backward compatibility
  - Camera snapshot failures logged as warning, non-fatal — processing continues without vision data
patterns_established:
  - Optional vision_data parameter threaded through IoT pipeline (pipeline → mqtt → formatter)
  - Try/except with warning log for non-critical camera data extraction in processing loop
observability_surfaces:
  - "Camera snapshot failed" warning log in data_processor processing loop
  - Camera fields presence/absence in ThingsBoard payload values confirms camera enabled/disabled state
drill_down_paths:
  - .gsd/milestones/M001/slices/S23/tasks/T01-SUMMARY.md
duration: 15m
verification_result: passed
completed_at: 2026-03-16
---

# S23: IoT Integration

**Camera vision telemetry fields wired through DataProcessingPipeline → MQTTService → ThingsBoardFormatter with full backward compatibility when camera is disabled**

## What Happened

Threaded CameraResultsStore vision data through the existing IoT telemetry pipeline. ThingsBoardFormatter.format_telemetry() gained a `vision_data=None` parameter — when provided, 6 camera fields (broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status) are merged into the existing field_mapping dict before the telemetry_fields whitelist filter runs. MQTTService.queue_telemetry() received the same parameter and forwards to the formatter. DataProcessingPipeline constructor accepts `camera_results_store=None`, and its processing loop calls snapshot() on the store each cycle to extract vision data (wrapped in try/except with warning log). Lifecycle._init_data_pipeline() passes self.camera_results_store to the pipeline. All 6 camera field names were added to config.yaml's telemetry_fields whitelist.

The design keeps the ThingsBoard payload flat — camera fields sit alongside sensor fields in the same values dict. The snapshot extraction explicitly whitelists only the 6 scalar fields, excluding latest_frame (binary image data) by design.

## Verification

- py_compile: all 4 modified Python files compile clean
- Import checks: ThingsBoardFormatter, MQTTService, DataProcessingPipeline all import successfully
- Signature confirmation: vision_data=None present in format_telemetry and queue_telemetry; camera_results_store=None in pipeline constructor
- Lifecycle wiring: camera_results_store=self.camera_results_store in _init_data_pipeline()
- Config: all 6 camera field names present in telemetry_fields
- Backward compat: format_telemetry(processed_data) without vision_data produces zero camera keys
- Vision merge: format_telemetry(processed_data, vision_data={...}) includes all 6 camera fields with correct values
- Observability: "Camera snapshot failed" warning log present in data_processor.py

## Requirements Advanced

- DATA-02 — Camera vision fields now flow through IoT pipeline to ThingsBoard payload. Contract proven with functional test (formatter accepts vision_data, produces correct output). Runtime validation requires camera hardware + ThingsBoard instance.

## Requirements Validated

- none

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

None.

## Known Limitations

- Runtime validation requires camera hardware and ThingsBoard instance — contract-level proof only
- Camera snapshot failures are logged but not counted in a separate stats counter (uses existing MQTT error stats for transport)

## Follow-ups

- none

## Files Created/Modified

- `src/services/iot/thingsboard.py` — Added vision_data=None param to format_telemetry(), merges 6 camera fields into field_mapping
- `src/services/iot/mqtt_client.py` — Added vision_data=None param to queue_telemetry(), forwards to formatter
- `src/services/processing/data_processor.py` — Added camera_results_store=None to constructor, snapshot extraction in processing loop step 6
- `src/core/lifecycle.py` — Passes camera_results_store=self.camera_results_store to DataProcessingPipeline
- `config/config.yaml` — Added 6 camera field names to telemetry_fields list

## Forward Intelligence

### What the next slice should know
- CameraResultsStore.snapshot() returns a dict with keys including latest_frame (bytes), broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status. The IoT pipeline only uses the 6 scalar fields — the GUI (S24) will need latest_frame for the live feed display.
- The ThingsBoard payload is flat — camera fields are peers of sensor fields, not nested. The GUI should read from CameraResultsStore directly, not from telemetry.

### What's fragile
- The 6-field whitelist in thingsboard.py is hardcoded as a tuple — if CameraResultsStore.snapshot() key names change, the formatter silently drops the renamed fields (no error, just missing data). The config.yaml telemetry_fields list must also stay in sync.

### Authoritative diagnostics
- Grep for "Camera snapshot failed" in logs — this is the single diagnostic signal for camera↔pipeline integration issues at runtime
- Camera field presence in ThingsBoard payload values dict confirms end-to-end flow; absence confirms camera is disabled/None

### What assumptions changed
- No assumptions changed — slice executed exactly as planned, single-task slice with clean implementation
