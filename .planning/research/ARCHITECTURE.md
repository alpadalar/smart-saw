# Architecture Research: Otomatik Kesim Sayfası Integration

**Domain:** Industrial Saw PLC Control GUI — Automatic/Serial Cutting Page
**Researched:** 2026-04-08
**Confidence:** HIGH (based on direct codebase inspection)
**Milestone:** v2.1 — Otomatik Kesim Sayfası

---

## How the Automatic Cutting Page Integrates

The new page follows the same structural pattern used by all existing pages. There are four integration surfaces to wire: the controller itself, the sidebar registration, the Modbus register operations, and the GUI-to-PLC data flow.

---

## System Overview (Updated)

```
+------------------------------------------------------------------------------+
|                         GUI Thread (Qt Event Loop)                            |
|  +--------------+  +--------------+  +--------------+  +------------------+  |
|  |ControlPanel  |  |OtomatikKesim |  |  Positioning  |  | Sensor / Tracking|  |
|  | Controller   |  | Controller   |  |  Controller   |  | / Camera  Pages  |  |
|  |  (index 0)   |  |  (index 1)   |  |  (index 2)   |  |  (index 3,4,5)   |  |
|  +--------------+  +------+-------+  +--------------+  +------------------+  |
|                           |                                                    |
|                           | QTimers (500ms read D2056)                         |
|                           | MachineControl writes on button actions            |
+---------------------------+----------------------------------------------------+
|                asyncio Event Loop (Main Thread)                                |
|  +-------------------------------------------------------------------------+  |
|  |                  DataProcessingPipeline (10 Hz)                          |  |
|  |  read -> process -> control -> write -> save -> IoT                      |  |
|  +-------------------------------------------------------------------------+  |
|  +----------------------+  +------------------------------------------------+ |
|  | AsyncModbusService   |  |  MachineControl (synchronous, separate client) | |
|  | (async, 10 Hz loop)  |  |  Registers 20 (control bits), 2041, 2066,      | |
|  |                      |  |  D2050, D2056, D2064                           | |
|  +----------------------+  +------------------------------------------------+ |
+------------------------------------------------------------------------------+
```

---

## Component Boundaries

### New Component

| Component | File | Responsibility |
|-----------|------|----------------|
| `OtomatikKesimController` | `src/gui/controllers/otomatik_kesim_controller.py` | New QWidget page: parameter input, START/RESET/IPTAL buttons, real-time kesilmis adet display, speed inputs C and S |

### Modified Components (surgical changes only)

| Component | File | What Changes |
|-----------|------|-------------|
| `MainController` | `src/gui/controllers/main_controller.py` | Insert `OtomatikKesimController` at index 1; shift existing buttons down by one position; add to `closeEvent` `stop_timers()` call |
| `MachineControl` | `src/services/control/machine_control.py` | Add new constants and methods for D2050 write, D2064 Double Word write, D2056 read, and bits 20.13 and 20.14 |

---

## Sidebar Registration: 2nd Position

The current sidebar layout in `main_controller.py` uses fixed geometry slots (y coordinates: 165, 286, 407, 528, 649). Inserting at index 1 (second position) requires shifting all existing buttons and pages.

**Current mapping:**
```
Index 0  y=165  Kontrol Paneli
Index 1  y=286  Konumlandirma
Index 2  y=407  Sensor Verileri
Index 3  y=528  Izleme
Index 4  y=649  Kamera (conditional)
```

**Required mapping after insertion:**
```
Index 0  y=165  Kontrol Paneli       (unchanged)
Index 1  y=286  Otomatik Kesim       (NEW -- takes y=286 slot)
Index 2  y=407  Konumlandirma        (was index 1, now index 2)
Index 3  y=528  Sensor Verileri      (was index 2, now index 3)
Index 4  y=649  Izleme               (was index 3, now index 4)
Index 5  y=770  Kamera (conditional) (was index 4, now index 5)
```

The `nav_buttons` list and `_switch_page()` method use numeric indices -- shifting is a matter of re-ordering the list and updating `stackedWidget.addWidget()` call order. The camera conditional block appends last so it always gets the highest index regardless of how many earlier pages exist.

Existing lambda closures (`lambda: self._switch_page(0)`) hardcode page numbers, so each button's lambda must be updated to reflect the new index.

