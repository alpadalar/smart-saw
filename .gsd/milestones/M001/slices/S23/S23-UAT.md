# S23: IoT Integration — UAT

**Milestone:** M001
**Written:** 2026-03-16

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: Integration is contract-level — camera hardware and ThingsBoard instance not available in dev. All verification is through import checks, py_compile, and functional tests against real domain objects.

## Preconditions

- Python 3.10+ with project dependencies installed
- Working directory is the project root (or worktree)
- No camera hardware required — all tests use constructed domain objects

## Smoke Test

Run `python -c "from src.services.iot.thingsboard import ThingsBoardFormatter"` — should import without error, confirming the modified formatter loads cleanly.

## Test Cases

### 1. Backward compatibility — no vision data

1. Create a ThingsBoardFormatter with a config that includes camera field names in telemetry_fields
2. Create a ProcessedData instance with RawSensorData (e.g., serit_motor_akim_a=12.5)
3. Call `format_telemetry(processed_data)` without vision_data parameter
4. Inspect the returned dict's 'values' key
5. **Expected:** No camera keys (broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status) present in values. Only sensor fields appear.

### 2. Vision data merge — all 6 fields

1. Create a ThingsBoardFormatter with camera field names in telemetry_fields
2. Create a ProcessedData instance with RawSensorData
3. Call `format_telemetry(processed_data, vision_data={'broken_count': 3, 'tooth_count': 28, 'crack_count': 1, 'wear_percentage': 15.5, 'health_score': 72.0, 'health_status': 'warning'})`
4. Inspect the returned dict's 'values' key
5. **Expected:** All 6 camera fields present with exact values: broken_count=3, tooth_count=28, crack_count=1, wear_percentage=15.5, health_score=72.0, health_status='warning'

### 3. MQTTService forwards vision_data

1. Inspect `src/services/iot/mqtt_client.py` line containing `queue_telemetry`
2. **Expected:** Method signature is `queue_telemetry(self, processed_data, vision_data=None)` and body calls `self.formatter.format_telemetry(processed_data, vision_data=vision_data)`

### 4. DataProcessingPipeline accepts camera_results_store

1. Inspect `src/services/processing/data_processor.py` constructor
2. **Expected:** Constructor accepts `camera_results_store=None` parameter and stores it as `self.camera_results_store`
3. Inspect the processing loop (step 6 area)
4. **Expected:** When `self.camera_results_store is not None`, calls `snapshot()`, extracts vision fields, passes as `vision_data` to `queue_telemetry()`

### 5. Lifecycle wiring

1. Inspect `src/core/lifecycle.py` method `_init_data_pipeline`
2. **Expected:** Contains `camera_results_store=self.camera_results_store` in the DataProcessingPipeline constructor call

### 6. Config telemetry_fields

1. Open `config/config.yaml` and find the `telemetry_fields` list under `iot.thingsboard`
2. **Expected:** List includes all 6 camera field names: broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status

### 7. py_compile all modified files

1. Run `python -m py_compile src/services/iot/thingsboard.py`
2. Run `python -m py_compile src/services/iot/mqtt_client.py`
3. Run `python -m py_compile src/services/processing/data_processor.py`
4. Run `python -m py_compile src/core/lifecycle.py`
5. **Expected:** All 4 commands complete with exit code 0, no output

## Edge Cases

### Vision data with missing keys

1. Call `format_telemetry(processed_data, vision_data={'broken_count': 3})` — only 1 of 6 fields provided
2. **Expected:** Only broken_count appears in output values. Other 5 camera fields absent. No error.

### Vision data with empty dict

1. Call `format_telemetry(processed_data, vision_data={})`
2. **Expected:** No camera fields in output. Behaves same as vision_data=None.

### Camera snapshot failure in pipeline

1. Grep for `"Camera snapshot failed"` in `src/services/processing/data_processor.py`
2. **Expected:** Warning log exists inside a try/except block wrapping `self.camera_results_store.snapshot()`. Processing continues with `vision_data = None` on failure.

## Failure Signals

- Import error on any of the 4 modified Python files — indicates syntax or dependency break
- Camera fields appearing in telemetry when vision_data is None — backward compatibility broken
- Camera fields missing when vision_data is provided with all 6 keys — field mapping or whitelist broken
- Missing "Camera snapshot failed" log line — error handling removed or bypassed
- camera_results_store not passed in lifecycle — pipeline won't receive camera data at runtime

## Requirements Proved By This UAT

- DATA-02 — Contract-level proof that camera vision fields flow through IoT pipeline. Formatter accepts vision_data and produces correct output. Runtime proof deferred to camera hardware availability.

## Not Proven By This UAT

- End-to-end runtime telemetry delivery to ThingsBoard (requires MQTT broker + ThingsBoard instance)
- CameraResultsStore.snapshot() returning real detection data (requires camera hardware + AI models)
- Telemetry field values accuracy under real camera conditions

## Notes for Tester

- All tests can be run without camera hardware or ThingsBoard — this is pure contract verification
- The functional test in Test Case 2 can be run as a standalone Python script (construct FakeConfig, RawSensorData, ProcessedData)
- The edge case "Vision data with missing keys" tests the dict comprehension's `if k in vision_data` guard — important for partial camera results during startup
