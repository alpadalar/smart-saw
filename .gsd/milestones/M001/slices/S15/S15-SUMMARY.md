---
id: S15
parent: M001
milestone: M001
provides:
  - TouchButton widget for dual mouse/touch support
  - Touch event handling for positioning buttons
  - Emergency stop overlay during jog operations
requires: []
affects: []
key_files:
  - "src/gui/widgets/touch_button.py"
  - "src/gui/controllers/positioning_controller.py"
key_decisions:
  - "Touch instant activation (0ms delay) — industrial users expect immediate response"
  - "Strict touch bounds, no tolerance zone — prevents accidental adjacent button activation"
  - "First button wins multi-touch — prevents conflicting jog commands"
  - "Emergency stop always responsive — safety feature must be accessible"
  - "Stop jog on focusOutEvent — safety mechanism for backgrounded app"
patterns_established:
  - "Dual input handling (mouse + touch on same widget)"
  - "First-touch-wins multi-touch conflict resolution"
  - "Safety overlay pattern (emergency stop during active operation)"
observability_surfaces: []
drill_down_paths: []
duration: 3min
verification_result: passed
completed_at: 2026-01-30
blocker_discovered: false
---
# S15: Touch Long Press Fix

**TouchButton widget with Qt touch events, instant activation, strict bounds checking, emergency stop overlay, and app focus loss safety**

## What Happened

Implemented touch event support for positioning buttons to enable hold-to-jog functionality on industrial touchscreen HMI.

## Accomplishments

- Created TouchButton class extending QPushButton with Qt touch event handling
- Instant activation (0ms) on touch down, strict button bounds checking
- First-touch-wins multi-touch conflict resolution
- Emergency stop overlay button (300x150px, centered at bottom, "ACIL DURDUR")
- App focus loss safety: stops jog on focusOutEvent

## Files Changed

- `src/gui/widgets/touch_button.py` (252 lines, created)
- `src/gui/widgets/__init__.py` (8 lines, created)
- `src/gui/controllers/positioning_controller.py` (+140 lines)

## Commits

1. **f52365a** — feat: create TouchButton widget with mouse and touch event handling
2. **3f7e571** — feat: update PositioningController with TouchButton and emergency stop

---
*Completed: 2026-01-30*
