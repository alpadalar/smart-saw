# Technology Stack — Otomatik Kesim Sayfası (v2.1)

**Project:** Smart Saw Control System
**Milestone:** v2.1 Otomatik Kesim Sayfası
**Researched:** 2026-04-08
**Overall confidence:** HIGH

---

## Executive Summary

The automatic cutting page adds NO new library dependencies. All four capabilities required — Double Word Modbus write, bit-level Modbus operations, hold-delay button patterns, and numeric input validation — are already fully supported by the installed stack (pymodbus 3.5.4, PySide6 6.9.2, stdlib struct).

The work is entirely implementation inside existing modules: extend `MachineControl` with two new register addresses and a `write_registers()` call for the DWORD, and add a `QTimer`-gated confirm pattern for the RESET button. The `NumpadDialog` already handles decimal input but its validation is input-agnostic — a thin wrapper that rejects non-integer or out-of-range values is the only new logic needed.

---

## New Dependencies Required

**None.** requirements.txt is unchanged for this milestone.

Every capability needed is already present:

| Capability | How It Is Already Covered |
|-----------|--------------------------|
| Double Word (32-bit) Modbus write | `pymodbus 3.5.4` — `write_registers([low, high], address)` (FC 16) |
| Bit set/clear on register 20 | `MachineControl._set_bit()` and `_write_register_atomic()` already exist; add new bit constants |
| Read D2056 Word | `AsyncModbusService.read_holding_registers(2056, 1)` already works |
| Hold-delay (confirm-before-fire) button | `QTimer.singleShot()` with `pressed`/`released` signals — standard PySide6 pattern, no new widgets |
| Numeric input with decimal validation | `NumpadDialog` already exists; add an integer-only validation wrapper |
| Cross-thread GUI to asyncio scheduling | `asyncio.run_coroutine_threadsafe()` pattern already in use throughout the project |

---

## Implementation Details for Each Capability

### 1. Double Word Write: L*10 to D2064 (FC 16, write_registers)

pymodbus 3.5.4 exposes `write_registers(address, values)` on both the sync client (`ModbusTcpClient`) and the async client (`AsyncModbusTcpClient`). The method maps to Modbus function code 0x10 (Write Multiple Registers).

**Confirmed API (from installed pymodbus 3.5.4):**
```python
result = client.write_registers(
    address=2064,
    values=[low_word, high_word]  # List[int], each 0-65535
)
```

**Mitsubishi Q-series PLC word order for Double Word:** low word at the base address (D2064), high word at base + 1 (D2065). This matches the project's existing IEEE754 decode pattern in `ModbusReader._decode_ieee754()` which uses `(high_word << 16) | low_word` with `registers[42]` as low and `registers[43]` as high — the same convention.

**Encoding for L*10:**
```python
def encode_dword(value: int) -> list[int]:
    """Encode a 32-bit integer as [low_word, high_word] for Mitsubishi DWORD register."""
    low = value & 0xFFFF
    high = (value >> 16) & 0xFFFF
    return [low, high]

# Usage: L = 1000 mm -> D2064 = 10000 decimal = 0x00002710
# encode_dword(1000 * 10) -> [0x2710, 0x0000]
```

**Where to add this:** Extend `MachineControl` (in `src/services/control/machine_control.py`) with a `write_length()` method using the synchronous `ModbusTcpClient` (same pattern as all existing machine control methods). This is correct because the automatic cutting page, like the positioning page, calls `MachineControl` from the GUI thread without an asyncio bridge.

**MachineControl is the right home** (not `ModbusWriter`/`AsyncModbusService`) because:
- `ModbusWriter` is used only by `MLController` for speed writes during ML cutting cycles
- `MachineControl` owns all register-20 bit operations and all direct PLC commands
- The auto-cutting page will call these methods the same way `PositioningController` calls `machine_control.start_cutting()`

### 2. Bit Operations on Register 20: START (20.13), RESET (20.14), IPTAL (20.4)

The bit operation infrastructure already exists in `MachineControl._set_bit()` and `_write_register_atomic()`. Only new bit constant definitions are needed:

```python
# Add to MachineControl class constants:
AUTO_START_BIT = 13      # 20.13: Start automatic cutting
AUTO_RESET_BIT = 14      # 20.14: Reset automatic sequence
AUTO_IPTAL_BIT = 4       # 20.4:  Cancel / stop (same as CUTTING_STOP_BIT = 4)
```

Note: `AUTO_IPTAL_BIT = 4` is the same physical bit as the existing `CUTTING_STOP_BIT = 4` (20.4 stop cutting). This is expected — IPTAL on the auto page is the same stop signal. No conflict; just use the existing constant or alias it.

