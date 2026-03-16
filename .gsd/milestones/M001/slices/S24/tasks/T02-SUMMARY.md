---
id: T02
parent: S24
milestone: M001
provides:
  - camera_results_store threaded through lifecycle → GUIApplication → MainController
  - Conditional 5th sidebar button and camera page at stacked widget index 4
  - closeEvent wiring for camera page timer cleanup
key_files:
  - src/core/lifecycle.py
  - src/gui/app.py
  - src/gui/controllers/main_controller.py
key_decisions:
  - Kept camera button/page creation fully inside `if self.camera_results_store is not None` guard — no else branch, no placeholder
patterns_established:
  - Lazy import of CameraController inside config guard — maintains zero-import boundary between camera subsystem and GUI
observability_surfaces:
  - hasattr(main_controller, 'camera_page') indicates camera GUI is active
  - nav_buttons length (4 vs 5) and stackedWidget.count() (4 vs 5) reflect camera state
  - CameraController timers stopped log line in closeEvent confirms cleanup
duration: 12m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T02: Wire camera page into application stack

**Threaded camera_results_store through lifecycle → GUIApplication → MainController with conditional 5th sidebar button and camera page at index 4.**

## What Happened

Added `camera_results_store=None` as a keyword parameter to both `GUIApplication.__init__()` and `MainController.__init__()`. In `lifecycle._init_gui()`, the existing `self.camera_results_store` attribute (set in `_init_camera`, None when camera disabled) is now passed through to GUIApplication, which forwards it to MainController.

In `MainController._setup_ui()`, when `camera_results_store` is not None: a 5th sidebar button ("Kamera") is created at y=649 with `camera-icon2.svg`, appended to `nav_buttons`, and wired to `_switch_page(4)`. CameraController is lazy-imported inside the guard and instantiated with the results store as its sole data source. The camera page is added to the stacked widget at index 4.

In `closeEvent()`, camera page `stop_timers()` is called if the page exists — using `hasattr` checks so it's safe when camera is disabled.

## Verification

All checks passed:

- `python -m py_compile` — lifecycle.py, app.py, main_controller.py all compile clean
- `from src.gui.app import GUIApplication` — imports OK
- `from src.gui.controllers.main_controller import MainController` — imports OK
- `grep -c 'camera_controller' src/gui/controllers/__init__.py` → 0 (zero-import guard intact)
- `inspect.signature(GUIApplication.__init__)` — contains `camera_results_store` param
- `inspect.signature(MainController.__init__)` — contains `camera_results_store` param
- Backward compat: only `control_manager` and `data_pipeline` are required params (event_loop and camera_results_store default to None)

Slice-level checks (all passing at T02):
- camera_controller.py compiles and imports ✓
- No cv2/torch imports in camera_controller.py ✓
- No camera_controller in __init__.py ✓
- MainController backward compat with 3 args ✓
- CameraController has stop_timers() ✓
- lifecycle.py compile clean ✓ (import fails due to pre-existing missing iot.http_client module — not from this change)

## Diagnostics

- Camera page presence: `hasattr(controller, 'camera_page')` — True only when camera_results_store provided
- Button count: `len(controller.nav_buttons)` — 5 with camera, 4 without
- Stacked widget: `controller.stackedWidget.count()` — 5 with camera, 4 without
- Timer cleanup confirmation: `"CameraController timers stopped"` in logs during window close

## Deviations

None.

## Known Issues

- `from src.core.lifecycle import LifecycleManager` fails due to pre-existing missing `src.services.iot.http_client` module — unrelated to camera wiring. AST parse and py_compile both succeed for lifecycle.py.

## Files Created/Modified

- `src/core/lifecycle.py` — Added camera_results_store kwarg to GUIApplication constructor call
- `src/gui/app.py` — Added camera_results_store=None param, stored it, forwarded to MainController
- `src/gui/controllers/main_controller.py` — Added camera_results_store=None param, conditional 5th sidebar button + camera page + closeEvent stop_timers wiring
