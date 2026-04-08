---
phase: 25-machinecontrol-extension
plan: 01
subsystem: machine_control
tags: [modbus, plc, auto-cutting, tdd, fc16, double-word]
dependency_graph:
  requires: []
  provides: [MachineControl.write_target_adet, MachineControl.write_target_uzunluk, MachineControl.read_kesilmis_adet, MachineControl.start_auto_cutting, MachineControl.reset_auto_cutting, MachineControl.cancel_auto_cutting]
  affects: [src/services/control/machine_control.py]
tech_stack:
  added: []
  patterns: [TDD RED-GREEN-REFACTOR, FC16-double-word-low-word-first, singleton-pattern]
key_files:
  created:
    - tests/test_machine_control_auto_cutting.py
  modified:
    - src/services/control/machine_control.py
decisions:
  - "_write_double_word uses FC16 write_registers([low, high]) for atomic Mitsubishi low-word-first double write"
  - "int(round(l_mm * 10)) eliminates IEEE 754 float drift in write_target_uzunluk (T-25-02 mitigation)"
  - "cancel_auto_cutting reuses CUTTING_STOP_BIT=4 per D-01: single PLC stop/cancel bit for both modes"
metrics:
  duration: "~3 minutes"
  completed: "2026-04-09"
  tasks_completed: 3
  files_changed: 2
---

# Phase 25 Plan 01: MachineControl Auto Cutting Extension Summary

## One-liner

MachineControl singleton extended with Auto Cutting Control section: FC16 double-word write helper, 6 public PLC methods (D2050/D2056/D2064), and 11 unit tests validating all 7 PLC/CTRL requirements.

## What Was Built

Added a complete "Auto Cutting Control (Otomatik Kesim)" section to `MachineControl` providing the PLC communication foundation for Phase 26 (OtomatikKesimController GUI layer).

### Register and Bit Constants Added

| Constant | Value | Purpose |
|----------|-------|---------|
| TARGET_ADET_REGISTER | 2050 | D2050: Hedef adet (P*X) |
| TARGET_LENGTH_REGISTER | 2064 | D2064: Hedef uzunluk (Double Word low word) |
| CUT_COUNT_REGISTER | 2056 | D2056: Kesilmis adet |
| AUTO_CUTTING_START_BIT | 13 | 20.13: Auto cutting start |
| AUTO_CUTTING_RESET_BIT | 14 | 20.14: Auto cutting reset |

### Methods Added

| Method | Requirement | PLC Operation |
|--------|-------------|---------------|
| `_write_double_word(register, value)` | PLC-04 | FC16 write_registers([low, high]) |
| `write_target_adet(p, x)` | PLC-01 | FC6 write_register to D2050 with P*X |
| `write_target_uzunluk(l_mm)` | PLC-02 | FC16 to D2064/D2065 with int(round(l_mm*10)) |
| `read_kesilmis_adet()` | PLC-03 | read_holding_registers from D2056 |
| `start_auto_cutting()` | CTRL-01 | _set_bit(20, 13, True) fire-and-forget |
| `reset_auto_cutting(active)` | CTRL-02 | _set_bit(20, 14, active) hold/release |
| `cancel_auto_cutting()` | CTRL-03 | _set_bit(20, CUTTING_STOP_BIT=4, True) |

## Test Coverage

11 unit tests in `tests/test_machine_control_auto_cutting.py`:

- `test_write_double_word_fc16`: verifies FC16 call with [0x2710, 0x0000] for value=10000
- `test_write_double_word_large_value`: verifies [0x4240, 0x000F] for value=1000000
- `test_write_target_adet`: P=5, X=10 → write_register(2050, 50)
- `test_write_target_uzunluk_word_order`: L=1000mm → D2064=0x2710, D2065=0x0000 (SUCCESS CRITERION 5)
- `test_write_target_uzunluk_float_rounding`: 100.3*10=1003 not 1002 (IEEE 754 guard)
- `test_read_kesilmis_adet`: read_holding_registers(2056, count=1) returns value
- `test_read_kesilmis_adet_disconnected`: returns None on connection failure
- `test_start_auto_cutting`: write_register(20, 0x2000) (bit 13)
- `test_reset_auto_cutting_active`: write_register(20, 0x4000) (bit 14 set)
- `test_reset_auto_cutting_release`: write_register(20, 0x0000) (bit 14 cleared from 0x4000)
- `test_cancel_auto_cutting`: write_register(20, 0x0010) (bit 4)

## Verification Results

| Check | Result |
|-------|--------|
| `python -m pytest tests/test_machine_control_auto_cutting.py -v` | 11/11 PASSED |
| `python -m pytest tests/ -q` | 69/69 PASSED (0 regressions) |
| `ruff check machine_control.py` | 0 errors |
| `ruff check test_machine_control_auto_cutting.py` | 0 errors |
| Section order: Speed Control → Auto Cutting → Status Methods | Confirmed (lines 421→482→640) |
| Success criterion 5: D2064=0x2710, D2065=0x0000 for L=1000mm | Confirmed by test |

## Commits

| Hash | Task | Description |
|------|------|-------------|
| af8cd39 | Task 1 (RED) | Failing test suite (11 tests, all RED) |
| 1c6f7ae | Task 2 (GREEN) | Auto Cutting Control section implementation |
| 6a3ccc1 | Task 3 (REFACTOR) | Verification: ruff clean, 69/69 tests pass |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all methods fully implemented with real Modbus calls.

## Threat Surface Scan

No new network endpoints, auth paths, or trust boundary changes introduced. All mitigations from threat register applied:

- **T-25-02 (mitigate):** `int(round(l_mm * 10))` implemented — IEEE 754 drift eliminated, verified by `test_write_target_uzunluk_float_rounding`.
- **T-25-03 (mitigate):** `_ensure_connected()` checked before FC16 write, `result.isError()` checked after — verified in `_write_double_word` implementation.

## Self-Check: PASSED
