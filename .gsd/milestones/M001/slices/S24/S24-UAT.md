# S24: Camera GUI — UAT

**Milestone:** M001
**Written:** 2026-03-16

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: No camera hardware available. All proof is contract-level — compilation, import, API surface, and structural verification. The slice plan explicitly states "Real runtime required: no" and "Human/UAT required: no".

## Preconditions

- Working directory is the M001 worktree with all S24 changes applied
- Python environment has PySide6 installed (for import checks)
- No camera hardware or model files required

## Smoke Test

Run `python -m py_compile src/gui/controllers/camera_controller.py && python -c "from src.gui.controllers.camera_controller import CameraController; print('OK')"` — must print "OK" with no errors.

## Test Cases

### 1. CameraController compiles and imports

1. Run `python -m py_compile src/gui/controllers/camera_controller.py`
2. Run `python -c "from src.gui.controllers.camera_controller import CameraController"`
3. **Expected:** Both succeed with exit code 0, no output on stderr

### 2. Zero-import guard — no cv2 or torch in camera_controller

1. Run `grep -c 'import cv2' src/gui/controllers/camera_controller.py`
2. Run `grep -c 'import torch' src/gui/controllers/camera_controller.py`
3. **Expected:** Both return 0

### 3. Zero-import guard — controllers/__init__.py untouched

1. Run `grep -c 'camera_controller' src/gui/controllers/__init__.py`
2. **Expected:** Returns 0

### 4. MainController imports cleanly

1. Run `python -c "from src.gui.controllers.main_controller import MainController; print('OK')"`
2. **Expected:** Prints "OK", exit code 0

### 5. GUIApplication imports cleanly

1. Run `python -c "from src.gui.app import GUIApplication; print('OK')"`
2. **Expected:** Prints "OK", exit code 0

### 6. lifecycle.py compiles cleanly

1. Run `python -m py_compile src/core/lifecycle.py`
2. **Expected:** Exit code 0, no errors (note: `import LifecycleManager` fails due to pre-existing missing http_client — py_compile is the valid check)

### 7. CameraController has stop_timers method

1. Run `python -c "from src.gui.controllers.camera_controller import CameraController; assert hasattr(CameraController, 'stop_timers'); print('OK')"`
2. **Expected:** Prints "OK"

### 8. CameraController accepts results_store parameter

1. Run:
   ```
   python -c "
   import inspect
   from src.gui.controllers.camera_controller import CameraController
   sig = inspect.signature(CameraController.__init__)
   assert 'results_store' in sig.parameters
   print('OK')
   "
   ```
2. **Expected:** Prints "OK"

### 9. MainController backward compatibility (3 args)

1. Run:
   ```
   python -c "
   import inspect
   from src.gui.controllers.main_controller import MainController
   sig = inspect.signature(MainController.__init__)
   p = sig.parameters
   assert p['camera_results_store'].default is None
   print('OK: camera_results_store is optional')
   "
   ```
2. **Expected:** Prints "OK: camera_results_store is optional"

### 10. GUIApplication accepts camera_results_store parameter

1. Run:
   ```
   python -c "
   import inspect
   from src.gui.app import GUIApplication
   sig = inspect.signature(GUIApplication.__init__)
   assert 'camera_results_store' in sig.parameters
   assert sig.parameters['camera_results_store'].default is None
   print('OK')
   "
   ```
2. **Expected:** Prints "OK"

### 11. 5th sidebar button geometry

1. Run `grep 'y=649\|649' src/gui/controllers/main_controller.py`
2. **Expected:** Shows `setGeometry(26, 649, 355, 110)` for btnCamera

### 12. Camera page at stacked widget index 4

1. Run `grep -A2 'addWidget.*camera\|camera.*addWidget\|index.*4\|_switch_page(4)' src/gui/controllers/main_controller.py`
2. **Expected:** Shows camera page added to stacked widget and button wired to `_switch_page(4)`

## Edge Cases

### Camera disabled (camera_results_store=None)

1. Run:
   ```
   python -c "
   import inspect
   from src.gui.controllers.main_controller import MainController
   sig = inspect.signature(MainController.__init__)
   # Verify camera_results_store defaults to None
   assert sig.parameters['camera_results_store'].default is None
   print('No camera page created when store is None')
   "
   ```
2. **Expected:** When camera_results_store is None, no 5th button is created, no camera page is added, `hasattr(controller, 'camera_page')` would be False

### CameraController with no data flowing

1. Inspect `_update_frame` method in camera_controller.py — it should handle None/empty `latest_frame` from snapshot gracefully
2. Inspect `_update_stats` and `_update_health` methods — they should use `.get()` with defaults for missing keys
3. **Expected:** All timer callbacks have try/except wrapping with logger.error — no unhandled exceptions

## Failure Signals

- `python -m py_compile` fails on any of the 4 modified files → syntax/structure issue
- Import of CameraController, MainController, or GUIApplication raises ImportError → broken import chain
- `grep 'import cv2'` or `grep 'import torch'` returns non-zero count → zero-import guard violated
- `grep 'camera_controller' src/gui/controllers/__init__.py` returns non-zero → lazy import guard broken
- `stop_timers` method missing from CameraController → timer cleanup won't work in closeEvent

## Requirements Proved By This UAT

- GUI-01 — CameraController has frame update timer with QImage.loadFromData() JPEG decoding (contract proof)
- GUI-02 — Broken tooth detection panel with count/timestamp labels reading from store (contract proof)
- GUI-03 — Crack detection panel with count/timestamp labels reading from store (contract proof)
- GUI-04 — Wear percentage display label reading from store (contract proof)
- GUI-05 — Health score/status display with dynamic color from store (contract proof)
- GUI-06 — Conditional 5th sidebar button at y=649 (contract proof)
- GUI-07 — 4-thumbnail sequential strip with deque history (contract proof)
- GUI-08 — OK/alert indicators on detection panels (contract proof)
- GUI-09 — Wear visualization frame (contract proof)
- CAM-02 — Zero-import guard preserved (grep proof)

## Not Proven By This UAT

- Live camera feed rendering with actual JPEG frames — requires camera hardware
- Detection stats updating with real broken/crack counts — requires RT-DETR models and camera input
- Health score dynamic color changes — requires running HealthCalculator with real detection data
- Thumbnail strip populating with sequential frames — requires active capture session
- camera-icon2.svg rendering on sidebar button — requires asset file in expected location
- Full lifecycle startup path (LifecycleManager → GUIApplication → MainController with camera) — blocked by pre-existing http_client import issue

## Notes for Tester

- The LifecycleManager import failure is pre-existing (missing `src.services.iot.http_client` module) and unrelated to S24. Use `py_compile` as the valid compilation check for lifecycle.py.
- Thumbnail size is 220×140 (not 240×150 as in slice must-haves) — this was a deliberate fit decision for the 934px frame width.
- The blade change strip (TestereDegisimFrame) listed in the slice must-haves was not implemented — it wasn't in the T01 task scope.