**New methods to add to MachineControl:**
```python
def start_auto_cutting(self) -> bool:
    return self._set_bit(self.CONTROL_REGISTER, self.AUTO_START_BIT, True)

def reset_auto_cutting(self) -> bool:
    return self._set_bit(self.CONTROL_REGISTER, self.AUTO_RESET_BIT, True)

def cancel_auto_cutting(self) -> bool:
    return self._set_bit(self.CONTROL_REGISTER, self.CUTTING_STOP_BIT, True)
```

No new pymodbus calls — `_set_bit` performs read-modify-write on a single holding register, identical to how all other bits are set today.

### 3. Reading D2056 (Word): Kesilmis Adet

D2056 is a single 16-bit Word register. `AsyncModbusService.read_holding_registers(2056, 1)` works directly, matching the existing pattern for reading target speed registers (2066, 2041) in `ModbusReader.read_all_sensors()`.

**Integration point:** Add D2056 reading to `ModbusReader` (or read it directly in the new page controller via `AsyncModbusService`). The 10 Hz read cycle in `ModbusReader.read_all_sensors()` is the natural place to add it — append `kesilen_adet_auto` to `RawSensorData`. Alternatively, the auto cutting page controller can poll D2056 independently using `asyncio.run_coroutine_threadsafe` (same threading bridge already used by `ControlPanelController` and `PositioningController`).

The simpler path that avoids model changes: add a dedicated `read_auto_status()` method to `ModbusReader` that reads D2056 on demand, and call it from the GUI page at 1 Hz via a `QTimer`.

### 4. Hold-Delay Pattern for RESET Button (20.14)

The project already has two button interaction patterns:

| Pattern | Where Used | What It Does |
|---------|-----------|--------------|
| Instant press-and-hold (TouchButton) | Positioning page jog buttons | Action fires on press, stops on release |
| Single click | Control panel START/STOP | Action fires immediately on click |

The RESET button needs a third pattern: hold-to-confirm (press and hold for N milliseconds before the PLC command fires). This prevents accidental resets. This pattern is implemented entirely with `QTimer.singleShot()` — no new classes needed.

**Implementation using existing PySide6 QTimer:**
```python
from PySide6.QtCore import QTimer

class AutoCuttingController(QWidget):
    RESET_HOLD_MS = 1500  # Hold 1.5 seconds to confirm reset

    def _setup_reset_button(self):
        self.btnReset.pressed.connect(self._on_reset_pressed)
        self.btnReset.released.connect(self._on_reset_released)
        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(self._execute_reset)

    def _on_reset_pressed(self):
        self._reset_timer.start(self.RESET_HOLD_MS)
        # Optional: show progress indicator

    def _on_reset_released(self):
        self._reset_timer.stop()  # Cancelled if released before timeout
        # Optional: cancel progress indicator

    def _execute_reset(self):
        # Fires only if button held for RESET_HOLD_MS
        asyncio.run_coroutine_threadsafe(
            self._do_reset(), self.event_loop
        )
```

This is pure PySide6 — `QTimer` with `setSingleShot(True)` is well-established for exactly this use case. No third-party library. `QTimer` parent is `self` so Qt handles cleanup automatically.

**Touch support:** The existing `TouchButton` widget emits `touch_pressed`/`touch_released` signals that mirror `pressed`/`released`. If the RESET button needs touchscreen hold-to-confirm, use `TouchButton` instead of `QPushButton` and connect `touch_pressed`/`touch_released` in addition to mouse signals.

### 5. Numeric Input Validation for Parameter Fields

The `NumpadDialog` in `src/gui/numpad.py` already handles:
- Touch-friendly digit entry (0-9, backspace, enter)
- Up to 10-digit string values
- Returns a string from `get_value()`; caller parses

**Current state:** The numpad has no decimal point key — only digit buttons 0-9, backspace, and enter. This is confirmed by direct inspection of `numpad.py`.

**What is needed for the new parameters:**

| Parameter | Type | Range | Input Strategy |
|-----------|------|-------|----------------|
| P (hedef adet) | Integer | >=1 | NumpadDialog as-is, validate int(raw) >= 1 |
| L (uzunluk mm) | Integer | >=1, <=65535 | NumpadDialog as-is, validate range; L*10 fits DWORD easily |
| C (kesim hizi) | Integer | >=40, <=90 | NumpadDialog as-is, same limits as existing speed entry |
| S (inme hizi) | Float (stored as int*100) | >=10, <=60 | Accept integer mm/min; multiply by 100 for register. Fractional precision not operationally needed |
| X (paketteki adet) | Integer | >=1 | NumpadDialog as-is, validate int(raw) >= 1 |

**Recommended approach:** Keep `NumpadDialog` integer-only. For S (inme hizi), accept integer input (consistent with how the existing control panel handles speed entry — the user enters "20" meaning 20.0 mm/min). The existing `write_descent_speed(value)` in `MachineControl` already multiplies by 100 for the register.

