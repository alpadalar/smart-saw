---
phase: 25-machinecontrol-extension
reviewed: 2026-04-09T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - tests/test_machine_control_auto_cutting.py
  - src/services/control/machine_control.py
findings:
  critical: 0
  warning: 4
  info: 2
  total: 6
status: issues_found
---

# Phase 25: Code Review Report

**Reviewed:** 2026-04-09
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Two files were reviewed: the new `MachineControl` auto cutting methods in
`machine_control.py` and the companion unit tests in
`test_machine_control_auto_cutting.py`.

The new auto cutting methods (`_write_double_word`, `write_target_adet`,
`write_target_uzunluk`, `read_kesilmis_adet`, `start_auto_cutting`,
`reset_auto_cutting`, `cancel_auto_cutting`) are structurally consistent with
the existing module patterns. The tests correctly patch the Modbus client at the
right import path and cover the primary happy-path and disconnected-client
scenarios.

Four warnings were found. The most impactful is a semantic bug in the
pre-existing `get_control_register_status()` method: it reads `CHIP_CLEANING_BIT`
(value 3) from `CONTROL_REGISTER` (20), but chip cleaning lives on a different
physical register (102). Bit 3 of register 20 is the cutting-start bit, so the
`chip_cleaning` key in the returned dict actually reflects cutting state — a
silent data-integrity issue that worsens now that more callers may rely on the
status dict. Two additional warnings cover missing input guards on the new write
methods, and one covers misleading log output in `__init__`. Two info items
flag the missing auto-cutting keys in the status dict and a gap in test coverage.

---

## Warnings

### WR-01: `get_control_register_status` reads chip-cleaning bit from the wrong register

**File:** `src/services/control/machine_control.py:651`

**Issue:** `get_control_register_status()` reads `self.CHIP_CLEANING_BIT` (= 3)
from `CONTROL_REGISTER` (= 20). However, chip cleaning is controlled via
`KONVEYOR_REGISTER` (= 102). Bit 3 of register 20 is `CUTTING_START_BIT`.
Therefore the dict key `'chip_cleaning'` actually reflects the cutting-start
bit, while the cutting-start bit is also separately reported as
`'cutting_start'` — both read from the same physical bit. Any caller that
relies on `'chip_cleaning'` from this dict gets wrong data.

**Fix:** Either read register 102 separately for the chip-cleaning key, or
remove the `chip_cleaning` key from this dict (it covers only register 20):

```python
def get_control_register_status(self) -> Optional[dict]:
    """Get all bit statuses from control register (register 20 only)."""
    try:
        current_value = self._read_register(self.CONTROL_REGISTER)
        if current_value is None:
            return None

        return {
            # Removed: 'chip_cleaning' — lives on KONVEYOR_REGISTER (102), not here
            'cutting_start':    bool((current_value >> self.CUTTING_START_BIT)    & 1),
            'cutting_stop':     bool((current_value >> self.CUTTING_STOP_BIT)     & 1),
            'rear_vise_open':   bool((current_value >> self.REAR_VISE_OPEN_BIT)   & 1),
            'front_vise_open':  bool((current_value >> self.FRONT_VISE_OPEN_BIT)  & 1),
            'material_forward': bool((current_value >> self.MATERIAL_FORWARD_BIT) & 1),
            'material_backward':bool((current_value >> self.MATERIAL_BACKWARD_BIT)& 1),
            'saw_up':           bool((current_value >> self.SAW_UP_BIT)           & 1),
            'saw_down':         bool((current_value >> self.SAW_DOWN_BIT)         & 1),
            'auto_cutting_start': bool((current_value >> self.AUTO_CUTTING_START_BIT) & 1),
            'auto_cutting_reset': bool((current_value >> self.AUTO_CUTTING_RESET_BIT) & 1),
        }
    except Exception as e:
        logger.error(f"Control register status error: {e}")
        return None
```

---

### WR-02: `write_target_adet` does not guard against 16-bit overflow

**File:** `src/services/control/machine_control.py:546`

