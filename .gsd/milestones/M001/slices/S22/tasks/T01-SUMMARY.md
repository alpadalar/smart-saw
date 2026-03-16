---
id: T01
parent: S22
milestone: M001
provides:
  - Zero-import guard on camera package — `import src.services.camera` is inert
key_files:
  - src/services/camera/__init__.py
key_decisions:
  - Removed all re-exports from __init__.py rather than making them conditional; docstring documents direct submodule import pattern
patterns_established:
  - Camera submodule imports are always direct (e.g., `from src.services.camera.results_store import ...`), never via package-level re-export
observability_surfaces:
  - none (pure import guard — failure is a clear ModuleNotFoundError for cv2)
duration: 5m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Fix __init__.py zero-import guard

**Removed unconditional cv2-triggering imports from camera `__init__.py`; package import is now inert.**

## What Happened

The camera package `__init__.py` had two import lines — `CameraResultsStore` from `results_store` (safe) and `CameraService` from `camera_service` (triggers cv2 at module level). Both imports and the `__all__` list were removed. The module docstring was preserved and extended with usage examples showing the direct submodule import pattern.

## Verification

- `python -c "import src.services.camera; print('OK')"` — **passed**
- `python -m py_compile src/services/camera/__init__.py` — **passed**
- `python -c "from src.services.camera.results_store import CameraResultsStore; print('OK')"` — **passed** (submodule imports unaffected)
- `python -c "assert 'cv2' not in sys.modules"` after importing — **passed** (cv2 not loaded)

### Slice-level verification (partial — T01 is first of 3 tasks):

| Check | Status |
|-------|--------|
| `import src.services.camera` no cv2 | ✅ pass |
| `from ...detection_worker import DetectionWorker` | ✅ pass |
| `from ...ldc_worker import LDCWorker` | ✅ pass |
| `py_compile __init__.py` | ✅ pass |
| `py_compile detection_worker.py` | ✅ pass |
| `py_compile ldc_worker.py` | ✅ pass |
| `py_compile lifecycle.py` | ✅ pass |
| DetectionWorker accepts `db_service=None` | ⬜ T02 |
| LDCWorker accepts `db_service=None` | ⬜ T02 |
| `_init_camera()` references all camera objects | ⬜ T03 |
| `stop()` stops camera before SQLite flush | ⬜ T03 |
| INSERT SQL matches schemas | ⬜ T02 |
| logger.warning on write_async failure | ⬜ T02 |

## Diagnostics

No runtime surfaces — this is a static import guard. If someone re-adds an unconditional import, `python -c "import src.services.camera"` will fail with `ModuleNotFoundError: No module named 'cv2'` in environments without opencv.

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/services/camera/__init__.py` — removed unconditional imports and `__all__`; kept and extended docstring with direct import examples