**Validation wrapper (no new library, stdlib only):**
```python
def open_integer_input(
    parent, current: int, min_val: int, max_val: int
) -> Optional[int]:
    """Open numpad and return validated integer, or None if cancelled/invalid."""
    dialog = NumpadDialog(parent, initial_value=str(current))
    if dialog.exec() == QDialog.Accepted:
        raw = dialog.get_value()
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
        except ValueError:
            pass
    return None
```

This is 10 lines of stdlib — no new package.

---

## Integration Points with Existing System

| New Component | Integrates With | How |
|---------------|----------------|-----|
| `AutoCuttingController` (new page) | `MainController` | Added as 6th page in `QStackedWidget`; sidebar button in position 2 (after Kontrol Paneli) |
| `AutoCuttingController` | `MachineControl` | Same singleton pattern as `PositioningController` — `self.machine_control = MachineControl()` |
| `MachineControl.write_length(L)` | `ModbusTcpClient.write_registers()` | Calls FC 16 with `[low_word, high_word]` at address 2064 |
| `MachineControl.write_piece_count(n)` | `ModbusTcpClient.write_register()` | FC 06 single write at address 2050 — same as existing `_write_register()` |
| D2056 reading | `AsyncModbusService` | Via `asyncio.run_coroutine_threadsafe()` + 1 Hz `QTimer`, or a new `read_auto_status()` on `ModbusReader` |
| C, S writes | `MachineControl.write_cutting_speed()` / `write_descent_speed()` | Already implemented — the auto page reuses these exact methods |
| IPTAL button | `MachineControl.cancel_auto_cutting()` (equals `stop_cutting()`) | Sets bit 20.4, same as existing stop_cutting |
| START / RESET | New `MachineControl.start_auto_cutting()` / `reset_auto_cutting()` | Sets bits 20.13 / 20.14 using existing `_set_bit()` |

---

## What NOT to Add

| Package | Reason |
|---------|--------|
| Any new pip package | Zero new dependencies required for this milestone |
| `AsyncModbusService` for new page control commands | The auto cutting page uses `MachineControl` (sync client, GUI thread) — same pattern as `PositioningController`. `AsyncModbusService` is for the 10 Hz data collection loop only. |
| `write_coil` / FC 05 | Not needed — the PLC uses holding registers (FC 06/16) for all control, not discrete coils. All existing bit operations use read-modify-write on holding registers. |
| `mask_write_register` (FC 22) | Available in pymodbus 3.5.4 but unsuitable. FC 22 requires PLC support for the Mask Write Register function code. The existing project uses read-modify-write which is proven working with this PLC. |
| New widget classes | `QPushButton` + `QTimer` is sufficient for hold-delay RESET. `TouchButton` already exists if touchscreen hold-confirm is needed. |
| Decimal point in NumpadDialog | Avoid unless fractional descent speed is operationally required — integer mm/min input is consistent with the existing control panel and covers all practical values. |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| pymodbus `write_registers` API | HIGH | Verified from installed pymodbus 3.5.4 via direct `help()` inspection — `write_registers(address, values: List[int])` confirmed |
| Mitsubishi DWORD word order [low, high] | HIGH | Consistent with existing `_decode_ieee754()` in `ModbusReader` which uses the same low/high convention |
| Bit 20.13 / 20.14 via `_set_bit()` | HIGH | `_set_bit()` is proven working for bits 3-10 on register 20; bits 13 and 14 use an identical mechanism |
| `QTimer.setSingleShot(True)` hold-delay | HIGH | Standard Qt pattern; PySide6 6.9.2 installed and confirmed |
| No new dependencies needed | HIGH | Based on direct code inspection of installed packages — all required APIs present |
| Integer-only NumpadDialog for S field | MEDIUM | Operationally acceptable but worth confirming the operator requirement — fractional descent speed may be needed |

---

## Sources

All findings based on direct inspection of installed project code and installed packages:

- `src/services/control/machine_control.py` — existing `_set_bit()`, `_write_register()`, `CONTROL_REGISTER = 20`, sync Modbus from GUI thread pattern
- `src/services/modbus/client.py` — `AsyncModbusService.write_register()` and `read_holding_registers()`, rate-limiting semaphore architecture
- `src/services/modbus/reader.py` — `_decode_ieee754()` confirming low/high word order for multi-register reads; D2066/D2041 polling pattern
- `src/gui/widgets/touch_button.py` — `touch_pressed`/`touch_released` signals for touchscreen hold patterns
- `src/gui/numpad.py` — `NumpadDialog` — integer-only digit buttons, no decimal point key confirmed
- `src/gui/controllers/positioning_controller.py` — `QTimer` + `pressed`/`released` for existing hold-to-jog pattern
- pymodbus 3.5.4 (installed) — `write_registers(address, values: List[int])` confirmed via `help()` introspection
- PySide6 6.9.2 (installed) — `QTimer.singleShot()`, `setSingleShot(True)` confirmed
- `requirements.txt` — current dependency list; no changes needed for v2.1
