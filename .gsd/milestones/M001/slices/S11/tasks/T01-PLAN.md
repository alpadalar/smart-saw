# T01: 11-initial-delay-logic 01

**Slice:** S11 — **Milestone:** M001

## Description

Make initial_delay logic mode-aware: only apply to ML mode, skip for manual mode.

Purpose: Manual mode should have no artificial delay at cutting start — operator expects immediate control response. ML mode retains delay to allow material engagement before AI adjustments.
Output: Modified ControlManager with mode-aware initial delay behavior.

## Files

- `src/services/control/manager.py`
