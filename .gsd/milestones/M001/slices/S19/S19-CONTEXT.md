---
id: S19
milestone: M001
status: ready
---

# S19: Foundation — Context

## Goal

Remove the numpy<2.0 version cap, define the camera config schema in `config.yaml`, add `SCHEMA_CAMERA_DB` to `schemas.py` with two tables, establish the zero-import guard pattern with static verification, and scaffold the empty `src/services/camera/` module directory.

## Why this Slice

Every downstream camera slice (S20–S24) depends on numpy 2.x compatibility (OpenCV/ultralytics/torch won't install without it), the `camera:` config section (all services read from it), and the camera.db schema (detection and wear results need a target table). The import guard pattern must be established here — before any camera Python code exists — so that every subsequent slice inherits the "camera.enabled=false means zero camera imports" contract from day one. Doing this first is zero-risk (additive config/schema changes, one line in requirements.txt) and unblocks everything else.

## Scope

### In Scope

- Remove `numpy<2.0` upper bound from `requirements.txt` (change to `numpy>=1.24.0`)
- Verify ML model prediction parity after numpy upgrade (load existing `.pkl` model, run a test prediction, confirm output matches pre-upgrade values)
- Add `camera:` section to `config/config.yaml` with `enabled: false` default and all sub-keys (device_id, fps, resolution, jpeg_quality, recordings_path, detection, wear, health)
- Add `SCHEMA_CAMERA_DB` to `src/services/database/schemas.py` with two tables: `detection_events` and `wear_history`
- Add `'camera'` key to the `SCHEMAS` dict in `schemas.py`
- Establish the zero-import guard pattern: camera.db is only created when `camera.enabled=true` (inside `_init_camera()`, not in the existing `_init_databases()`)
- Static verification that no camera module is imported at startup when `camera.enabled=false`
- Scaffold `src/services/camera/` directory with `__init__.py` (empty or minimal)

### Out of Scope

- Any camera Python implementation code (CameraService, VisionService, DetectionWorker, etc.) — that's S20+
- Adding new pip dependencies beyond the numpy uncap (opencv-python-headless, ultralytics, torch, kornia are added when S20 needs them)
- Modifying `lifecycle.py` beyond the minimum needed for the import guard pattern (the full `_init_camera()` method comes in S22)
- Creating the `data/recordings/` directory structure — that's S20
- GUI changes — that's S24

## Constraints

- `camera.enabled` must default to `false` in config.yaml — machines without camera hardware must not be affected
- The numpy upgrade must not break existing ML model predictions — verify parity before proceeding
- `SCHEMA_CAMERA_DB` must follow the existing schema pattern in `schemas.py` (string constant with CREATE TABLE + CREATE INDEX)
- Camera.db must NOT be created in `_init_databases()` — it is only created conditionally when camera is enabled (anti-pattern 5 from pitfalls research)
- Config defaults use research-recommended values: 1280×720, 30fps, JPEG quality 85, confidence threshold 0.5, detection interval 2s, wear interval 5s, health weights 70% broken / 30% wear

## Integration Points

### Consumes

- `requirements.txt` — current numpy pin (`numpy<2.0,>=1.24.0`) to be relaxed
- `config/config.yaml` — existing config structure to append `camera:` section
- `src/services/database/schemas.py` — existing `SCHEMAS` dict and schema pattern
- `data/models/Bagging_dataset_v17_20250509.pkl` — existing ML model for parity verification

### Produces

- `requirements.txt` — updated with `numpy>=1.24.0` (no upper bound)
- `config/config.yaml` — `camera:` section with `enabled: false` and all sub-keys
- `src/services/database/schemas.py` — `SCHEMA_CAMERA_DB` constant (detection_events + wear_history tables) and `'camera'` key in `SCHEMAS` dict
- `src/services/camera/__init__.py` — empty module scaffold for downstream slices
- ML parity verification evidence — confirmation that existing model produces identical outputs after numpy upgrade

## Open Questions

- **Exact detection_events columns** — The research proposes `id, timestamp, event_type, confidence, wear_percentage, health_score, kesim_id, image_path` plus traceability columns (makine_id, serit_id, malzeme_cinsi). Finalize during planning based on what DetectionWorker and LDCWorker will actually write.
- **wear_history granularity** — Whether wear_history stores per-frame entries or aggregated per-session entries. Current thinking: per-frame (matches wear.csv pattern from old project), but may be adjusted during S21 planning if disk usage is a concern.
