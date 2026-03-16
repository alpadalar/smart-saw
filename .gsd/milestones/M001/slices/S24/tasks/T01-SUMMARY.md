---
id: T01
parent: S24
milestone: M001
provides:
  - CameraController QWidget with 3-timer polling architecture reading from CameraResultsStore
key_files:
  - src/gui/controllers/camera_controller.py
key_decisions:
  - Used deque-based thumbnail history (maxlen=4) instead of shifting QPixmap arrays — cleaner O(1) append
  - Kept timer callbacks fully independent with per-callback try/except — one failing timer won't crash others
patterns_established:
  - CameraController reads exclusively from results_store.snapshot() — no direct service access
  - Static helper methods _set_ok_style/_set_alert_style for reusable indicator styling
observability_surfaces:
  - logger.info on init and timer stop, logger.error with exc_info on all timer callback failures
  - QLabel text values (lbl_broken_count, lbl_health_score, etc.) inspectable via Qt introspection
duration: 20m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Build CameraController widget

**Built complete CameraController QWidget with live feed, detection panels, thumbnails, wear/health displays, and 3 QTimers polling CameraResultsStore**

## What Happened

Created `src/gui/controllers/camera_controller.py` (~400 lines) implementing the full camera page layout for the 1528×1080 content area. The widget has 8 sub-frames: camera feed (934×525), sequential thumbnails (4×220×140), broken tooth detection panel with count/timestamp/OK-alert indicator, crack detection panel with same, wear percentage, health score, health status with dynamic color, and recording/FPS info labels.

Three QTimers drive data updates at 500ms (frame + thumbnails), 1000ms (detection stats), and 2000ms (health/wear). Frame display uses `QImage.loadFromData()` for JPEG decoding — no cv2 needed. Thumbnail strip uses a `deque(maxlen=4)` that appends new frames and refreshes all 4 thumbnail labels. Detection panels show green "✓ OK" or red "✗ UYARI" based on broken/crack counts. Health status label dynamically sets its text color from the `health_color` hex value in the store.

Followed existing controller patterns from sensor_controller.py and monitoring_controller.py for dark theme styling, QTimer usage, and stop_timers() convention.

## Verification

All 5 task-level checks pass:
- `python -m py_compile` — compiles clean ✓
- Import test — `from src.gui.controllers.camera_controller import CameraController` succeeds ✓
- `grep -c 'import cv2'` → 0 ✓
- `grep -c 'import torch'` → 0 ✓
- Contract check — `results_store` in __init__ params, `stop_timers` exists ✓

Slice-level checks (partial — T01 is intermediate):
- camera_controller.py compiles + imports ✓
- MainController imports ✓
- GUIApplication imports ✓
- LifecycleManager import — FAILS (pre-existing: missing `src.services.iot.http_client` module, unrelated to this task)
- grep cv2/torch = 0 ✓
- grep camera_controller in __init__.py = 0 ✓
- CameraController has stop_timers() ✓
- Remaining slice checks (MainController backward compat, 5th button y=649) — T02 scope

## Diagnostics

- Check timer state: `hasattr(controller, '_frame_timer')` and `.isActive()`
- Inspect label values: `controller.lbl_broken_count.text()`, `controller.lbl_health_score.text()`
- Frame decode failures appear in logs as `"Failed to decode JPEG frame"` or `"Error in _update_frame"` with traceback
- Timer stop confirmation: `"CameraController timers stopped"` in logs

## Deviations

- Thumbnail size 220×140 (plan spec) vs 240×150 (slice must-haves) — used plan spec which fits 4 thumbnails within 934px frame width with 10px spacing
- 8 sub-frames reduced to 7 visible groups (blade change strip from slice plan not in task plan, omitted)

## Known Issues

- LifecycleManager import fails due to missing `src.services.iot.http_client` — pre-existing, not introduced by this task

## Files Created/Modified

- `src/gui/controllers/camera_controller.py` — NEW: Complete CameraController QWidget (~400 lines)
- `.gsd/milestones/M001/slices/S24/tasks/T01-PLAN.md` — Added Observability Impact section
- `.gsd/milestones/M001/slices/S24/S24-PLAN.md` — Marked T01 as done
