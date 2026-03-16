---
estimated_steps: 5
estimated_files: 5
---

# T01: Wire camera telemetry through IoT pipeline

**Slice:** S23 — IoT Integration
**Milestone:** M001

## Description

Thread CameraResultsStore vision data through the existing IoT telemetry chain: formatter → mqtt → pipeline → lifecycle. All changes are additive — every new parameter defaults to None, preserving current behavior when camera is disabled. The 6 camera fields (broken_count, tooth_count, crack_count, wear_percentage, health_score, health_status) merge into the same telemetry dict alongside sensor fields, filtered through the existing telemetry_fields config whitelist.

## Steps

1. **ThingsBoardFormatter** (`src/services/iot/thingsboard.py`):
   - Add `vision_data=None` parameter to `format_telemetry(self, processed_data, vision_data=None)`
   - After the existing `field_mapping.update({...})` block that adds processed data fields (ml_output, torque_guard_active, etc.), add a new block: if `vision_data` is not None, merge the 6 camera fields into `field_mapping` using `field_mapping.update()` — only include keys that exist in vision_data
   - The 6 fields: `broken_count`, `tooth_count`, `crack_count`, `wear_percentage`, `health_score`, `health_status`
   - No other changes — the existing filter logic (`if self.telemetry_fields: for field in ...`) will naturally pick up camera fields once they're in the config list

2. **MQTTService** (`src/services/iot/mqtt_client.py`):
   - Change `queue_telemetry(self, processed_data)` signature to `queue_telemetry(self, processed_data, vision_data=None)`
   - In the body, change `self.formatter.format_telemetry(processed_data)` to `self.formatter.format_telemetry(processed_data, vision_data=vision_data)`

3. **DataProcessingPipeline** (`src/services/processing/data_processor.py`):
   - Add `camera_results_store=None` parameter to `__init__()` after `mqtt_service=None`
   - Store as `self.camera_results_store = camera_results_store`
   - In the processing loop at step 6 (the `if self.iot_service:` block around line 198), before calling `queue_telemetry`, get vision data:
     ```python
     vision_data = None
     if self.camera_results_store is not None:
         try:
             snapshot = self.camera_results_store.snapshot()
             vision_data = {
                 k: snapshot[k] for k in (
                     'broken_count', 'tooth_count', 'crack_count',
                     'wear_percentage', 'health_score', 'health_status'
                 ) if k in snapshot and snapshot[k] is not None
             }
             if not vision_data:
                 vision_data = None
         except Exception as e:
             logger.warning(f"Camera snapshot failed: {e}")
     ```
   - Pass `vision_data=vision_data` to `queue_telemetry()`

4. **Lifecycle** (`src/core/lifecycle.py`):
   - In `_init_data_pipeline()`, add `camera_results_store=self.camera_results_store` to the `DataProcessingPipeline(...)` constructor call
   - Note: `self.camera_results_store` is already initialized to None in `__init__` (line 87) and set to a real instance in `_init_camera()` (line 419). Since `_init_camera()` is called before `_init_data_pipeline()` in the startup sequence, the value will be set correctly.

5. **Config** (`config/config.yaml`):
   - Add camera field names to the `telemetry_fields` list, grouped under a comment:
     ```yaml
     # Camera vision
     - broken_count
     - tooth_count
     - crack_count
     - wear_percentage
     - health_score
     - health_status
     ```
   - Place after the existing "# Anomaly detection" group (which is near the end of the list)

## Must-Haves

- [ ] `format_telemetry` accepts `vision_data=None` — backward compatible
- [ ] `queue_telemetry` accepts `vision_data=None` — backward compatible
- [ ] `DataProcessingPipeline.__init__` accepts `camera_results_store=None` — backward compatible
- [ ] Camera snapshot extracts only the 6 scalar fields, never `latest_frame` (binary)
- [ ] Lifecycle passes `self.camera_results_store` to pipeline constructor
- [ ] Config telemetry_fields includes all 6 camera field names
- [ ] When vision_data is None, telemetry output is identical to current behavior

## Verification

- `cd /media/workspace/smart-saw/.gsd/worktrees/M001 && python -m py_compile src/services/iot/thingsboard.py`
- `cd /media/workspace/smart-saw/.gsd/worktrees/M001 && python -m py_compile src/services/iot/mqtt_client.py`
- `cd /media/workspace/smart-saw/.gsd/worktrees/M001 && python -m py_compile src/services/processing/data_processor.py`
- `cd /media/workspace/smart-saw/.gsd/worktrees/M001 && python -m py_compile src/core/lifecycle.py`
- `cd /media/workspace/smart-saw/.gsd/worktrees/M001 && python -c "from src.services.iot.thingsboard import ThingsBoardFormatter"`
- `cd /media/workspace/smart-saw/.gsd/worktrees/M001 && python -c "from src.services.iot.mqtt_client import MQTTService"`
- `cd /media/workspace/smart-saw/.gsd/worktrees/M001 && python -c "from src.services.processing.data_processor import DataProcessingPipeline"`
- Verify `format_telemetry` signature has `vision_data=None` parameter via `grep`
- Verify `queue_telemetry` signature has `vision_data=None` parameter via `grep`
- Verify pipeline constructor has `camera_results_store=None` parameter via `grep`
- Verify lifecycle passes `camera_results_store=self.camera_results_store` via `grep`
- Verify config has `broken_count`, `tooth_count`, `crack_count`, `wear_percentage`, `health_score`, `health_status` in telemetry_fields via `grep`
- Verify `format_telemetry` merges vision_data fields into field_mapping via code inspection

## Inputs

- `src/services/iot/thingsboard.py` — ThingsBoardFormatter with `format_telemetry(processed_data)` building field_mapping dict then filtering via telemetry_fields config
- `src/services/iot/mqtt_client.py` — MQTTService with `queue_telemetry(processed_data)` calling formatter then queueing result
- `src/services/processing/data_processor.py` — DataProcessingPipeline with `__init__(..., mqtt_service=None)` and processing loop calling `iot_service.queue_telemetry(processed_data)` at step 6
- `src/core/lifecycle.py` — `_init_data_pipeline()` creates DataProcessingPipeline; `self.camera_results_store` already an attribute (may be None)
- `config/config.yaml` — `iot.thingsboard.telemetry_fields` list controls which fields pass through to ThingsBoard

## Expected Output

- `src/services/iot/thingsboard.py` — `format_telemetry` accepts and merges `vision_data` into field_mapping
- `src/services/iot/mqtt_client.py` — `queue_telemetry` accepts and forwards `vision_data` to formatter
- `src/services/processing/data_processor.py` — pipeline holds `camera_results_store`, calls `snapshot()` per cycle, passes vision_data to queue_telemetry
- `src/core/lifecycle.py` — `_init_data_pipeline` passes `camera_results_store=self.camera_results_store`
- `config/config.yaml` — 6 camera field names added to telemetry_fields

## Observability Impact

- **New log signal:** `logger.warning("Camera snapshot failed: {e}")` in `data_processor.py` — emitted when `camera_results_store.snapshot()` raises. Grep for `"Camera snapshot failed"` to detect camera↔pipeline integration failures.
- **Inspection:** Camera fields appear in ThingsBoard telemetry `values` dict when vision_data is provided. When camera is disabled/None, values dict is unchanged — no camera keys present.
- **No new status endpoints or persisted failure state** — this is pass-through wiring; failure visibility comes from the existing MQTT stats (`errors` counter) and the warning log above.
