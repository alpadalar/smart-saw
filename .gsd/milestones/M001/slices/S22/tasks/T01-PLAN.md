---
estimated_steps: 3
estimated_files: 1
---

# T01: Fix __init__.py zero-import guard

**Slice:** S22 — Lifecycle & DB Integration
**Milestone:** M001

## Description

The camera package `__init__.py` unconditionally imports `CameraService` from `camera_service.py`, which in turn does `import cv2` at module level. This means any code that does `import src.services.camera` triggers a cv2 import even when `camera.enabled=false`. The lifecycle imports from submodules directly (e.g., `from src.services.camera.results_store import CameraResultsStore`), so the `__init__.py` re-exports aren't needed.

Fix by removing the unconditional imports that trigger cv2. Keep the docstring for package documentation.

## Steps

1. Open `src/services/camera/__init__.py`. Current content imports `CameraResultsStore` from `results_store` (safe — no cv2 dep) and `CameraService` from `camera_service` (triggers cv2). Remove both import lines and the `__all__` list. Keep the module docstring describing what the package contains.
2. Verify: `python -c "import src.services.camera; print('OK')"` — must succeed without cv2 installed/imported.
3. Verify: `python -m py_compile src/services/camera/__init__.py` — syntax OK.

## Must-Haves

- [ ] `import src.services.camera` does not trigger cv2 import
- [ ] Package docstring preserved describing contained modules
- [ ] No existing imports broken (lifecycle imports from submodules directly, not from `__init__.py`)

## Verification

- `python -c "import src.services.camera; print('OK')"` succeeds
- `python -m py_compile src/services/camera/__init__.py` passes
- `python -c "from src.services.camera.results_store import CameraResultsStore; print('OK')"` still works (submodule import unaffected)

## Inputs

- `src/services/camera/__init__.py` — current file with unconditional cv2-triggering imports

## Expected Output

- `src/services/camera/__init__.py` — cleaned: docstring only, no unconditional imports that trigger cv2/torch
