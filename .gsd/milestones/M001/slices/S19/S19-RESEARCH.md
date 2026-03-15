# S19: Foundation — Research

**Date:** 2026-03-16
**Slice scope:** numpy cap removed, camera config schema defined, camera.db schema in schemas.py, zero-import guard active.

## Summary

S19 is a pure infrastructure slice with zero behavioral risk to the running system. It has four deliverables: (1) remove the `numpy<2.0` cap from `requirements.txt`, (2) add a `camera:` config section to `config.yaml`, (3) add `SCHEMA_CAMERA_DB` to `schemas.py` with its `'camera'` key in `SCHEMAS`, and (4) ensure the camera module directory exists with a zero-import guard pattern ready for downstream slices. None of these changes touch runtime code paths — they are additive schema/config changes that prepare the ground for S20–S24.

The system currently runs Python 3.13, numpy 1.26.4, and already has `opencv-python-headless` 4.11.0, `ultralytics` 8.3.199, and `torch` 2.8.0 installed system-wide. The `numpy<2.0` cap in `requirements.txt` is a documentation constraint — it does not block the current environment, but it is misleading and would block future dependency upgrades (e.g., opencv-python-headless 4.13+ requires numpy>=2 on Python 3.12+). Removing it is low-risk and forward-looking.

A notable environment concern: **both `opencv-python` (4.8.1.78) and `opencv-python-headless` (4.11.0.86) are installed**. The loaded `cv2` resolves to 4.11.0 with GUI backend available (`cv2.namedWindow` exists). This dual installation creates a latent Qt5/Qt6 symbol conflict risk on Linux. S19 should document this in requirements.txt but not attempt to uninstall packages — that is an environment concern for deployment, not a code change.

## Requirements Addressed

