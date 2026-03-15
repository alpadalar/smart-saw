# S10: Ai Mode Switch Fix

**Goal:** Fix cross-thread asyncio scheduling in GUI mode switch operations.
**Demo:** Fix cross-thread asyncio scheduling in GUI mode switch operations.

## Must-Haves


## Tasks

- [x] **T01: 10-ai-mode-switch-fix 01** `est:3min`
  - Fix cross-thread asyncio scheduling in GUI mode switch operations.

Purpose: GUI thread (Qt) cannot safely schedule coroutines on main thread's asyncio loop using `asyncio.ensure_future()`. This causes mode switch failures when clicking AI/Manual mode buttons.

Output: Mode switching works correctly from GUI thread via `asyncio.run_coroutine_threadsafe()`.

## Files Likely Touched

- `src/core/lifecycle.py`
- `src/gui/app.py`
- `src/gui/controllers/main_controller.py`
- `src/gui/controllers/control_panel_controller.py`
