# S11: Initial Delay Logic

**Goal:** Make initial_delay logic mode-aware: only apply to ML mode, skip for manual mode.
**Demo:** Make initial_delay logic mode-aware: only apply to ML mode, skip for manual mode.

## Must-Haves


## Tasks

- [x] **T01: 11-initial-delay-logic 01** `est:1min`
  - Make initial_delay logic mode-aware: only apply to ML mode, skip for manual mode.

Purpose: Manual mode should have no artificial delay at cutting start — operator expects immediate control response. ML mode retains delay to allow material engagement before AI adjustments.
Output: Modified ControlManager with mode-aware initial delay behavior.

## Files Likely Touched

- `src/services/control/manager.py`