---

## Modbus Register Operations

All four Modbus operations for the automatic cutting page use `MachineControl` (the synchronous client), consistent with how `PositioningController` handles PLC writes. Do not use `AsyncModbusService` directly from the GUI thread.

### 1. Word Write: D2050 (Hedef Adet = P x X)

D2050 is a standard 16-bit holding register. Use `write_register` (single register):

```python
# In MachineControl
TARGET_ADET_REGISTER = 2050

def write_target_adet(self, p: int, x: int) -> bool:
    """Write P*X to D2050 (Word)."""
    value = p * x
    if not (0 <= value <= 65535):
        logger.error(f"Target adet out of range: {value}")
        return False
    return self._write_register(self.TARGET_ADET_REGISTER, value)
```

### 2. Double Word Write: D2064 (Hedef Uzunluk = L x 10)

D2064 is a 32-bit Double Word stored in two consecutive 16-bit registers: D2064 (low word) and D2065 (high word). `pymodbus`'s `write_registers` (plural) handles multi-register writes. Both `AsyncModbusTcpClient` and synchronous `ModbusTcpClient` expose this method -- confirmed via runtime introspection.

Word order convention: Mitsubishi FX-series PLCs typically store Double Words as low word at the base address (D2064 = low 16 bits, D2065 = high 16 bits). Verify with actual PLC documentation before shipping -- this is flagged as an open question below.

```python
# In MachineControl
TARGET_UZUNLUK_REGISTER = 2064  # Low word; D2065 = high word (verify order)

def write_target_uzunluk(self, l_mm: float) -> bool:
    """Write L*10 to D2064/D2065 as 32-bit Double Word."""
    value = int(l_mm * 10)
    if not (0 <= value <= 0xFFFFFFFF):
        logger.error(f"Target uzunluk out of range: {value}")
        return False

    low_word = value & 0xFFFF
    high_word = (value >> 16) & 0xFFFF

    try:
        if not self._ensure_connected():
            return False
        result = self.client.write_registers(
            address=self.TARGET_UZUNLUK_REGISTER,
            values=[low_word, high_word]  # VERIFY word order with PLC docs
        )
        if result.isError():
            logger.error(
                f"Double word write error at {self.TARGET_UZUNLUK_REGISTER}: {result}"
            )
            return False
        logger.info(
            f"Target uzunluk written: {l_mm}mm -> {value} "
            f"(low={low_word:#06x}, high={high_word:#06x})"
        )
        return True
    except Exception as e:
        logger.error(f"Double word write exception: {e}")
        return False
```

### 3. Word Read: D2056 (Kesilmis Adet -- real-time)

D2056 is a standard 16-bit holding register. Use `read_holding_registers` with count=1 via the existing `_read_register` helper:

```python
# In MachineControl
KESILMIS_ADET_REGISTER = 2056

def read_kesilmis_adet(self) -> Optional[int]:
    """Read current cut count from D2056 (Word). Returns None on error."""
    return self._read_register(self.KESILMIS_ADET_REGISTER)
```

### 4. Bit Operations on Register 20 (Control Bits)

Register 20 is the existing `CONTROL_REGISTER` in `MachineControl`. The new bits slot alongside existing bits without conflict:

| Bit | Function | Status |
|-----|----------|--------|
| 20.3 | Cutting start | existing (`CUTTING_START_BIT`) |
| 20.4 | Cutting stop / IPTAL | existing (`CUTTING_STOP_BIT`) -- reused |
| 20.5 | Rear vise open | existing |
| 20.6 | Front vise open | existing |
| 20.7 | Material forward | existing |
| 20.8 | Material backward | existing |
| 20.9 | Saw up | existing |
| 20.10 | Saw down | existing |
| 20.13 | AUTO START | NEW |
| 20.14 | AUTO RESET (hold-delay) | NEW |

20.4 (IPTAL) is already `CUTTING_STOP_BIT`. The new page reuses it -- no new constant needed for IPTAL, just call the existing `cancel_cutting()` or `_set_bit(CONTROL_REGISTER, CUTTING_STOP_BIT, True)` directly.

