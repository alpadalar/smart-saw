# S19 ("Foundation") — Research

**Date:** 2026-03-16

## Summary

S19 is the foundation slice that unblocks all camera work (S20–S24). It touches 4 existing files — `requirements.txt`, `config/config.yaml`, `src/services/database/schemas.py`, `src/core/lifecycle.py` — with zero new modules. The scope is: (1) remove the numpy `<2.0` cap that blocks opencv/torch/ultralytics installation, (2) add the `camera:` config section to `config.yaml` with `enabled: false` default, (3) define `SCHEMA_CAMERA_DB` in `schemas.py` and register it in the `SCHEMAS` dict, (4) add an `_init_camera()` stub in `lifecycle.py` with a lazy-import guard that creates camera.db only when `camera.enabled=true`.

There is one confirmed breakage risk: **`np.ptp()` in `src/anomaly/base.py:254`** is removed in numpy 2.0 and must be replaced with `np.max() - np.min()` before or alongside the numpy cap removal. All other numpy usage in the codebase (`np.mean`, `np.std`, `np.percentile`, `np.array`) is safe across numpy 1.x/2.x. The ML pickle model was trained with scikit-learn 1.4.2 and already loads with a warning on 1.8.0 — this is a pre-existing issue unrelated to numpy 2.x.

## Recommendation

Implement S19 as 4 surgical edits to existing files plus one defensive fix in `anomaly/base.py`:

1. **`requirements.txt`** — Change `numpy<2.0,>=1.24.0` to `numpy>=1.24.0` (remove upper bound only).
2. **`src/anomaly/base.py`** — Replace `np.ptp(values)` with `np.max(values) - np.min(values)` at line 254. This is the only numpy 2.0-incompatible call in the codebase.
3. **`config/config.yaml`** — Append the `camera:` section at EOF with `enabled: false` default and all sub-keys (device_id, resolution, fps, model paths, detection/wear intervals, health weights).
4. **`src/services/database/schemas.py`** — Add `SCHEMA_CAMERA_DB` constant with `detection_events` and `wear_history` tables, then add `'camera': SCHEMA_CAMERA_DB` to the `SCHEMAS` dict.
5. **`src/core/lifecycle.py`** — Add `_init_camera()` method between `_init_mqtt()` (line 118) and `_init_data_pipeline()` (line 121). The method checks `camera.enabled`, returns early if false, otherwise creates `camera.db` via `SQLiteService` and registers it in `self.db_services['camera']`. **No camera module imports** — those are deferred to S20+. Also add camera DB stop to the shutdown sequence.

This approach is zero-risk for the existing system: `camera.enabled: false` is the default, `np.ptp` replacement is semantically identical, and the numpy cap removal only lifts an upper bound (pip is free to keep installing 1.26.x).

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| SQLite DB creation with schema | `SQLiteService(db_file, schema_sql)` | Existing pattern in `_init_databases()` — handles WAL mode, connection pooling, write queue |
| Config section access | `self.config.get('camera', {}).get('enabled', False)` | Same nested-dict pattern used by `_init_mqtt()` for IoT config |
| Schema registration | `SCHEMAS` dict in `schemas.py` | All DB schemas register here; `_init_databases()` iterates this dict |

## Existing Code and Patterns

- `src/core/lifecycle.py:_init_mqtt()` (line 320) — The template for `_init_camera()`: check config flag, early return if disabled, lazy-import service, catch errors and continue. Camera follows the same pattern but simpler (no import needed in S19, just DB creation).
- `src/core/lifecycle.py:_init_databases()` (line 228) — Creates SQLite services by iterating `db_config['databases']`. Camera DB is NOT added here (would create it unconditionally). Instead, `_init_camera()` creates it conditionally — matches anti-pattern 5 from ARCHITECTURE.md.
- `src/services/database/schemas.py:SCHEMAS` dict (bottom of file) — Maps db names to schema SQL. `'camera'` key must be added here so it's available for `_init_camera()` to reference.
- `src/core/lifecycle.py` startup sequence: `_init_databases` → `_init_modbus` → `_init_control_manager` → `_init_mqtt` → **`_init_camera` (NEW)** → `_init_data_pipeline` → `_init_gui`. Camera goes after MQTT and before data pipeline so `camera_results_store` (added in S22) is available for pipeline injection.
- `src/core/lifecycle.py` shutdown sequence: GUI thread join → data pipeline stop → IoT stop → Modbus disconnect → PostgreSQL disconnect → SQLite flush. Camera stop goes before data pipeline stop (added in S22).

## Constraints

