---
phase: 26-otomatik-kesim-controller
reviewed: 2026-04-09T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - src/gui/controllers/otomatik_kesim_controller.py
  - src/gui/numpad.py
  - tests/test_otomatik_kesim_controller.py
findings:
  critical: 0
  warning: 4
  info: 3
  total: 7
status: issues_found
---

# Phase 26: Code Review Report

**Reviewed:** 2026-04-09T00:00:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Three files were reviewed: the new `OtomatikKesimController` widget, the `NumpadDialog` helper, and the unit test suite. The controller is well-structured overall — guard clauses are consistent, the ML reset pitfall (Pitfall 4 / T-26-07) is correctly addressed, and the test fixture uses the established `__new__` + injection pattern cleanly.

Four warnings were found, all in the controller: one is a logic bug in the RESET hold sequence that contradicts the docstring's stated safety guarantee (stuck PLC bit); one is a missing style-swap on mode-toggle buttons that makes the UI visually broken; one is a dead code branch that can never execute; and one is a missing style reset that leaves the counter permanently green after cancel. Three informational items cover a slightly misleading `_l_value` persistence path, a minor test coverage gap, and a floating-point comparison smell.

---

## Warnings

### WR-01: RESET stuck-bit — `reset_auto_cutting(False)` never called after full hold

**File:** `src/gui/controllers/otomatik_kesim_controller.py:808-822`

**Issue:** The docstring for `_on_reset_release` states: *"Always calls reset_auto_cutting(False) to clear bit 20.14 regardless of elapsed time (T-26-08: prevents stuck bit)."* The implementation contradicts this: `reset_auto_cutting(False)` is gated behind `if elapsed < 1.5`. When the user holds for the full 1500 ms, `_on_reset_tick` calls `reset_auto_cutting(True)` and stops the tick timer, but `_reset_in_progress` remains `True`. On finger lift, `_on_reset_release` runs, `elapsed >= 1.5`, so `reset_auto_cutting(False)` is **never called**. PLC bit 20.14 stays asserted — exactly the stuck-bit the comment warns against.

**Fix:**
```python
def _on_reset_release(self) -> None:
    if not self._reset_in_progress:
        return
    self._reset_tick_timer.stop()
    elapsed = time.monotonic() - self._reset_start
    if elapsed < 1.5 and self.machine_control:
        self.machine_control.reset_auto_cutting(False)
    elif elapsed >= 1.5 and self.machine_control:
        # Full hold already sent True; always clear the bit on release
        self.machine_control.reset_auto_cutting(False)
    self._reset_in_progress = False
    self._reset_progress = 0.0
    self.btnReset.update()
```

Or more concisely — call `reset_auto_cutting(False)` unconditionally and let the PLC handle idempotency:

```python
    self._reset_tick_timer.stop()
    elapsed = time.monotonic() - self._reset_start
    if elapsed < 1.5 and self.machine_control:
        self.machine_control.reset_auto_cutting(False)
    if elapsed >= 1.5 and self.machine_control:
        self.machine_control.reset_auto_cutting(False)  # clear after full hold
```

---

### WR-02: ML mode toggle buttons do not visually update on mode switch

**File:** `src/gui/controllers/otomatik_kesim_controller.py:944-953, 955-963`

**Issue:** `btnManual` and `btnAI` are initialized with static stylesheets (`_button_checked_style` on `btnManual`, `_button_default_style` on `btnAI`). Neither `_switch_to_mode` nor `_sync_ml_mode` calls `setStyleSheet()` — they only call `setChecked(True/False)`. Because the stylesheet strings contain only `QPushButton {}` rules (not `QPushButton:checked {}`), `setChecked` has no visual effect. After switching to AI mode the `btnManual` button remains visually highlighted (pink gradient) and `btnAI` remains visually unlit.

**Fix:** Update both stylesheet assignments in `_switch_to_mode` and `_sync_ml_mode`:
```python
def _switch_to_mode(self, mode: ControlMode) -> None:
    manual_active = (mode == ControlMode.MANUAL)
    self.btnManual.setChecked(manual_active)
    self.btnAI.setChecked(not manual_active)
    self.btnManual.setStyleSheet(
        self._button_checked_style if manual_active else self._button_default_style
    )
    self.btnAI.setStyleSheet(
        self._button_checked_style if not manual_active else self._button_default_style
    )
    if self.control_manager and self.event_loop:
        asyncio.run_coroutine_threadsafe(
            self.control_manager.set_mode(mode),
            self.event_loop,
        )
    logger.info(f"ML mode switched to: {mode.value}")
```

Apply the same pattern to `_sync_ml_mode`.