**Issue:** `p * x` is written directly to a single Modbus register (FC6), which
is a 16-bit field (max 65535). There is no validation that the product fits. For
example `write_target_adet(1000, 100)` computes 100 000, which silently
overflows the register. pymodbus may raise or silently truncate; either way the
PLC receives the wrong target count with no error returned to the caller.

**Fix:** Add an overflow guard and return `False` with a log:

```python
def write_target_adet(self, p: int, x: int) -> bool:
    try:
        value = int(p) * int(x)
        if not (0 <= value <= 0xFFFF):
            logger.error(
                f"write_target_adet: computed value {value} out of 16-bit range "
                f"(P={p}, X={x})"
            )
            return False
        ...
```

---

### WR-03: `write_target_uzunluk` does not guard against negative input

**File:** `src/services/control/machine_control.py:573`

**Issue:** A negative `l_mm` value (e.g., `-10.0`) produces a negative integer
after `int(round(l_mm * 10))`. When `_write_double_word` splits this into
`low_word = value & 0xFFFF` and `high_word = (value >> 16) & 0xFFFF`, Python's
arbitrary-precision integers encode the two's-complement bit pattern of a
large positive number. The PLC receives a nonsensical distance value with no
error signalled to the caller.

**Fix:** Validate before scaling:

```python
def write_target_uzunluk(self, l_mm: float) -> bool:
    try:
        if l_mm < 0:
            logger.error(f"write_target_uzunluk: negative length {l_mm}mm is invalid")
            return False
        value = int(round(l_mm * 10))
        ...
```

---

### WR-04: `__init__` logs stale `host`/`port` parameter values instead of resolved values

**File:** `src/services/control/machine_control.py:112-114`

**Issue:** After resolving `self.host` and `self.port` from config (when the
caller passes `None`), the log messages on lines 112 and 114 reference the raw
`host` and `port` parameters, not `self.host`/`self.port`. When `MachineControl()` is
called without arguments, both parameters are `None`, so the log prints
`"connected to None:None"` rather than the actual host and port.

```
# Current (misleading when host/port not passed):
logger.info(f"MachineControl connected to {host}:{port}")
logger.warning(f"MachineControl failed to connect to {host}:{port}")
```

**Fix:**

```python
logger.info(f"MachineControl connected to {self.host}:{self.port}")
# ...
logger.warning(f"MachineControl failed to connect to {self.host}:{self.port}")
```

---

## Info

### IN-01: `get_control_register_status` omits the new auto-cutting bits added in phase 25

**File:** `src/services/control/machine_control.py:650-659`

**Issue:** The status dict returned by `get_control_register_status()` does not
include `auto_cutting_start` (bit 13) or `auto_cutting_reset` (bit 14), which
were added in this phase. Any downstream diagnostic or UI code that calls this
method to inspect machine state will silently miss the new bits. This is an
omission rather than a correctness bug (the fix is shown in WR-01 above where
both bits are included).

**Fix:** See WR-01 fix — add both `auto_cutting_start` and `auto_cutting_reset`
keys to the returned dict.

---

### IN-02: Test suite has no boundary/overflow coverage for `write_target_adet` and `write_target_uzunluk`

**File:** `tests/test_machine_control_auto_cutting.py`

**Issue:** The tests cover the nominal case (small valid values) but do not test
the boundary conditions flagged in WR-02 and WR-03: values that overflow a
16-bit register, or negative lengths. Once the guards described in WR-02/WR-03
are added, these cases will need tests to prevent regression.

**Fix:** After adding guards, add tests such as:

```python
def test_write_target_adet_overflow_returns_false(mock_client_class):
    _make_connected_mc(mock_client_class)
    mc = MachineControl()
    result = mc.write_target_adet(1000, 1000)  # 1_000_000 > 65535
    assert result is False

def test_write_target_uzunluk_negative_returns_false(mock_client_class):
    _make_connected_mc(mock_client_class)
    mc = MachineControl()
    result = mc.write_target_uzunluk(-1.0)
    assert result is False
```

---

_Reviewed: 2026-04-09_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
