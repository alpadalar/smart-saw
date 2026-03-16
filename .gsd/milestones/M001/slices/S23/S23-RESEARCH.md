# S23: IoT Integration — Research

**Date:** 2026-03-16

## Summary

Straightforward wiring. Camera telemetry fields need to flow from `CameraResultsStore.snapshot()` into the existing ThingsBoard telemetry payload. The data pipeline currently calls `self.iot_service.queue_telemetry(processed_data)` — this needs to also carry camera vision data when the store is available. Three files need surgical changes, one needs a config addition. No new architecture, no new dependencies, no unfamiliar APIs.

## Recommendation

Thread the `camera_results_store` through the existing pipeline → formatter → IoT chain as an optional parameter at each level. All camera fields are added to the same telemetry dict alongside sensor fields — no separate MQTT topic, no separate send cycle. When `camera_results_store is None`, behavior is identical to today.

## Implementation Landscape

### Key Files

- `src/services/processing/data_processor.py` — The 10 Hz loop. Step 6 calls `self.iot_service.queue_telemetry(processed_data)`. Needs: (1) accept `camera_results_store` in constructor, (2) pass `camera_results_store.snapshot()` to `queue_telemetry()` when available.

- `src/services/iot/mqtt_client.py` — `MQTTService.queue_telemetry(processed_data)` calls `self.formatter.format_telemetry(processed_data)`. Needs: (1) accept optional `vision_data` dict parameter, (2) forward it to formatter.

- `src/services/iot/thingsboard.py` — `ThingsBoardFormatter.format_telemetry(processed_data)` builds a `field_mapping` dict and filters by `telemetry_fields` config. Needs: (1) accept optional `vision_data` dict parameter, (2) merge camera fields into `field_mapping` before the filter step.

- `src/core/lifecycle.py` — `_init_data_pipeline()` creates `DataProcessingPipeline`. Needs: pass `self.camera_results_store` (already an attribute, may be None) to pipeline constructor.

- `config/config.yaml` — `iot.thingsboard.telemetry_fields` list controls which fields are included. Needs: add camera vision field names so they pass the filter.

### CameraResultsStore Snapshot Fields (produced by S20–S22)

From detection_worker:
- `broken_count` (int), `broken_confidence` (float), `tooth_count` (int)
- `crack_count` (int), `crack_confidence` (float)
- `last_detection_ts` (str)

From ldc_worker:
- `wear_percentage` (float), `last_wear_ts` (str)
- `health_score` (float), `health_status` (str), `health_color` (str)

From camera_service:
- `latest_frame` (bytes — JPEG), `frame_count` (int), `is_recording` (bool)
- `recording_path` (str|None), `fps_actual` (float)

For IoT telemetry, include: `broken_count`, `tooth_count`, `crack_count`, `wear_percentage`, `health_score`, `health_status`. Skip `latest_frame` (binary), `*_confidence` (internal), `*_ts` (redundant with telemetry timestamp), `health_color` (GUI-only), frame metadata.

### Build Order

1. **ThingsBoardFormatter** — add `vision_data` parameter to `format_telemetry()`. Merge 6 camera fields into `field_mapping`. No upstream dependency.
2. **MQTTService** — update `queue_telemetry()` to accept and forward `vision_data`. Depends on step 1.
3. **DataProcessingPipeline** — add `camera_results_store` constructor param, call `snapshot()` per cycle, pass to `queue_telemetry()`. Depends on step 2.
4. **Lifecycle** — pass `self.camera_results_store` to pipeline constructor. One line change.
5. **Config** — add camera field names to `telemetry_fields` list.

Steps 1–3 can be a single task (they form a tight chain). Step 4 and 5 are trivially small and can be included in the same task or a second small task.

### Verification Approach

- `py_compile` all modified files — confirms no syntax errors
- `python -c "from src.services.iot.thingsboard import ThingsBoardFormatter"` — import OK
- `python -c "from src.services.iot.mqtt_client import MQTTService"` — import OK
- `python -c "from src.services.processing.data_processor import DataProcessingPipeline"` — import OK
- Verify `format_telemetry` signature accepts `vision_data=None` (backward compatible)
- Verify `queue_telemetry` signature accepts `vision_data=None` (backward compatible)
- Verify `DataProcessingPipeline.__init__` accepts `camera_results_store=None` (backward compatible)
- Verify lifecycle passes `self.camera_results_store` to pipeline
- Verify config has camera field names in `telemetry_fields`
- Verify `format_telemetry` with `vision_data={'broken_count': 3, ...}` includes those fields in output values dict
- Verify `format_telemetry` with `vision_data=None` produces identical output to current behavior

### Important Patterns

- **Backward compatibility:** Every new parameter defaults to `None`. Existing call sites that don't pass camera data continue working unchanged.
- **Filter integration:** `ThingsBoardFormatter` uses a `telemetry_fields` config list to whitelist fields. Camera fields must be added to this list in `config.yaml` — otherwise they'll be silently dropped (unless the list is empty, in which case all non-None values are included).
- **No hot-path cost:** `snapshot()` is a single lock acquisition + dict copy — microsecond-range. Called once per 10 Hz cycle.
- **Exclude binary data:** `latest_frame` (JPEG bytes) must NOT be sent to ThingsBoard. Only scalar/string values.

## Constraints

- `queue_telemetry()` is called from asyncio context — `snapshot()` acquires a threading.Lock briefly, which is acceptable (microsecond hold time, same pattern as AnomalyManager).
- Camera fields must not duplicate existing field names in `field_mapping` — all 6 proposed names (`broken_count`, `tooth_count`, `crack_count`, `wear_percentage`, `health_score`, `health_status`) are unique.
