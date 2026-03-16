---
estimated_steps: 5
estimated_files: 4
---

# T02: Wire camera page into application stack

**Slice:** S24 — Camera GUI
**Milestone:** M001

## Description

Thread `camera_results_store` through the creation chain: lifecycle → GUIApplication → MainController → CameraController. Add conditional 5th sidebar button and camera page to the stacked widget. Preserve zero-import guard — CameraController is lazy-imported inside the config guard, not at module level.

## Steps

1. **Edit `src/core/lifecycle.py`** — In `_init_gui()`, pass `camera_results_store=self.camera_results_store` as a keyword argument to the `GUIApplication(...)` constructor call. The attribute `self.camera_results_store` already exists on LifecycleManager (set in `_init_camera()`, defaults to None).

   Find this line (around line 493):
   ```python
   self.gui_app = GUIApplication(
       self.control_manager,
       self.data_pipeline,
       event_loop=event_loop
   )
   ```
   Add `camera_results_store=self.camera_results_store` as a 4th kwarg.

2. **Edit `src/gui/app.py`** — Add `camera_results_store=None` parameter to `GUIApplication.__init__()`. Store as `self.camera_results_store`. Pass it through to `MainController(...)` constructor in `_run_gui()`.

   Constructor change:
   ```python
   def __init__(self, control_manager, data_pipeline, event_loop=None, camera_results_store=None):
   ```
   Store: `self.camera_results_store = camera_results_store`
   
   In `_run_gui()` where MainController is created:
   ```python
   self._main_window = MainController(
       self.control_manager,
       self.data_pipeline,
       event_loop=self.event_loop,
       camera_results_store=self.camera_results_store
   )
   ```

3. **Edit `src/gui/controllers/main_controller.py`** — Add `camera_results_store=None` parameter to `MainController.__init__()`. Store it. After existing sidebar buttons are created (after btnTracking), conditionally create 5th button and camera page:

   In `__init__` signature:
   ```python
   def __init__(self, control_manager, data_pipeline, event_loop=None, camera_results_store=None):
   ```
   Store: `self.camera_results_store = camera_results_store`

   In `_setup_ui()`, after `self.nav_buttons = [...]` list is created and before the stacked widget section, add:
   ```python
   # Conditional camera button
   if self.camera_results_store is not None:
       self.btnCamera = QPushButton("  Kamera", self.sidebarFrame)
       self.btnCamera.setGeometry(26, 649, 355, 110)
       self.btnCamera.setIcon(self._icon("camera-icon2.svg"))
       self.btnCamera.setIconSize(QSize(80, 80))
       self.btnCamera.setStyleSheet(nav_btn_style)
       self.btnCamera.setCheckable(True)
       self.btnCamera.clicked.connect(lambda: self._switch_page(4))
       self.nav_buttons.append(self.btnCamera)
   ```

   After existing pages are added to stacked widget (after index 3 monitoring), add:
   ```python
   # Conditional camera page
   if self.camera_results_store is not None:
       from .camera_controller import CameraController
       self.camera_page = CameraController(
           self.camera_results_store,
           parent=self.stackedWidget
       )
       self.stackedWidget.addWidget(self.camera_page)  # Index 4
   ```

   In `closeEvent()`, after the existing page stop_timers loop, add:
   ```python
   # Stop camera page timers if it exists
   if hasattr(self, 'camera_page') and self.camera_page and hasattr(self.camera_page, 'stop_timers'):
       self.camera_page.stop_timers()
   ```

4. **Verify `src/gui/controllers/__init__.py`** — Confirm it does NOT import CameraController. Do not modify this file. The zero-import guard requires CameraController to be lazy-imported only inside the config check in main_controller.py.

5. **Run all compile checks:**
   - `python -m py_compile src/core/lifecycle.py`
   - `python -m py_compile src/gui/app.py`
   - `python -m py_compile src/gui/controllers/main_controller.py`
   - Import checks for all three modules
   - Verify `grep -c 'camera_controller' src/gui/controllers/__init__.py` returns 0

## Must-Haves

- [ ] camera_results_store=None parameter in GUIApplication.__init__()
- [ ] camera_results_store=None parameter in MainController.__init__()
- [ ] camera_results_store passed from lifecycle → GUIApplication → MainController
- [ ] 5th sidebar button (btnCamera) at y=649 with camera-icon2.svg, only when camera_results_store is provided
- [ ] CameraController lazy-imported inside `if self.camera_results_store is not None:` guard
- [ ] Camera page added at stacked widget index 4
- [ ] camera_page.stop_timers() called in closeEvent
- [ ] controllers/__init__.py does NOT import CameraController
- [ ] Backward compatibility: MainController still works with 3 positional args (no camera)

## Verification

- `python -m py_compile src/core/lifecycle.py` — compiles clean
- `python -m py_compile src/gui/app.py` — compiles clean
- `python -m py_compile src/gui/controllers/main_controller.py` — compiles clean
- `python -c "from src.core.lifecycle import LifecycleManager; print('OK')"` — imports
- `python -c "from src.gui.app import GUIApplication; print('OK')"` — imports
- `python -c "from src.gui.controllers.main_controller import MainController; print('OK')"` — imports
- `grep -c 'camera_controller' src/gui/controllers/__init__.py` → 0
- `python -c "import inspect; from src.gui.app import GUIApplication; sig = inspect.signature(GUIApplication.__init__); assert 'camera_results_store' in sig.parameters, 'Missing param'; print('GUIApp OK')"` — passes
- `python -c "import inspect; from src.gui.controllers.main_controller import MainController; sig = inspect.signature(MainController.__init__); assert 'camera_results_store' in sig.parameters, 'Missing param'; print('MainCtrl OK')"` — passes

## Inputs

- `src/gui/controllers/camera_controller.py` — T01 output: CameraController(results_store, parent=None) widget with stop_timers()
- `src/core/lifecycle.py` — Has self.camera_results_store attribute (set in _init_camera, None when camera disabled)
- `src/gui/app.py` — GUIApplication creates MainController in _run_gui()
- `src/gui/controllers/main_controller.py` — Sidebar buttons at y=165/286/407/528, stacked widget with 4 pages at indices 0-3

## Expected Output

- `src/core/lifecycle.py` — MODIFIED: passes camera_results_store to GUIApplication
- `src/gui/app.py` — MODIFIED: accepts and forwards camera_results_store
- `src/gui/controllers/main_controller.py` — MODIFIED: conditional 5th button + camera page + closeEvent wiring

## Observability Impact

- **Camera page presence:** `hasattr(main_controller, 'camera_page')` — True only when camera_results_store was provided
- **Button count:** `len(main_controller.nav_buttons)` — 5 when camera enabled, 4 when disabled
- **Stacked widget page count:** `main_controller.stackedWidget.count()` — 5 when camera enabled, 4 when disabled
- **Timer cleanup:** `"CameraController timers stopped"` appears in logs during closeEvent when camera page exists
- **Failure visibility:** If CameraController import fails at runtime, the error surfaces immediately during MainController._setup_ui() — not silently swallowed