```python
# In MachineControl -- add to existing constants block
AUTO_START_BIT = 13    # 20.13: Automatic cutting start
AUTO_RESET_BIT = 14    # 20.14: Automatic cutting reset (hold-delay)

def start_auto_cutting(self) -> bool:
    """Set bit 20.13 to initiate automatic cutting."""
    return self._set_bit(self.CONTROL_REGISTER, self.AUTO_START_BIT, True)

def stop_auto_cutting(self) -> bool:
    """Clear bit 20.13."""
    return self._set_bit(self.CONTROL_REGISTER, self.AUTO_START_BIT, False)

def reset_auto_cutting(self, activate: bool) -> bool:
    """Set/clear bit 20.14 for reset (hold-delay: high while button held)."""
    return self._set_bit(self.CONTROL_REGISTER, self.AUTO_RESET_BIT, activate)

def cancel_auto_cutting(self) -> bool:
    """Set bit 20.4 (reuses existing CUTTING_STOP_BIT)."""
    return self._set_bit(self.CONTROL_REGISTER, self.CUTTING_STOP_BIT, True)
```

---

## Data Flow: GUI Inputs to PLC Registers

```
Operator Input (NumpadDialog touch)
    P (hedef adet)  --+
    X (paketteki)   --+--> P * X  --> MachineControl.write_target_adet()
                                              |
                                         D2050 (Word) -- PLC total target count

    L (uzunluk mm)  -------> L * 10  --> MachineControl.write_target_uzunluk()
                                              |
                                     D2064/D2065 (Double Word) -- target length

    C (kesim hizi)  -------> MachineControl.set_cutting_speed()
                                              |
                                         D2066 (existing -- shared with manual page)

    S (inme hizi)   -------> MachineControl.set_descent_speed() [value * 100]
                                              |
                                         D2041 (existing -- shared with manual page)

QTimer (500ms, Qt thread)
    --> MachineControl.read_kesilmis_adet()
              |
         D2056 (Word read)
              |
         labelKesilmisAdet.setText(str(count))

Button: START
    --> MachineControl.start_auto_cutting()   [bit 20.13 set]

Button: RESET (TouchButton, hold-delay)
    pressed  --> MachineControl.reset_auto_cutting(True)   [bit 20.14 high]
    released --> MachineControl.reset_auto_cutting(False)  [bit 20.14 low]

Button: IPTAL
    --> MachineControl.cancel_auto_cutting()  [bit 20.4 set -- existing constant]
```

### Shared Registers with ControlPanelController

C (kesim hizi) and S (inme hizi) write to D2066 and D2041 respectively -- the same physical registers as the manual cutting page. Both pages write to identical addresses. The PLC holds whichever was written last. No arbitration is needed; the requirement explicitly states these are shared.

---

## Patterns to Follow

### Pattern 1: MachineControl for GUI-Initiated Writes

`ControlPanelController` and `PositioningController` both use `MachineControl` (synchronous `ModbusTcpClient`) for direct button-to-PLC writes. They do NOT use `asyncio.run_coroutine_threadsafe()` for these writes. The synchronous client manages its own connection and cooldown. `OtomatikKesimController` follows the same pattern exactly.

```python
class OtomatikKesimController(QWidget):
    def __init__(self, control_manager=None, data_pipeline=None, parent=None):
        super().__init__(parent)
        self.control_manager = control_manager
        self.data_pipeline = data_pipeline
        self.machine_control: Optional[MachineControl] = None
        self._initialize_machine_control()
        self._setup_ui()
        self._setup_timers()

    def _initialize_machine_control(self) -> None:
        try:
            self.machine_control = MachineControl()  # singleton
            if not self.machine_control.is_connected:
                logger.warning("MachineControl initialized but not connected")
        except Exception as e:
            logger.error(f"MachineControl initialization error: {e}")
            self.machine_control = None
```

### Pattern 2: NumpadDialog for Parameter Input

`ControlPanelController` uses `NumpadDialog` for speed input. The same dialog handles P, L, C, S, X on the automatic cutting page. Import path: `from ..numpad import NumpadDialog`.

```python
def _open_numpad_for(self, field: str):
    dlg = NumpadDialog(parent=self)
    if dlg.exec() == QDialog.Accepted:
        raw = dlg.get_value()
        if raw:
            self._params[field] = int(raw)
            self._update_display(field)
```

### Pattern 3: QTimer for Periodic Register Read