| Requirement | How S19 Supports |
|------------|-----------------|
| **CAM-01** — camera.enabled flag | Config schema defines `camera.enabled: false` default |
| **CAM-02** — zero import when disabled | Module directory with `__init__.py` establishes the lazy-import guard pattern; no camera imports added to lifecycle yet (that's S22) |
| **DATA-03** — camera DB schema lifecycle | `SCHEMA_CAMERA_DB` added to schemas.py; `'camera'` key added to `SCHEMAS` dict — lifecycle can reference it in S22 |

## Recommendation

Execute all four changes in sequence as independent commits. Each is pure addition with no existing code modification risk:

1. **requirements.txt** — Change `numpy<2.0,>=1.24.0` to `numpy>=1.24.0`. Add `opencv-python-headless>=4.11.0`, `ultralytics>=8.3.70`, `torch>=2.6.0`, `torchvision>=0.21.0`, `kornia>=0.7.0` in a clearly marked camera section with comments.

2. **config.yaml** — Add `camera:` section at the end of the file with `enabled: false` as the top-level guard. Include all sub-keys needed by S20–S24 (device_id, resolution, fps, jpeg_quality, recordings_path, detection model paths, wear config, health weights).

3. **schemas.py** — Add `SCHEMA_CAMERA_DB` constant with `detection_events` and `wear_history` tables. Add `'camera': SCHEMA_CAMERA_DB` to the `SCHEMAS` dict. The camera.db will NOT be created in `_init_databases()` — it will be conditionally created in `_init_camera()` (S22).

4. **src/services/camera/__init__.py** — Create the module directory with an empty `__init__.py`. This establishes the namespace for S20+ without importing anything.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| DB schema definition | `SCHEMA_*_DB` constants in `schemas.py` | All 5 existing schemas follow identical pattern — multi-line SQL string with CREATE TABLE + CREATE INDEX |
| Schema mapping | `SCHEMAS` dict in `schemas.py` | lifecycle.py iterates this dict in `_init_databases()`; camera entry must exist here but camera.db must NOT be created there (config-gated in S22) |
| Config structure | `config.yaml` YAML sections | All existing services (modbus, ml, iot, anomaly_detection) follow same pattern: top-level key with `enabled` flag |

## Existing Code and Patterns

- `src/services/database/schemas.py` — Contains 5 schema constants (`SCHEMA_RAW_DB`, `SCHEMA_TOTAL_DB`, `SCHEMA_LOG_DB`, `SCHEMA_ML_DB`, `SCHEMA_ANOMALY_DB`) and a `SCHEMAS` dict mapping names to SQL. New `SCHEMA_CAMERA_DB` follows identical pattern. **Critical:** Adding `'camera'` to `SCHEMAS` dict means `_init_databases()` would try to create it — but camera.db must only be created when `camera.enabled=true`. This means either: (a) don't add to `SCHEMAS` dict, add in `_init_camera()` directly, or (b) add to `SCHEMAS` but skip in `_init_databases()`. Approach (a) is cleaner and matches the architecture doc's anti-pattern #5 guidance.

- `src/core/lifecycle.py` — `_init_databases()` iterates `db_config['databases']` from config.yaml, not the `SCHEMAS` dict. The `SCHEMAS` dict is used only for schema lookup via `SCHEMAS.get(db_name, '')`. So adding `'camera'` to `SCHEMAS` is safe as long as `config.yaml` `database.sqlite.databases` does NOT include `camera`. The camera.db creation will be handled in `_init_camera()` (S22) using direct `SQLiteService(path, SCHEMA_CAMERA_DB)`.

- `config/config.yaml` — `database.sqlite.databases` dict maps names to filenames. Camera should NOT be added here. This dict controls unconditional DB creation. Camera DB is conditional.

- `src/services/iot/mqtt_client.py` — Example of config-gated optional service with `enabled` flag pattern. Camera follows the same pattern.

## Constraints

- **`SCHEMAS` dict vs `_init_databases()` loop:** `_init_databases()` iterates `config['database']['sqlite']['databases']` — NOT the `SCHEMAS` dict. It uses `SCHEMAS.get(db_name, '')` for schema lookup. Adding `'camera'` to `SCHEMAS` is safe because it won't be iterated unless `camera` appears in the config databases dict. However, NOT adding `camera` to the config databases dict is the correct pattern — camera.db creation is gated in `_init_camera()`.

- **Dual OpenCV installation:** Both `opencv-python` (4.8.1.78) and `opencv-python-headless` (4.11.0.86) are installed. This is a known conflict scenario — the `cv2` namespace is shared and load order is unpredictable. Currently cv2 resolves to 4.11.0 with GUI backend. `requirements.txt` should specify `opencv-python-headless` and note that `opencv-python` should be uninstalled, but the actual uninstall is an environment task.

- **No `from __future__ import annotations` or `TYPE_CHECKING` patterns exist yet:** Zero usage across the entire codebase. S19 should not introduce them in existing files — only in new `src/services/camera/` files. This pattern will be used in S20+ camera modules to prevent import-time evaluation of cv2/torch type annotations.

- **numpy 1.26.4 works with all current deps:** opencv-python-headless 4.11.0 requires `numpy>=1.26.0` on Python 3.12+. ultralytics 8.3.199 requires `numpy>=1.23.0`. scikit-learn 1.8.0 requires `numpy>=1.24.1`. pandas 2.3.2 requires `numpy>=1.26.0` on Python 3.12+. Removing the `<2.0` cap does not force an upgrade — pip will keep 1.26.4 since all constraints are satisfied.

## Common Pitfalls

- **Adding `camera` to `database.sqlite.databases` in config.yaml** — This would cause `_init_databases()` to unconditionally create camera.db on every startup, violating the `camera.enabled=false` → zero camera artifact guarantee. Camera DB creation must be conditional, handled in `_init_camera()` (S22). Only add `SCHEMA_CAMERA_DB` to `schemas.py` `SCHEMAS` dict for lookup.

- **Importing camera modules at the top of existing files** — S19 creates `src/services/camera/__init__.py` but must NOT add any `import` statement for it in lifecycle.py, main_controller.py, or any other existing file. The zero-import guard means camera module is invisible until S22 adds lazy imports inside config guards.

- **Over-specifying config defaults** — The `camera:` config section should have sensible defaults but not include values that only make sense with camera hardware present (e.g., don't set `recordings_path` to an absolute path that requires specific disk layout). Use relative paths like `data/recordings`.

## Open Risks

- **opencv-python vs opencv-python-headless conflict on deployment target** — The industrial panel PC environment may have different package state. The requirements.txt change documents intent, but deployment scripts must ensure only headless is installed. Risk level: LOW (deployment concern, not code concern).

- **Future numpy 2.x upgrade** — Removing the cap does not force an upgrade now, but a future `pip install --upgrade numpy` could pull 2.x, which may surface C-extension ABI issues with older compiled packages. Risk level: LOW (numpy 2.x has been stable since mid-2024; sklearn 1.8, pandas 2.3, ultralytics 8.3+ all support it).

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| OpenCV | `mindrally/skills@computer-vision-opencv` | available (587 installs) — potentially useful for S20 camera capture, not needed for S19 |
| PyTorch | `mindrally/skills@deep-learning-pytorch` | available (265 installs) — potentially useful for S21 detection pipeline, not needed for S19 |
| PySide6 | `ds-codi/project-memory-mcp@pyside6-mvc` | available (44 installs) — potentially useful for S24 camera GUI, not needed for S19 |

None of these skills are needed for S19 (pure config/schema/requirements changes). They may be useful for S20–S24.

## Implementation Details

### 1. requirements.txt changes

```diff
- numpy<2.0,>=1.24.0
+ numpy>=1.24.0

+ # === Camera Vision & AI Detection (v2.0) ===
+ # Camera capture (headless — avoids Qt5/Qt6 conflict with PySide6)
+ opencv-python-headless>=4.11.0
+ # RT-DETR object detection
+ ultralytics>=8.3.70
+ # PyTorch runtime (for ultralytics + LDC)
+ # For CPU-only: pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
+ torch>=2.6.0
+ torchvision>=0.21.0
+ # LDC edge detection preprocessing
+ kornia>=0.7.0
```

### 2. config.yaml camera section

```yaml
# Camera Vision & AI Detection (v2.0)
camera:
  enabled: false          # Set true to enable camera module
  device_id: 0            # OpenCV VideoCapture device index
  fps: 30
  resolution:
    width: 1920
    height: 1200
  jpeg_quality: 85
  recordings_path: "data/recordings"

  detection:
    enabled: true
    broken_model_path: "data/models/best.pt"
    crack_model_path: "data/models/catlak-best.pt"
    interval_seconds: 2.0
    confidence_threshold: 0.5

  wear:
    enabled: true
    ldc_weights_path: "data/models/ldc_weights.pth"
    interval_seconds: 5.0
    baseline_edge_count: null   # Calibrated per blade

  health:
    broken_weight: 0.70
    wear_weight: 0.30
```

### 3. schemas.py addition

Add `SCHEMA_CAMERA_DB` constant and `'camera'` entry in `SCHEMAS` dict. Two tables: `detection_events` (kirik/catlak/asinma events with traceability) and `wear_history` (wear % time series).

### 4. Module directory

Create `src/services/camera/__init__.py` with docstring only — no imports. This prevents Python from complaining about missing package when S20+ adds submodules.

## Sources

- Direct inspection: `src/services/database/schemas.py` — 5 existing schema patterns
- Direct inspection: `src/core/lifecycle.py` — `_init_databases()` iteration pattern, startup sequence
- Direct inspection: `config/config.yaml` — existing service config patterns (modbus, ml, iot, anomaly_detection)
- Direct inspection: `requirements.txt` — current numpy cap and dependency list
- Runtime verification: `pip list` output, `pip show` metadata — actual installed versions and numpy requirements
- Architecture research: `.gsd/milestones/M001/M001-RESEARCH.md` — ARCHITECTURE.md anti-pattern #5

---
*Research completed: 2026-03-16*
*Ready for planning: yes*
