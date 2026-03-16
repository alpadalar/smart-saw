# S22: Lifecycle & DB Integration — UAT

**Milestone:** M001
**Written:** 2026-03-16

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: No camera hardware or AI model files available in dev. All verification is contract-level: imports, syntax, constructor signatures, SQL column alignment, shutdown ordering, and observability hooks.

## Preconditions

- Python environment with project dependencies installed (excluding cv2/torch — not needed for these checks)
- Working directory is the project root with `src/` accessible
- No running application instance required

## Smoke Test

Run `python -c "import src.services.camera; print('OK')"` — must print OK without importing cv2. This confirms the zero-import guard that underpins the entire camera module's config-driven architecture.

## Test Cases

### 1. Zero-import guard preserved

1. Run `python -c "import sys; import src.services.camera; assert 'cv2' not in sys.modules; print('PASS')"`
2. **Expected:** Prints `PASS` — cv2 is not loaded when importing the camera package

### 2. Worker imports succeed independently

1. Run `python -c "from src.services.camera.detection_worker import DetectionWorker; print('OK')"`
2. Run `python -c "from src.services.camera.ldc_worker import LDCWorker; print('OK')"`
3. **Expected:** Both print `OK` — workers are importable without camera hardware

### 3. All modified files compile

1. Run `python -m py_compile src/services/camera/__init__.py`
2. Run `python -m py_compile src/services/camera/detection_worker.py`
3. Run `python -m py_compile src/services/camera/ldc_worker.py`
4. Run `python -m py_compile src/core/lifecycle.py`
5. **Expected:** All four commands exit 0 with no output

### 4. DetectionWorker accepts db_service parameter

1. Run:
   ```python
   python -c "
   import inspect
   from src.services.camera.detection_worker import DetectionWorker
   sig = inspect.signature(DetectionWorker.__init__)
   p = sig.parameters['db_service']
   assert p.default is None, f'Expected None, got {p.default}'
   print('PASS')
   "
   ```
2. **Expected:** Prints `PASS` — db_service is an optional keyword parameter defaulting to None

### 5. LDCWorker accepts db_service parameter

1. Run:
   ```python
   python -c "
   import inspect
   from src.services.camera.ldc_worker import LDCWorker
   sig = inspect.signature(LDCWorker.__init__)
   p = sig.parameters['db_service']
   assert p.default is None, f'Expected None, got {p.default}'
   print('PASS')
   "
   ```
2. **Expected:** Prints `PASS` — db_service is an optional keyword parameter defaulting to None

### 6. Lifecycle _init_camera references all camera services

1. Run `grep -c 'CameraResultsStore\|CameraService\|DetectionWorker\|LDCWorker' src/core/lifecycle.py`
2. **Expected:** Count ≥ 8 (each class referenced at import + instantiation minimum)

### 7. Lifecycle stop order: camera before SQLite flush

1. Run:
   ```bash
   grep -n 'detection_worker.stop\|ldc_worker.stop\|camera_service.stop\|db_services.items' src/core/lifecycle.py
   ```
2. **Expected:** detection_worker.stop and ldc_worker.stop line numbers are lower than db_services.items line number. Camera threads stop before SQLite services flush.

### 8. INSERT SQL matches detection_events schema columns

1. Run `grep -A2 'INSERT INTO detection_events' src/services/camera/detection_worker.py`
2. Compare with `grep -A12 'CREATE TABLE.*detection_events' src/services/database/schemas.py`
3. **Expected:** INSERT column list is `(timestamp, event_type, confidence, count, image_path, kesim_id, makine_id, serit_id, malzeme_cinsi)` — exactly 9 non-auto columns matching schema (id is AUTOINCREMENT)

### 9. INSERT SQL matches wear_history schema columns

1. Run `grep -A2 'INSERT INTO wear_history' src/services/camera/ldc_worker.py`
2. Compare with `grep -A12 'CREATE TABLE.*wear_history' src/services/database/schemas.py`
3. **Expected:** INSERT column list is `(timestamp, wear_percentage, health_score, edge_pixel_count, image_path, kesim_id, makine_id, serit_id, malzeme_cinsi)` — exactly 9 non-auto columns matching schema

### 10. Warning logs on DB write failure

1. Run `grep 'logger.warning.*DB write failed' src/services/camera/detection_worker.py src/services/camera/ldc_worker.py`
2. **Expected:** At least 3 matches: broken_tooth drop, crack drop (in detection_worker), wear_history drop (in ldc_worker)

### 11. No module-level camera imports in lifecycle

1. Run `head -50 src/core/lifecycle.py | grep 'from src.services.camera'`
2. **Expected:** No output — all camera imports are inside _init_camera(), not at module level

## Edge Cases

### Camera disabled in config

1. With `camera.enabled=false` in config, `import src.services.camera` must not trigger cv2
2. Lifecycle's `_init_camera()` should not execute camera service creation when config flag is false
3. **Expected:** Application starts normally without camera, no cv2/torch loaded

### db_service is None (backward compatibility)

1. Instantiate DetectionWorker or LDCWorker without db_service parameter
2. **Expected:** Workers function without DB writes — no AttributeError, no NoneType.write_async calls

### _init_camera failure

1. If any camera import or instantiation fails inside _init_camera
2. **Expected:** Exception caught, `logger.warning("Camera initialization failed: ...")` emitted, lifecycle continues without camera services

## Failure Signals

- `ModuleNotFoundError: No module named 'cv2'` on `import src.services.camera` — zero-import guard broken
- `TypeError: __init__() got an unexpected keyword argument 'db_service'` — worker constructor not updated
- Camera stop lines appear after SQLite flush lines in lifecycle.py — shutdown order wrong
- INSERT column count mismatch (not 9) — SQL will fail at runtime with column count error
- No `logger.warning` grep hits — write failure not observable

## Requirements Proved By This UAT

- CAM-02 — zero-import guard verified (test case 1)
- DATA-01 — INSERT SQL for detection_events and wear_history verified against schema (test cases 8, 9)
- DATA-03 — lifecycle _init_camera creates camera db and wires services (test case 6)

## Not Proven By This UAT

- Actual frame capture and detection (requires camera hardware + model files)
- Actual DB writes landing in camera.db (requires running application with camera.enabled=true)
- IoT telemetry integration (S23)
- GUI display of detection/wear results (S24)
- Traceability column population (deferred — currently NULL)

## Notes for Tester

- All test cases are runnable without camera hardware or AI model files
- The verification is contract-level: correct imports, correct SQL, correct shutdown order
- Runtime validation requires camera.enabled=true with actual hardware — that's beyond this slice's scope
- If cv2 or torch are installed in the test environment, test case 1 won't fail even if the guard is broken — run in a clean environment without cv2 to truly validate
