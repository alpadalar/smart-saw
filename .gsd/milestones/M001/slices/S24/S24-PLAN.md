# S24: Camera GUI

**Goal:** Camera page with live feed, detection stats, wear %, health score, thumbnails, and sidebar nav button — all reading from CameraResultsStore.
**Demo:** With camera.enabled=true, a 5th sidebar button appears. Clicking it switches to the camera page showing live frame area, broken/crack detection panels, sequential thumbnails strip, wear percentage, health score with status text and color, and OK/alert indicators. With camera.enabled=false, no camera button or page exists.

## Must-Haves

- CameraController widget with programmatic layout (no .ui file), reading exclusively from CameraResultsStore
- 3 QTimers: 500ms (frame update), 1000ms (detection stats), 2000ms (health/wear)
- Live feed display using QImage.loadFromData() for JPEG decoding (no cv2 in GUI)
- Broken tooth and crack detection panels with count, timestamp, OK/alert indicators
- 4-thumbnail sequential images strip (240×150 each)
- Wear percentage, health score, health status displays with dynamic color
- 5th sidebar nav button at y=649, conditionally created when camera_results_store is provided
- Camera page at stacked widget index 4
- stop_timers() called in MainController.closeEvent()
- Zero-import guard: no module-level imports of camera_controller, cv2, or torch
- controllers/__init__.py must NOT import CameraController

## Proof Level

- This slice proves: contract
- Real runtime required: no (no camera hardware)
- Human/UAT required: no

## Verification

- `python -m py_compile src/gui/controllers/camera_controller.py` — compiles clean
- `python -c "from src.gui.controllers.camera_controller import CameraController"` — imports without error
- `python -c "from src.gui.controllers.main_controller import MainController"` — imports without error
- `python -c "from src.gui.app import GUIApplication"` — imports without error
- `python -c "from src.core.lifecycle import LifecycleManager"` — imports without error
- Grep verify: `grep -c 'import cv2' src/gui/controllers/camera_controller.py` returns 0
- Grep verify: `grep -c 'import torch' src/gui/controllers/camera_controller.py` returns 0
- Grep verify: `grep -c 'camera_controller' src/gui/controllers/__init__.py` returns 0
- MainController constructor still works with 3 args (backward compat)
- CameraController has stop_timers() method
- 5th button geometry: y=649

## Observability / Diagnostics

- Runtime signals: logger.info on CameraController init, logger.error on frame decode failures and timer callback exceptions
- Inspection surfaces: QLabel text values for detection counts, wear %, health score — readable via Qt introspection
- Failure visibility: Frame decode errors logged with exception context; timer callback errors caught and logged per-callback
- Redaction constraints: none

## Integration Closure

- Upstream surfaces consumed: `src/services/camera/results_store.py` (CameraResultsStore.snapshot() API), `src/core/lifecycle.py` (camera_results_store attribute), `src/gui/app.py` (GUIApplication constructor), `src/gui/controllers/main_controller.py` (sidebar + stacked widget)
- New wiring introduced: lifecycle → GUIApplication → MainController → CameraController creation chain; 5th sidebar button; page index 4 in stacked widget; stop_timers() in closeEvent
- What remains before the milestone is truly usable end-to-end: nothing — S24 is the final slice in M001

## Tasks

- [ ] **T01: Build CameraController widget** `est:1h30m`
  - Why: The camera page is the core deliverable — a self-contained QWidget that reads CameraResultsStore and displays all camera vision data. Covers GUI-01 through GUI-05, GUI-07, GUI-08, GUI-09.
  - Files: `src/gui/controllers/camera_controller.py`
  - Do: Create CameraController(results_store, parent=None) QWidget with programmatic layout for 1528×1080 content area. 8 sub-frames: KameraFrame (live feed ~934×525), SiraliGoruntuFrame (4 thumbnails 934×150), KirikTespitiFrame (broken detection ~505×438), CatlakTespitiFrame (crack detection ~505×438), TestereDegisimFrame (blade change strip), AsinmaYuzdesiFrame (wear % 260×105), TestereSagligiFrame (health score 260×105), TestereDurumuFrame (health status 260×105). 3 QTimers for frame/stats/health updates. Use QImage.loadFromData() for JPEG→QPixmap (no cv2). Include stop_timers() method. All styling matches dark theme (#0A0E1A background, #F4F6FC text, rgba frames). No module-level cv2/torch imports.
  - Verify: `python -m py_compile src/gui/controllers/camera_controller.py && python -c "from src.gui.controllers.camera_controller import CameraController; print('OK')"` succeeds. `grep -c 'import cv2\|import torch' src/gui/controllers/camera_controller.py` returns 0.
  - Done when: CameraController compiles, imports, has stop_timers(), takes results_store param, has no cv2/torch module-level imports
- [ ] **T02: Wire camera page into application stack** `est:30m`
  - Why: Thread camera_results_store through the creation chain and add the 5th sidebar button + camera page to MainController. Covers GUI-06 and CAM-02 (zero-import guard preservation).
  - Files: `src/core/lifecycle.py`, `src/gui/app.py`, `src/gui/controllers/main_controller.py`, `src/gui/controllers/__init__.py`
  - Do: (1) lifecycle._init_gui(): pass camera_results_store=self.camera_results_store to GUIApplication constructor. (2) GUIApplication.__init__(): accept camera_results_store=None param, store it, pass to MainController constructor. (3) MainController.__init__(): accept camera_results_store=None param. If truthy: lazy-import CameraController inside the guard, create 5th sidebar button (btnCamera, y=649, camera-icon2.svg), append to nav_buttons, create CameraController page, addWidget at index 4, wire click to _switch_page(4). (4) MainController.closeEvent(): add camera_page to stop_timers loop if it exists. (5) Do NOT add CameraController to controllers/__init__.py — it's lazy-imported only.
  - Verify: `python -m py_compile src/gui/controllers/main_controller.py && python -m py_compile src/gui/app.py && python -m py_compile src/core/lifecycle.py` all succeed. `grep -c 'camera_controller' src/gui/controllers/__init__.py` returns 0.
  - Done when: All 4 files compile clean, MainController works with and without camera_results_store, __init__.py unchanged, zero-import guard preserved

## Files Likely Touched

- `src/gui/controllers/camera_controller.py` — NEW
- `src/gui/controllers/main_controller.py` — MODIFIED
- `src/gui/app.py` — MODIFIED
- `src/core/lifecycle.py` — MODIFIED