---

### WR-03: Dead code — `if value <= 0` branch is unreachable in P and X handlers

**File:** `src/gui/controllers/otomatik_kesim_controller.py:616-619, 638-641`

**Issue:** In `_handle_p_frame_click`, `value` is clamped with `value = max(1, min(9999, value))` on line 616. After this clamp `value` is always >= 1. The immediately following `if value <= 0:` branch (line 617) can never be true — it is dead code. The same pattern exists in `_handle_x_frame_click` (lines 638-641). The dead branches create a false impression that a zero/negative value could escape the clamp.

**Fix:** Remove the dead branches. If the intent is to allow clearing the field when the user enters 0, apply the guard *before* the clamp:
```python
value = int(float(value_str)) if value_str else 0
if value <= 0:
    self._p_value = ""
    self.labelPValue.setText("\u2014")
else:
    value = max(1, min(9999, value))
    self._p_value = str(value)
    self.labelPValue.setText(str(value))
self._update_total_label()
```

Note: the same dead-code pattern exists in `_handle_l_frame_click` at line 661, though for L the clamp lower-bound is 1.0 so the same logic applies.

---

### WR-04: `labelCounter` style not reset to white after `_handle_iptal_click` or next START

**File:** `src/gui/controllers/otomatik_kesim_controller.py:900-926, 759-779`

**Issue:** `_on_cutting_complete` sets `labelCounter` style to green (`color: #22C55E`) at line 903. Neither `_handle_iptal_click` (lines 759-779) nor `_handle_start_click` resets this stylesheet back to white (`color: #F4F6FC`). After a completed cut, pressing IPTAL or START again leaves the counter permanently green, making subsequent partial counts visually indistinguishable from a completion state.

**Fix:** Add a style reset in `_handle_iptal_click` (and optionally at the top of `_handle_start_click`):
```python
def _handle_iptal_click(self) -> None:
    ...
    self.labelCounter.setText("0 / 0")
    # Reset counter colour to white
    self.labelCounter.setStyleSheet(
        "background: transparent;"
        " color: #F4F6FC;"
        " font: 80px 'Plus Jakarta Sans';"
        " font-weight: bold;"
    )
    self._previous_count = None
    ...
```

---

## Info

### IN-01: `_l_value` stores `str(float)` but `_validate_params` parses with `float()`

**File:** `src/gui/controllers/otomatik_kesim_controller.py:667, 716`

**Issue:** `_handle_l_frame_click` stores `self._l_value = str(value)` where `value` is a Python `float`, so `_l_value` could be `"100.0"` or even `"1e5"` for large numbers. `_validate_params` calls `float(self._l_value)` which handles this correctly. However there is a subtle inconsistency: after a full 5-digit value like `99999.0`, `str(99999.0)` in Python is `"99999.0"`, but the display label is set to `"99999"` (integer representation). The stored `_l_value` and the displayed value diverge in appearance. This is harmless to correctness but can cause confusion when debugging.

**Suggestion:** Store `_l_value` as the same formatted string shown in the display label:
```python
display = f"{value:.1f}" if value != int(value) else str(int(value))
self._l_value = display   # consistent with what the user sees
self.labelLValue.setText(display)
```

---

### IN-02: Test suite has no coverage for `_on_cutting_complete` style-reset gap

**File:** `tests/test_otomatik_kesim_controller.py`

**Issue:** `test_cutting_complete` (line 164) verifies that `_on_cutting_complete` is called but mocks it out entirely, so the actual body of `_on_cutting_complete` is never exercised by the test suite. In particular, neither the green-style application on `labelCounter` nor the missing style-reset on IPTAL (WR-04 above) would be caught by the current tests.

**Suggestion:** Add a test that calls `_on_cutting_complete` directly and asserts `labelCounter.setStyleSheet` was called with the green colour string, and a follow-up test that calls `_handle_iptal_click` and asserts the counter style is reset.

---

### IN-03: Floating-point equality comparison for display formatting

**File:** `src/gui/controllers/otomatik_kesim_controller.py:666`

**Issue:** `f"{value:.1f}" if value != int(value) else str(int(value))` uses `!=` to compare a `float` to an `int`. While values here are constrained to 1.0–99999.0 rounded to 1 decimal place (so this comparison is safe in practice), floating-point equality is generally fragile and could surprise future maintainers if the rounding strategy changes.

**Suggestion:** Replace with a modulo check:
```python
display = str(int(value)) if value % 1 == 0 else f"{value:.1f}"
```

Or equivalently use `math.isclose(value, round(value), rel_tol=1e-9)`.

---

_Reviewed: 2026-04-09T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