`PositioningController` uses a 300ms QTimer to poll PLC feedback bits. The automatic cutting page uses 500ms to read D2056 -- consistent with the polling cadence.

```python
def _setup_timers(self):
    self._adet_timer = QTimer(self)
    self._adet_timer.timeout.connect(self._update_kesilmis_adet)
    self._adet_timer.start(500)

def _update_kesilmis_adet(self):
    if self.machine_control and self.machine_control.is_connected:
        count = self.machine_control.read_kesilmis_adet()
        if count is not None:
            self.labelKesilmisAdet.setText(str(count))
```

### Pattern 4: TouchButton for RESET Hold-Delay

RESET (20.14) uses `TouchButton` from `src/gui/widgets/touch_button.py`. Wire all four signals as `PositioningController` does:

```python
self.btnReset = TouchButton(self)
self.btnReset.pressed.connect(
    lambda: self._on_reset_button(True)
)
self.btnReset.released.connect(
    lambda: self._on_reset_button(False)
)
self.btnReset.touch_pressed.connect(
    lambda: self._on_reset_button(True)
)
self.btnReset.touch_released.connect(
    lambda: self._on_reset_button(False)
)

def _on_reset_button(self, is_pressed: bool) -> None:
    if self.machine_control:
        self.machine_control.reset_auto_cutting(is_pressed)
    self.btnReset.setChecked(is_pressed)
```

### Pattern 5: stop_timers() for Qt Lifecycle

Every page controller that creates QTimers must implement `stop_timers()`. `MainController.closeEvent()` calls it on all page controllers.

