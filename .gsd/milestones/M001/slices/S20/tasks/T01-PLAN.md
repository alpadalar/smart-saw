---
estimated_steps: 6
estimated_files: 4
---

# T01: Merge S19 foundation and build CameraResultsStore

**Slice:** S20 — Camera Capture
**Milestone:** M001

## Description

Two things must happen before any camera code can be built: (1) S19's foundation work — camera config in `config.yaml`, `SCHEMA_CAMERA_DB` in `schemas.py`, `_init_camera()` in `lifecycle.py`, camera module scaffold, numpy uncap — exists only on a diverged branch and must be merged into the worktree. (2) `CameraResultsStore` is the thread-safe singleton dict that serves as the sole integration boundary between camera threads and all consumers (GUI, IoT, detection, DB). It has zero external dependencies and must exist before `CameraService`.

## Steps

1. **Cherry-pick S19 commits into worktree branch.** Run `git cherry-pick 8dfbdb0 2131ac2` to bring in the two S19 feat commits. These add: numpy uncap (`>=1.24.0` without `<2.0`), `np.ptp()` replacement, camera config section in `config/config.yaml`, `SCHEMA_CAMERA_DB` in `src/services/database/schemas.py` with `detection_events` and `wear_history` tables, `_init_camera()` in `src/core/lifecycle.py` with config guard, and `src/services/camera/__init__.py` scaffold. Resolve any merge conflicts (likely in `.gsd/` files — use `--no-commit` if needed and reset `.gsd/` changes, then commit only src/config/requirements changes).

2. **Add `opencv-python-headless>=4.11.0` to `requirements.txt`.** Must be `headless` variant — `opencv-python` (non-headless) bundles Qt5/Qt6 which conflicts with PySide6. Place it near other heavy deps.

3. **Install dependencies.** Run `pip install opencv-python-headless>=4.11.0` (or `pip install -r requirements.txt`). Verify with `python -c "import cv2; print(cv2.__version__)"`.

4. **Create `src/services/camera/results_store.py`.** Implement `CameraResultsStore`:
   - `import threading` at top
   - Internal `self._data: dict = {}` and `self._lock = threading.Lock()`
   - `update(key: str, value: Any) -> None` — acquires lock, sets `_data[key] = value`
   - `update_batch(data: dict) -> None` — acquires lock, calls `_data.update(data)`
   - `get(key: str, default: Any = None) -> Any` — acquires lock, returns `_data.get(key, default)`
   - `snapshot() -> dict` — acquires lock, returns `dict(self._data)` (a shallow copy — NOT a reference)
   - All methods are thread-safe via the single Lock
   - Standard keys documented in docstring: `latest_frame` (bytes), `frame_count` (int), `is_recording` (bool), `recording_path` (str|None), `fps_actual` (float)

5. **Update `src/services/camera/__init__.py`** to export `CameraResultsStore`: `from src.services.camera.results_store import CameraResultsStore`.

6. **Verify.** Run:
   - `python -c "from src.services.camera.results_store import CameraResultsStore; s = CameraResultsStore(); s.update('k', 1); assert s.get('k') == 1; d = s.snapshot(); assert isinstance(d, dict); assert d == {'k': 1}; s.update('k', 2); assert d['k'] == 1; print('OK')"`
   - `python -c "import cv2; print(cv2.__version__)"`
   - `grep 'opencv-python-headless' requirements.txt`
   - Confirm `config/config.yaml` has `camera:` section
   - Confirm `src/services/database/schemas.py` has `SCHEMA_CAMERA_DB`
   - Confirm `src/core/lifecycle.py` has `_init_camera` method

## Must-Haves

- [ ] S19 commits cherry-picked — camera config, DB schema, lifecycle stub, camera scaffold, numpy uncap all present in worktree
- [ ] `opencv-python-headless>=4.11.0` in requirements.txt and importable
- [ ] `CameraResultsStore` class with thread-safe `update()`, `update_batch()`, `get()`, `snapshot()`
- [ ] `snapshot()` returns a copy, not a reference to internal dict
- [ ] `CameraResultsStore` exported from `src/services/camera/__init__.py`

## Verification

- `python -c "from src.services.camera.results_store import CameraResultsStore; s = CameraResultsStore(); s.update('k', 1); assert s.get('k') == 1; d = s.snapshot(); s.update('k', 2); assert d['k'] == 1; print('OK')"` prints OK
- `python -c "import cv2; print(cv2.__version__)"` succeeds
- `grep 'SCHEMA_CAMERA_DB' src/services/database/schemas.py` matches
- `grep '_init_camera' src/core/lifecycle.py` matches
- `grep 'camera:' config/config.yaml` matches

## Observability Impact

- **New signal:** `CameraResultsStore.snapshot()` — returns full state dict; any consumer or diagnostic script can call this to inspect current camera data (latest_frame, frame_count, is_recording, etc.)
- **Inspection:** `python -c "from src.services.camera.results_store import CameraResultsStore; s = CameraResultsStore(); print(s.snapshot())"` shows `{}` on fresh store — useful baseline to confirm store is empty before service starts
- **Failure state:** Store methods never raise (get returns default, snapshot returns empty dict) — failures are silent by design since the store is a passive data holder. Consumer-level errors surface upstream.

## Inputs

- S19 commits `8dfbdb0` and `2131ac2` on diverged branch — contain all foundation artifacts
- Old project reference: `CameraModule` used `data_lock` + scattered state — `CameraResultsStore` replaces this pattern with a clean API

## Expected Output

- `src/services/camera/results_store.py` — New file: `CameraResultsStore` class
- `src/services/camera/__init__.py` — Updated with `CameraResultsStore` export
- `requirements.txt` — `opencv-python-headless>=4.11.0` added
- S19 artifacts present: camera config in `config.yaml`, `SCHEMA_CAMERA_DB` in `schemas.py`, `_init_camera()` in `lifecycle.py`
