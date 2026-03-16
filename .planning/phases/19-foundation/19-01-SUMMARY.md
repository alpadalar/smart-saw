---
phase: 19-foundation
plan: 01
subsystem: database
tags: [numpy, camera, sqlite, schema, lifecycle]

# Dependency graph
requires: []
provides:
  - numpy>=1.24.0 without upper bound (numpy 2.x compatible)
  - np.ptp() replaced with np.max()-np.min() in anomaly/base.py
  - camera: config section in config.yaml with enabled: false default
  - SCHEMA_CAMERA_DB with detection_events and wear_history tables in schemas.py
  - _init_camera() method in lifecycle.py with config guard
  - src/services/camera/__init__.py module scaffold
affects: [S20, S21, S22, S23, S24]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "config-guard pattern: camera.enabled=false causes early return with zero behavioral change"
    - "optional DB pattern: camera.db only created when feature enabled (same as MQTT pattern)"

key-files:
  created:
    - src/services/camera/__init__.py
  modified:
    - requirements.txt
    - src/anomaly/base.py
    - config/config.yaml
    - src/services/database/schemas.py
    - src/core/lifecycle.py

key-decisions:
  - "numpy upper bound removed (>=1.24.0 only) — downstream camera slices need numpy 2.x for ultralytics/torch"
  - "camera.enabled defaults to false — zero behavioral change in production until camera hardware connected"
  - "camera.db created by _init_camera() not _init_databases() — keeps camera lifecycle isolated, no config.yaml database.sqlite.databases entry"
  - "No camera module imports in lifecycle.py — lazy import pattern deferred to S22 to avoid import errors when opencv not installed"

patterns-established:
  - "Optional feature pattern: config guard + early return + warning log on failure (established by _init_mqtt, replicated for _init_camera)"
  - "Camera DB shutdown: existing db_services loop automatically handles camera.db — no explicit shutdown code needed"

requirements-completed: [CAM-01, CAM-02, DATA-03]

# Metrics
duration: 2min
completed: 2026-03-16
---

# Phase 19 Plan 01: Foundation Summary

**numpy 2.x unblocked and camera foundation scaffolded: config schema, SCHEMA_CAMERA_DB (detection_events + wear_history), config-guarded _init_camera() in lifecycle, and empty camera module directory**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-15T23:59:29Z
- **Completed:** 2026-03-16T00:01:32Z
- **Tasks:** 2
- **Files modified:** 5 modified + 1 created

## Accomplishments

- Removed numpy<2.0 upper bound and replaced np.ptp() call — ML code now compatible with both numpy 1.x and 2.x
- Added camera: config section to config.yaml (enabled: false default) with all sub-keys matching research-recommended values (device_id, resolution, fps, jpeg_quality, recordings_path, detection, wear, health)
- Added SCHEMA_CAMERA_DB to schemas.py with detection_events and wear_history tables, registered as 'camera' in SCHEMAS dict (6 entries total)
- Added _init_camera() to lifecycle.py: config-guarded, creates camera.db only when camera.enabled=true, uses existing db_services shutdown loop
- Created src/services/camera/__init__.py as empty module scaffold (unblocks S20-S24 imports)

## Task Commits

Each task was committed atomically:

1. **Task 1: numpy uncap + np.ptp fix + camera config schema** - `8dfbdb0` (feat)
2. **Task 2: Camera DB schema + lifecycle _init_camera() + camera module scaffold** - `2131ac2` (feat)

## Files Created/Modified

- `requirements.txt` - Removed numpy<2.0 upper bound, now numpy>=1.24.0
- `src/anomaly/base.py` - Replaced np.ptp(values) with np.max(values)-np.min(values) at line 254
- `config/config.yaml` - Appended camera: section with enabled: false and all sub-keys
- `src/services/database/schemas.py` - Added SCHEMA_CAMERA_DB constant and 'camera' key in SCHEMAS dict
- `src/core/lifecycle.py` - Added _init_camera() method and call in startup sequence
- `src/services/camera/__init__.py` - New empty module scaffold with docstring listing future components

## Decisions Made

- numpy upper bound removed (>=1.24.0 only) because downstream camera slices (S20+) need ultralytics/torch which require numpy 2.x
- camera.enabled defaults to false so there is zero behavioral change in existing production deployment
- camera.db is created by _init_camera() not _init_databases() to keep camera lifecycle isolated; no entry added to database.sqlite.databases in config.yaml
- No camera module imports in lifecycle.py — lazy import pattern deferred to S22 to avoid ImportError when opencv-python-headless is not installed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all files edited cleanly with exact patterns specified in plan.

## User Setup Required

None - no external service configuration required. Camera feature is off by default (camera.enabled: false).

## Next Phase Readiness

- S20 (CameraService frame capture) can now proceed: camera/ module directory exists, config schema defined, SCHEMA_CAMERA_DB ready
- S21-S24 (detection workers, LDC wear, VisionService, GUI) unblocked by camera scaffold
- numpy 2.x compatibility established — ultralytics/torch can be added to requirements.txt in S20

---
*Phase: 19-foundation*
*Completed: 2026-03-16*

## Self-Check: PASSED

All 6 files verified on disk. Both task commits (8dfbdb0, 2131ac2) confirmed in git log.