```python
def stop_timers(self):
    if hasattr(self, '_adet_timer') and self._adet_timer:
        self._adet_timer.stop()
    logger.debug("OtomatikKesimController timers stopped")
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Using asyncio.run_coroutine_threadsafe for MachineControl Calls

`ControlPanelController` uses `asyncio.run_coroutine_threadsafe()` only when delegating to `control_manager.manual_set_speeds()` because `ControlManager` is an async service. `MachineControl` is synchronous -- calling it from the Qt thread directly is correct and intentional. Do not wrap `MachineControl` calls in `run_coroutine_threadsafe`.

### Anti-Pattern 2: Writing C/S via AsyncModbusService

`AsyncModbusService` lives in the asyncio event loop thread. Calling it from the Qt GUI thread without `run_coroutine_threadsafe` causes race conditions. Use `MachineControl` for all GUI-thread Modbus writes including C and S speeds.

### Anti-Pattern 3: Forgetting stop_timers in closeEvent

`MainController.closeEvent()` iterates a hardcoded list of pages to call `stop_timers()`. The `otomatik_kesim_page` must be added to this explicit list, not handled via a loose `hasattr` check.

### Anti-Pattern 4: Assuming Double Word Word Order

Do not assume big-endian or little-endian word order for D2064/D2065 without verifying against the actual PLC documentation. The existing `_decode_ieee754` uses `(high_word << 16) | low_word` for IEEE 754 floats -- Double Word integer layout on a Mitsubishi PLC may differ. Verify before first integration test.

---

## Build Order

### Step 1: Extend MachineControl

**File:** `src/services/control/machine_control.py`

Add constants and methods:
- `TARGET_ADET_REGISTER = 2050`
- `TARGET_UZUNLUK_REGISTER = 2064`
- `KESILMIS_ADET_REGISTER = 2056`
- `AUTO_START_BIT = 13`
- `AUTO_RESET_BIT = 14`
- `write_target_adet(p, x) -> bool`
- `write_target_uzunluk(l_mm) -> bool` (uses `client.write_registers` for Double Word)
- `read_kesilmis_adet() -> Optional[int]`
- `start_auto_cutting() -> bool`
- `stop_auto_cutting() -> bool`
- `reset_auto_cutting(activate: bool) -> bool`
- `cancel_auto_cutting() -> bool` (delegates to existing `CUTTING_STOP_BIT`)

All additive changes. Zero modifications to existing methods.

**Why first:** `OtomatikKesimController` depends on these. Testable with a Modbus simulator before the UI exists. Unit-test value encoding (P*X range check, L*10 double-word split).

### Step 2: OtomatikKesimController

**File:** `src/gui/controllers/otomatik_kesim_controller.py`

New `QWidget` following `PositioningController` as the structural template:
- `__init__` signature matches existing pages: `(self, control_manager=None, data_pipeline=None, parent=None)`
- `_initialize_machine_control()` -- identical to `PositioningController`
- `_setup_ui()` -- parameter fields (P, L, C, S, X via NumpadDialog), START/RESET/IPTAL buttons, kesilmis adet display label
- `_setup_timers()` -- 500ms QTimer for D2056
- `stop_timers()` -- required
- `update_data(data)` -- can be no-op or update C/S display from pipeline ProcessedData

**Dependencies:** Step 1, `NumpadDialog` (existing), `TouchButton` (existing).

### Step 3: MainController Integration

**File:** `src/gui/controllers/main_controller.py`

Changes (in order):
1. Add import: `from .otomatik_kesim_controller import OtomatikKesimController`
2. In `_setup_ui()`: create `self.otomatik_kesim_page` after `self.control_panel_page`
3. Update `stackedWidget.addWidget()` calls: otomatik_kesim at index 1, shift all others up by one
4. Shift sidebar button y-coordinates: `btnPositioning` y=407, `btnSensor` y=528, `btnTracking` y=649, camera y=770
5. Update all `lambda: self._switch_page(N)` closures with new indices
6. Update `nav_buttons` list order to include `btnOtomatikKesim` at position 1
7. Add `self.otomatik_kesim_page` to the `closeEvent` stop loop

**Why last:** Pure assembly. All components exist; this step only wires them together.

---

## Integration Points Summary

### New vs Modified

| Component | File | Status |
|-----------|------|--------|
| OtomatikKesimController | `src/gui/controllers/otomatik_kesim_controller.py` | NEW |
| MachineControl | `src/services/control/machine_control.py` | MODIFIED -- additive only |
| MainController | `src/gui/controllers/main_controller.py` | MODIFIED -- re-index + insert |

### Unchanged (explicitly)

`AsyncModbusService`, `ControlManager`, `DataProcessingPipeline`, `ModbusReader`, `ModbusWriter`, all database schemas, all IoT/MQTT code, and the entire camera subsystem are not touched by this feature.

---

## Open Questions (Research Flags)

1. **D2064 word order (HIGH priority -- must verify before integration test):** Confirm whether Mitsubishi PLC stores Double Word with low word at D2064 or high word at D2064. Affects `write_registers([low_word, high_word])` vs `write_registers([high_word, low_word])`.

2. **START bit latch behavior (MEDIUM):** Confirm whether 20.13 must be explicitly cleared by the GUI after the PLC acknowledges, or whether the PLC self-latches. Jog bits (20.7-20.10) require explicit release. Auto-start behavior may differ.

3. **RESET hold minimum duration (LOW):** Confirm whether the PLC expects a minimum hold time on 20.14 or accepts a simple bit-high-while-pressed pattern. `TouchButton` supports both.

---

## Sources

- `src/gui/controllers/main_controller.py` -- sidebar geometry, page index pattern, closeEvent pattern -- direct inspection, HIGH confidence
- `src/gui/controllers/positioning_controller.py` -- MachineControl singleton init, QTimer polling, TouchButton wiring -- direct inspection, HIGH confidence
- `src/gui/controllers/control_panel_controller.py` -- NumpadDialog usage, asyncio.run_coroutine_threadsafe vs direct MachineControl distinction -- direct inspection, HIGH confidence
- `src/services/control/machine_control.py` -- existing register constants (CONTROL_REGISTER=20, 2041, 2066), `_set_bit()`, `_write_register()`, `_write_register_atomic()` -- direct inspection, HIGH confidence
- `src/services/modbus/client.py` -- `write_registers` not present in AsyncModbusService but confirmed available in underlying pymodbus client; runtime check confirmed `write_registers` on `AsyncModbusTcpClient` -- direct inspection + runtime check, HIGH confidence
- `src/gui/widgets/touch_button.py` -- hold-delay pattern via `touch_pressed`/`touch_released` signals -- direct inspection, HIGH confidence
- `.planning/PROJECT.md` -- v2.1 register spec: D2050, D2064, D2056, bits 20.13/20.14/20.4 -- project spec, HIGH confidence

---

*Architecture research for: Smart Saw v2.1 Otomatik Kesim Sayfası*
*Researched: 2026-04-08*