- **numpy `<2.0` cap is a hard blocker** — `opencv-python-headless >=4.11.0` requires numpy >=2.0 on Python 3.9+. The cap must be removed in S19 before any S20+ dependency can be installed.
- **`np.ptp()` removed in numpy 2.0** — Used once at `src/anomaly/base.py:254`. Must be replaced before or alongside numpy upgrade. Replacement: `np.max(values) - np.min(values)` (semantically identical — ptp = peak-to-peak = max - min).
- **`camera.enabled: false` must be the default** — Machines without camera hardware must start without errors. The `_init_camera()` stub must early-return when disabled.
- **No camera module imports in S19** — `src/services/camera/` directory doesn't exist yet (created in S20). The lifecycle `_init_camera()` only does DB creation, not service imports.
- **Camera DB must be created inside `_init_camera()`, not in `_init_databases()`** — Anti-pattern 5 from ARCHITECTURE.md: don't create camera.db when camera is disabled.
- **`SCHEMA_CAMERA_DB` must still be in `schemas.py`** — The schema constant is registered in `SCHEMAS` dict but only used when `_init_camera()` creates the DB conditionally.
- **Startup sequence ordering** — `_init_camera()` must go between `_init_mqtt()` and `_init_data_pipeline()`. This ensures camera services (in S22) exist before the data pipeline, which will optionally reference `CameraResultsStore`.
- **ML pickle model trained with scikit-learn 1.4.2** — Loads with `InconsistentVersionWarning` on current sklearn 1.8.0. This is a pre-existing issue, not caused by S19 changes. The model loads and works correctly.

## Common Pitfalls

- **Adding `'camera'` to `db_config['databases']` in config.yaml** — This would cause `_init_databases()` to create camera.db unconditionally. Instead, camera DB creation belongs in `_init_camera()` only. The `databases:` key under `database.sqlite` must NOT include camera.
- **Importing camera modules in lifecycle.py at module level** — Even adding a `from ..services.camera import ...` at the top of the file would fail until S20 creates the module. S19 `_init_camera()` has no imports — it only creates a DB service.
- **Forgetting to add camera DB to shutdown sequence** — If `_init_camera()` adds `self.db_services['camera']`, the existing shutdown loop already iterates `self.db_services.items()` and stops each one. No explicit shutdown change needed for the DB — it's automatic.
- **Placing `_init_camera()` call after `_init_data_pipeline()`** — Would break S22 integration where the pipeline needs `camera_results_store`. Must go before pipeline init.

## Open Risks

- **numpy 2.x upgrade may surface deprecation warnings in existing code** — `np.mean`, `np.std`, `np.percentile`, `np.array` are all safe, but numpy 2.0 tightens type promotion rules. Low risk given the simple numeric operations used.
- **ML pickle model with numpy 2.x** — The `BaggingRegressor` trained with sklearn 1.4.2 / numpy <2.0 may serialize numpy dtypes internally. scikit-learn 1.8.0 handles the transition transparently via `__reduce__` compatibility, but this should be verified by loading the model after the numpy upgrade and running a test prediction.
- **`np.ptp` replacement may be missed in future code** — Other developers might use `np.ptp` in new code. Consider adding a linter rule or comment.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| numpy | N/A — standard library upgrade, no skill needed | N/A |
| SQLite schema | Existing `SQLiteService` pattern | Already in codebase |
| YAML config | Existing `ConfigManager` pattern | Already in codebase |

No external skills are needed for S19. The work is entirely within existing codebase patterns (config addition, schema addition, lifecycle method addition).

## Sources

- `requirements.txt` — Current numpy pin: `numpy<2.0,>=1.24.0`; installed: 1.26.4
- `src/anomaly/base.py:254` — `np.ptp(values)` confirmed as only numpy 2.0-incompatible usage
- `src/core/lifecycle.py` — Startup sequence: lines 109–124; shutdown: lines 150–185
- `src/services/database/schemas.py` — SCHEMAS dict at bottom; 5 existing entries (raw, total, log, ml, anomaly)
- `src/services/processing/data_processor.py:19` — `DataProcessingPipeline.__init__` signature: `(config, modbus_reader, modbus_writer, control_manager, db_services, mqtt_service=None)`
- numpy 2.0 migration guide — `np.ptp` removed; `np.float_`, `np.int_` etc. removed but not used in this codebase
- ML model: `data/models/Bagging_dataset_v17_20250509.pkl` — BaggingRegressor trained with sklearn 1.4.2, loads successfully with 1.8.0 + InconsistentVersionWarning

## Requirements Owned by S19

| Requirement | How S19 Delivers |
|-------------|-----------------|
| **CAM-01** (camera.enabled config flag) | Defines `camera:` section in `config.yaml` with `enabled: false` default |
| **CAM-02** (zero import when disabled) | Establishes zero-import guard pattern in `_init_camera()` — early return when disabled |
| **DATA-03** (camera DB schema lifecycle-driven) | Adds `SCHEMA_CAMERA_DB` to `schemas.py` and conditional creation in `_init_camera()` |

## Files to Change

| File | Change | Risk |
|------|--------|------|
| `requirements.txt` | Remove `<2.0` from numpy pin | LOW — only lifts upper bound |
| `src/anomaly/base.py` | Replace `np.ptp(values)` with `np.max(values) - np.min(values)` | LOW — semantically identical |
| `config/config.yaml` | Append `camera:` section at EOF | ZERO — additive only |
| `src/services/database/schemas.py` | Add `SCHEMA_CAMERA_DB` constant + `'camera'` entry in `SCHEMAS` | ZERO — additive only |
| `src/core/lifecycle.py` | Add `_init_camera()` method + call between mqtt and pipeline init | LOW — early-returns when disabled |
