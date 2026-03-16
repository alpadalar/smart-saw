# S23: IoT Integration

**Goal:** Camera telemetry fields (broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status) included in ThingsBoard telemetry payload when camera.enabled=true.

**Demo:** When CameraResultsStore has detection/wear data, `format_telemetry()` output contains camera vision fields alongside existing sensor fields. When camera is disabled or store is None, telemetry is identical to current behavior.

## Must-Haves

- ThingsBoardFormatter.format_telemetry() accepts optional vision_data dict and merges 6 camera fields into field_mapping
- MQTTService.queue_telemetry() accepts optional vision_data and forwards to formatter
- DataProcessingPipeline accepts optional camera_results_store, calls snapshot() per cycle, passes vision data to queue_telemetry()
- Lifecycle passes self.camera_results_store to DataProcessingPipeline constructor
- Config telemetry_fields list includes the 6 camera field names
- All new parameters default to None — backward compatible, zero behavior change when camera is disabled

## Proof Level

- This slice proves: integration
- Real runtime required: no (contract-level — no camera hardware in dev)
- Human/UAT required: no

## Verification

- `py_compile` all 4 modified Python files
- Import check: `python -c "from src.services.iot.thingsboard import ThingsBoardFormatter"`
- Import check: `python -c "from src.services.iot.mqtt_client import MQTTService"`
- Import check: `python -c "from src.services.processing.data_processor import DataProcessingPipeline"`
- Backward compat: `format_telemetry(processed_data)` without vision_data still works
- Vision merge: `format_telemetry(processed_data, vision_data={'broken_count': 3, 'tooth_count': 28, 'crack_count': 1, 'wear_percentage': 15.5, 'health_score': 72.0, 'health_status': 'warning'})` includes all 6 fields in output values
- Config: camera field names present in `iot.thingsboard.telemetry_fields`
- Lifecycle: `_init_data_pipeline` passes `self.camera_results_store` to pipeline constructor

## Integration Closure

- Upstream surfaces consumed: `CameraResultsStore.snapshot()` (S20), `ThingsBoardFormatter.format_telemetry()`, `MQTTService.queue_telemetry()`, `DataProcessingPipeline.__init__()`, `lifecycle._init_data_pipeline()`
- New wiring introduced in this slice: camera_results_store threaded through pipeline → mqtt → formatter chain
- What remains before the milestone is truly usable end-to-end: S24 (Camera GUI page)

## Tasks

- [ ] **T01: Wire camera telemetry through IoT pipeline** `est:30m`
  - Why: Thread CameraResultsStore.snapshot() data from lifecycle through DataProcessingPipeline → MQTTService → ThingsBoardFormatter, add camera field names to config whitelist
  - Files: `src/services/iot/thingsboard.py`, `src/services/iot/mqtt_client.py`, `src/services/processing/data_processor.py`, `src/core/lifecycle.py`, `config/config.yaml`
  - Do: (1) ThingsBoardFormatter.format_telemetry — add `vision_data=None` param, merge 6 fields (broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status) into field_mapping when vision_data is not None. (2) MQTTService.queue_telemetry — add `vision_data=None` param, forward to `self.formatter.format_telemetry(processed_data, vision_data=vision_data)`. (3) DataProcessingPipeline — add `camera_results_store=None` constructor param, store as attribute; in processing loop step 6 when iot_service and camera_results_store are both available, call `self.camera_results_store.snapshot()` and pass as vision_data to queue_telemetry. (4) Lifecycle._init_data_pipeline — pass `self.camera_results_store` as kwarg. (5) config.yaml — add 6 camera field names to telemetry_fields list under a "# Camera vision" comment group.
  - Verify: py_compile all modified files; import checks pass; format_telemetry with vision_data includes camera fields in output; format_telemetry without vision_data unchanged; config has camera fields listed
  - Done when: Camera vision fields flow from CameraResultsStore through the IoT pipeline to ThingsBoard telemetry payload, with full backward compatibility when camera is disabled

## Files Likely Touched

- `src/services/iot/thingsboard.py`
- `src/services/iot/mqtt_client.py`
- `src/services/processing/data_processor.py`
- `src/core/lifecycle.py`
- `config/config.yaml`
