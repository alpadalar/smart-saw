# Pitfalls Research

**Domain:** Adding automatic/serial cutting GUI page with PLC bit operations and Double Word Modbus writes to an existing industrial saw control system
**Researched:** 2026-04-08
**Confidence:** HIGH (codebase verified; Modbus byte-order and pymodbus patterns verified via official docs and community sources; existing patterns in MachineControl and AsyncModbusService confirmed by direct code review)

---

## Critical Pitfalls

Mistakes that cause incorrect PLC commands, wrong values written to the PLC, or safety failures.

---

### Pitfall 1: Wrong Word Order When Writing D2064 as a Double Word (32-bit)

**What goes wrong:**
`L×10` is a 32-bit value that must be written to D2064 and D2065 (two consecutive 16-bit Modbus holding registers). If the developer calls `write_register(2064, value)` with a 16-bit-clamped value instead of `write_registers`, or uses `BinaryPayloadBuilder` with the wrong `wordorder`, the PLC receives a silently incorrect length value. For example, with `wordorder=Endian.LITTLE` instead of `Endian.BIG`, a value of `15000` (L=1500.0mm × 10) written as `[0x3A98, 0x0000]` arrives at the PLC as `0x00003A98` which happens to match — but `500000` (L=50000mm × 10) written as `[0x86A0, 0x0007]` arrives as `0x000786A0` = 501,408 instead of 500,000. The error is not constant; it depends on the magnitude of the value and will only be caught during real-machine testing with large lengths.

**Why it happens:**
The Modbus standard defines 16-bit register byte order (big-endian) but says nothing about how two 16-bit registers form a 32-bit value. Mitsubishi PLCs store DDWORD values with the **low word at the lower address** (D2064 = low 16 bits, D2065 = high 16 bits). `pymodbus` `BinaryPayloadBuilder` defaults to `wordorder=Endian.BIG` which puts the high word first. The two conventions are opposite. Community sources (plctalk.net Modbus DWORD thread) confirm this is the most common integration mistake with Mitsubishi PLCs. The existing codebase uses only `write_register` (single 16-bit) — there is no existing 32-bit write pattern to follow.

**Consequences:**
Operator enters a target length of 1200mm. PLC receives a garbled value and runs the automatic cutting cycle to the wrong length. No error is raised — the write succeeds, the PLC just acts on the wrong data. This is a safety issue in an industrial cutting context.

**Prevention:**
Use `struct.pack` directly to split the 32-bit value into two 16-bit registers and manually verify the byte order against the PLC manual before writing. Prefer explicit struct-based splitting over `BinaryPayloadBuilder` because the intent is visible in code:

```python
import struct

def split_dword_for_mitsubishi(value_32bit: int) -> list[int]:
    """
    Split 32-bit int into [low_word, high_word] for Mitsubishi D register.
    Mitsubishi: lower D address = low 16 bits, upper D address = high 16 bits.
    """
    low_word = value_32bit & 0xFFFF
    high_word = (value_32bit >> 16) & 0xFFFF
    return [low_word, high_word]

# D2064 = low word, D2065 = high word
registers = split_dword_for_mitsubishi(length_mm * 10)
await modbus_client.write_registers(address=2064, values=registers)
```

Verify with a known round-number value (e.g., L=1000mm → 10000 = 0x00002710, registers = [0x2710, 0x0000]) against PLC monitoring software before any integration test.

**Detection:**
- PLC-side monitoring: check D2064 and D2065 independently after a write
- Write 65536 (0x00010000) — if D2064 = 0 and D2065 = 1, word order is correct for Mitsubishi
- Write 1 (0x00000001) — if D2064 = 1 and D2065 = 0, word order is correct for Mitsubishi

**Phase to address:** Phase that adds the PLC write logic for L parameter. Must be verified with actual PLC hardware before the GUI phase builds on top of it.

---

### Pitfall 2: `AsyncModbusService` Does Not Have `write_registers` — Only `write_register`

**What goes wrong:**
The existing `AsyncModbusService.write_register()` writes exactly one 16-bit register using function code 6 (Write Single Register). Writing a Double Word to D2064+D2065 requires writing two registers atomically using function code 16 (Write Multiple Registers), which uses `write_registers` (plural). If the developer calls `write_register` twice — once for address 2064, once for 2065 — there is a window between the two writes where the PLC sees a half-updated 32-bit value. If the PLC samples D2064/D2065 between the two writes (e.g., during its scan cycle), it receives a corrupted intermediate value. The `asyncio.sleep(0.11)` inter-write delay pattern in `ModbusWriter.write_speeds()` does not help here — it makes the window larger, not smaller.

**Why it happens:**
The developer looks at the existing Modbus write path, sees `write_register`, and uses it twice. `write_registers` (function code 16) is not present in the current codebase at all. The method must be added to `AsyncModbusService`.

**Consequences:**
In a serial cutting cycle, the PLC reads D2064/D2065 immediately after receiving a START command. If a double-write was in progress (two single writes), the PLC gets low_word=new, high_word=old — a spurious length that could cause the cutting cycle to run until an overtravel fault.

**Prevention:**
Add `write_registers(address, values)` to `AsyncModbusService` using `self._client.write_registers(address=address, values=values)` (pymodbus function code 16). Write D2064+D2065 in a single call. Never use two sequential `write_register` calls for a Double Word.

**Detection:**
- Code review: grep for `write_register(2064` or `write_register(2065` — both must be absent, replaced by a single `write_registers(2064, [low, high])`

**Phase to address:** Modbus infrastructure phase. Add `write_registers` to `AsyncModbusService` before any Double Word write logic is implemented.

---

### Pitfall 3: Bit Read-Modify-Write Race Condition on Register 20 Between MachineControl and the New Auto Page

**What goes wrong:**
`MachineControl._set_bit()` uses a synchronous read-modify-write pattern: read register 20, flip the target bit, write it back. The new auto page will use the same register 20 for bits 20.13 (START) and 20.14 (RESET). The existing control panel uses the same register for bits 20.3 (cutting start) and 20.4 (cutting stop). If the GUI thread (via MachineControl synchronous client) and the asyncio thread (via the new async write path) both attempt bit operations on register 20 concurrently, the second write overwrites the first's modification:

```
Thread A reads:  0b...0000100000001000  (bit 3 set)
Thread B reads:  0b...0000100000001000  (same state)
Thread A writes: 0b...0000100000001000 | bit 13 = 0b...0010100000001000  
Thread B writes: 0b...0000100000001000 | bit 14 = 0b...0001000000001000  ← erases Thread A's bit 13
```

The START bit (20.13) that Thread A just set gets silently cleared by Thread B's write. The PLC never sees the START command.

**Why it happens:**
`MachineControl` uses a `threading.Lock` on `cls._lock` for singleton creation, but there is no per-operation lock protecting the read-modify-write sequence. Concurrent callers both complete the read before either completes the write. The new auto page may introduce a second code path (via asyncio + `AsyncModbusService`) that bypasses the `MachineControl` singleton entirely, making the race structural.

**Consequences:**
START button press is silently lost. RESET hold-delay fires its bit write while a concurrent cutting-stop write is in progress. Both appear to succeed from the Python side but the PLC sees an incorrect register state.

**Prevention:**
Two options, in order of preference:
1. Route ALL register 20 bit operations through `MachineControl` — including the new 20.13/20.14 operations. Add `start_auto_cutting()` and `reset_auto_cutting()` methods to `MachineControl`. This keeps one serialization point.
2. If using `AsyncModbusService` for new bits, add a per-register async lock keyed on register address to `AsyncModbusService` so all register 20 operations (read-modify-write) are serialized.

The simplest correct path: use `MachineControl` (synchronous) for all register 20 bit operations and call it from the GUI thread, consistent with the existing pattern.

**Detection:**
- Stress test: press START and stop-cutting simultaneously (simulate via script or rapid button press)
- PLC monitoring: check that register 20 after concurrent operations contains all intended bits, not a subset
- Code review: confirm there is exactly one serialization point for register 20 writes

**Phase to address:** Architecture decision phase (before any button handler code is written). Decide: MachineControl-extended or new async path with per-register lock?

---

### Pitfall 4: RESET Button Hold-Delay Fires on Touch-Down Instead of Hold-Release

**What goes wrong:**
The PLC expects RESET (bit 20.14) to be pulsed: set high, hold for a defined interval, then clear. If the developer implements this with a `QTimer.singleShot(delay_ms, clear_bit)` but connects the bit-set to `pressed` (which fires on touch-down), and the timer-based bit-clear fires `delay_ms` later, the behavior is correct on mouse but incorrect on touch. The existing `TouchButton` emits `touch_pressed` and `touch_released`, which fire on touch-down and touch-up respectively. If the hold-delay logic uses `clicked` (which fires on touch-up after a press-release cycle) instead of the custom `touch_pressed`, the touch path adds the full finger-contact duration to the hold delay — making the total hold time unpredictable.

The opposite failure: if `touch_pressed` triggers the hold timer AND the operator's finger lifts before the timer fires, the developer may have added logic to cancel the timer on release — but if the cancel is wired to `released` (mouse) instead of `touch_released`, the cancellation is skipped entirely on touchscreen, and the bit stays set long past the intended hold duration.

**Why it happens:**
The existing `TouchButton` has four signals: `touch_pressed`, `touch_released`, `pressed` (QPushButton), `released` (QPushButton). On touchscreen, `pressed`/`released` do NOT fire — only `touch_pressed`/`touch_released` fire. On mouse, `pressed`/`released` fire but `touch_*` do not. A developer who connects hold-delay start to `pressed` only sees it working during mouse testing and misses the touchscreen path.

**Consequences:**
On the factory touchscreen panel (industrial touch display), the RESET hold-delay either does nothing (timer never starts) or runs indefinitely (timer starts, never cancels). PLC receives bit 20.14 stuck high or never set.

**Prevention:**
Connect hold-delay logic to **both** `touch_pressed`/`touch_released` and `pressed`/`released`:

```python
btn_reset.touch_pressed.connect(self._on_reset_hold_start)
btn_reset.touch_released.connect(self._on_reset_hold_cancel)
btn_reset.pressed.connect(self._on_reset_hold_start)
btn_reset.released.connect(self._on_reset_hold_cancel)
```

Guard against double-trigger (touch fires touch_pressed AND sometimes pressed on some Qt platforms) with a `_hold_active` flag set on first call, cleared on cancel.

**Detection:**
- Test on the actual touchscreen panel — not just mouse on development machine
- Wire a debug log in `_on_reset_hold_start` — confirm it fires on touchscreen tap
- Verify bit 20.14 is set AND cleared within the expected window using PLC monitoring

**Phase to address:** Hold-delay button implementation phase. The signal connection pattern must be established before the timer logic is written.

---

### Pitfall 5: Floating Point Precision Error in L×10 Conversion

**What goes wrong:**
The operator enters L = 100.1 (mm). Python computes `100.1 * 10 = 1001.0000000000002` due to IEEE 754 floating point. `int(1001.0000000000002) = 1001`, which happens to be correct. But `150.3 * 10 = 1502.9999999999998` and `int(1502.9999999999998) = 1502` instead of the expected 1503. The PLC receives 150.2mm instead of 150.3mm. At 10x scaling, a 0.1mm error in the stored value creates a 0.01mm error in the actual cut length — acceptable for most cuts, but the behavior is inconsistent and invisible to the operator.

**Why it happens:**
The existing codebase uses the same `x10` pattern for `inme_hizi` (`int(value * 100)` for the x100 case). The existing code is correct by luck for the values tested. Decimal values with repeating binary fractions (0.1, 0.3, 0.7) are the dangerous ones. `round()` before `int()` fixes this but is easy to forget.

**Consequences:**
Occasional off-by-one errors at the 0.1mm precision level that are difficult to reproduce and correlate with specific input values.

**Prevention:**
Use `round()` before `int()` for all scaling conversions:

```python
# WRONG
modbus_value = int(length_mm * 10)

# RIGHT
modbus_value = int(round(length_mm * 10))
```

Apply this consistently to all numeric PLC writes: `L×10`, `C` (direct), `S×100`, `P×X` (already integer-safe if inputs are validated as integers).

**Detection:**
Unit test: `assert int(round(150.3 * 10)) == 1503` — must pass. Run this test for all values with non-trivially-representable decimal fractions: 0.1, 0.3, 0.7, 1.1, 150.3, 999.9.

**Phase to address:** Parameter validation/conversion phase. Add unit tests for all scaling conversions before writing to Modbus.

---

### Pitfall 6: Sidebar Index Collision When Camera Page is Conditionally Present

**What goes wrong:**
The new auto page is described as "sidebar's 2nd slot" (after Kontrol Paneli). Current sidebar indices are:
- 0: Kontrol Paneli
- 1: Konumlandırma
- 2: Sensör Verileri
- 3: İzleme
- 4: Kamera (conditional — only when `camera_results_store is not None`)

If the new auto page is inserted at index 1, every existing page shifts by one. `_switch_page(1)` now opens the auto page, `_switch_page(2)` opens Konumlandırma, etc. The camera button's `lambda: self._switch_page(4)` now points at Konumlandırma instead of Kamera. Any hardcoded page index in tests or in `_switch_page` lambdas breaks.

**Why it happens:**
`main_controller.py` hardcodes page indices in `lambda: self._switch_page(N)` for each navigation button. There is no symbolic constant for page numbers. Adding a page in the middle requires updating every lambda after the insertion point — but the camera page is conditionally constructed, making its final index context-dependent.

**Consequences:**
Navigating to "Kamera" opens Konumlandırma. Automated tests that assert page index pass but navigate to the wrong page. First noticed during manual testing on hardware when clicking Kamera unexpectedly shows positioning controls.

**Prevention:**
Use named constants or an ordered list for page indices rather than bare integers. Define indices in one place:

```python
class PageIndex:
    CONTROL_PANEL = 0
    AUTO_CUTTING = 1        # new
    POSITIONING = 2         # was 1
    SENSOR = 3              # was 2
    MONITORING = 4          # was 3
    CAMERA = 5              # was 4 (conditional)
```

Update all `_switch_page(N)` lambdas and `stackedWidget.addWidget` calls atomically when the new page is added. The camera page index must be determined at runtime from `stackedWidget.count()` if it's added conditionally, not hardcoded.

**Detection:**
- After adding auto page: click every sidebar button, verify the correct page appears
- Check that Kamera button still opens camera page (not positioning or auto page)
- Grep for all `_switch_page(` calls and verify each number maps to the correct controller

**Phase to address:** Sidebar integration phase. Update all indices before writing any new page code.

---

## Moderate Pitfalls

---

### Pitfall 7: Accidental START When Navigating To or From Auto Page

**What goes wrong:**
Operator navigates to the auto page while the machine is mid-cycle (PLC already running a serial cut). The auto page initializes with default parameter values (P=0, L=0). If page initialization code writes default values to PLC registers as part of `__init__` or `showEvent`, it overwrites the in-progress cutting parameters. The PLC's D2050 (P×X) and D2064 (L×10) are updated mid-cycle with zeros, causing the cutting program to abort or behave erratically.

**Why it happens:**
It is natural to write "initial state" to PLC registers when a page becomes visible. The existing pages do not write to the PLC on show — they only read. The new page is different because it has PLC write responsibilities.

**Consequences:**
PLC receives P=0 or L=0 mid-cycle. Depending on PLC program logic, this may trigger an immediate stop (if P=0 means "no cuts remaining") or cause the PLC to reset the target length to zero. Either way, the operator loses the in-progress batch.

**Prevention:**
Never write to PLC registers during page initialization, `showEvent`, or on initial display. Write only on explicit operator confirmation (a distinct "PARAMETRELERI GÖNDER" or "KAYDET" button, separate from START). On page show, read back the current values from D2050, D2056, D2064 and populate the display fields — do not write.

**Detection:**
- Navigate to auto page while a test sequence is running on PLC simulator
- Confirm D2050 and D2064 are unchanged after page navigation
- Confirm "Kesilmiş Adet" display updates to reflect PLC's current D2056 without triggering a write

**Phase to address:** Auto page architecture phase. Establish "read on show, write only on explicit confirmation" as a design rule before any write code is added.

---

### Pitfall 8: START Button Active on Unvalidated Parameters

**What goes wrong:**
Operator opens the auto page with default/empty parameter fields (P=0, L=0, C=0, S=0, X=0). START button is enabled and tappable. Operator accidentally taps it (touch display, finger slip). PLC receives a START command with all-zero parameters and begins a cutting cycle with undefined behavior.

**Why it happens:**
The industrial control paradigm requires that control buttons are guarded by pre-conditions. The existing codebase has no parameter validation gates on control buttons. Adding a new page without validation gates replicates this absence.

**Consequences:**
A zero-length cutting cycle on a band saw is typically a no-op, but a zero-count (P×X=0) combined with START may leave the PLC in an indeterminate state that requires RESET to clear — which itself requires the hold-delay button that the operator may not know to use.

**Prevention:**
Validate before enabling START:
- P ≥ 1 (at least one piece)
- L > 0 (positive length)
- C > 0 (positive cutting speed)
- X ≥ 1 (at least one piece per pack)
- Parameters must have been explicitly written to PLC (a "sent" flag) before START is enabled

Implement as a `_validate_params()` method called from each parameter input change handler. Set `btnStart.setEnabled(valid)`.

**Detection:**
- Open page with all defaults; START button must be disabled
- Enter one valid parameter but leave others at zero; START button must remain disabled
- Enter all valid parameters; START button must become enabled

**Phase to address:** Parameter input phase. Validation logic must be in place before START button wiring is added.

---

### Pitfall 9: D2056 Read (Kesilmiş Adet) Shares the AsyncModbusService 10 Hz Read Loop

**What goes wrong:**
D2056 (current cut count, read-only) needs to be polled periodically to update the "Kesilmiş Adet" display. If the developer adds a separate `read_holding_registers(2056, 1)` call inside the existing `ModbusReader.read_all_sensors()` method (which reads 44 registers from address 1000), the read count jumps from 44 to 45 — but more critically, D2056 is far outside the current block (1000–1043). Adding a separate read creates a second Modbus TCP request per 10 Hz cycle. Under normal conditions this is fine, but if the PLC is under load or connection is marginal, the extra round-trip increases the chance of read timeouts, which mark the client as disconnected and trigger the 1-second reconnect cooldown, briefly stopping all data reads.

**Why it happens:**
The natural implementation is "add a read call for the new register." The existing code carefully batches all sensor reads into one request. The new read breaks the batch.

**Consequences:**
Under marginal network conditions, the extra read causes intermittent Modbus disconnects that ripple into the 10 Hz processing loop stalling for 1 second per cooldown, creating visible data gaps in the sensor graphs.

**Prevention:**
Two options:
1. Read D2056 from the GUI timer (200ms QTimer) using `MachineControl._read_register(2056)` — the synchronous client, separate from the async loop. This is a read of one register, low-frequency (5 Hz), and the synchronous client already exists.
2. Expand the async read block from 1000–1043 to also cover D2050 and D2056 by reading them as separate but sequential requests, or restructure the read to include a second batch.

Option 1 is simpler and consistent with how the positioning page reads machine state.

**Detection:**
- Monitor `AsyncModbusService.get_health()['error_count']` before and after adding the D2056 read
- Under simulated packet loss (network simulation), confirm error rate does not increase proportionally

**Phase to address:** PLC read integration phase. Decide read strategy before implementing the display update timer.

---

### Pitfall 10: MachineControl Singleton Not Initialized With New Bit Constants

**What goes wrong:**
The new page needs bits 20.13 (START) and 20.14 (RESET), neither of which exists in `MachineControl`. The developer adds methods directly to the new controller (`auto_cutting_controller.py`) that call `machine_control._set_bit(20, 13, True)` directly, bypassing `MachineControl`'s interface. This creates two separate classes that both know about register 20's bit layout. When the bit layout changes (e.g., PLC firmware update reassigns bits), there are two places to fix instead of one.

**Why it happens:**
It is faster to call `_set_bit` directly (it's a public-by-convention method) than to add new named methods to `MachineControl`. The singleton pattern in `MachineControl` invites bypassing the interface.

**Consequences:**
Maintenance debt: future developers do not know that register 20 is managed in two places. Risk of bit mask collision if a future feature adds another register 20 bit in the controller file without checking `MachineControl`.

**Prevention:**
Add named methods to `MachineControl`:
```python
AUTO_CUTTING_START_BIT = 13   # 20.13
AUTO_CUTTING_RESET_BIT = 14   # 20.14

def start_auto_cutting(self) -> bool:
    return self._set_bit(self.CONTROL_REGISTER, self.AUTO_CUTTING_START_BIT, True)

def reset_auto_cutting(self) -> bool:
    return self._set_bit(self.CONTROL_REGISTER, self.AUTO_CUTTING_RESET_BIT, True)
```

All register 20 knowledge lives in `MachineControl`. The new controller imports only `MachineControl`.

**Detection:**
- Code review: grep for `_set_bit(20,` or `_set_bit(self.CONTROL_REGISTER` outside `machine_control.py` — must return zero results

**Phase to address:** Architecture phase. Extend `MachineControl` before writing any GUI button handler code.

---

### Pitfall 11: `İPTAL` (Bit 20.4) Collides With Existing `CUTTING_STOP_BIT = 4`

**What goes wrong:**
The milestone spec lists İPTAL as 20.4. `MachineControl` already defines `CUTTING_STOP_BIT = 4`. The auto page's "İPTAL" button and the existing `stop_cutting()` method both target the same bit. If the new page adds a separate button labeled "İPTAL" that calls a new method with its own `_set_bit(20, 4, True)`, the implementation is a duplicate. Worse, if the developer assumes 20.4 is a *different* bit reserved for auto-mode cancel (a misread of the spec), they may define `AUTO_CANCEL_BIT = 4` alongside `CUTTING_STOP_BIT = 4` — two different constant names for the same bit — and both get used in the codebase, creating confusion.

**Why it happens:**
The milestone spec uses domain terminology ("İPTAL") without noting that this maps to the existing `stop_cutting()` operation. Developers reading only the milestone spec do not cross-reference `MachineControl`.

**Consequences:**
Either duplicate code (harmless but messy) or two constants with the same value (confusing). In the worst case, a developer adds a new constant `AUTO_CANCEL_BIT = 4` and later a different developer changes `CUTTING_STOP_BIT = 4` to a different value (wrong, but plausible if bit layout docs are ambiguous), creating a divergence.

**Prevention:**
Check `MachineControl` constants before implementing any new bit operation. 20.4 maps to `CUTTING_STOP_BIT = 4` and `stop_cutting()` already exists. The auto page's İPTAL button should call `machine_control.stop_cutting()` — no new method needed.

**Detection:**
- Code review: list all bit constants in `MachineControl` and verify no two have the same value unless intentional
- Grep for `BIT = 4` — should appear once as `CUTTING_STOP_BIT`

**Phase to address:** Architecture review before any new bit constant is defined.

---

## Minor Pitfalls

---

### Pitfall 12: NumpadDialog Decimal Input for L When PLC Expects Integer

**What goes wrong:**
The existing `NumpadDialog` accepts arbitrary numeric input. An operator enters L = 150.5 (mm). `L × 10 = 1505` — valid. But the numpad also allows L = 150.12 (three significant decimal digits). `L × 10 = 1501.2`, `int(round(1501.2)) = 1501`, silently truncated to 150.1mm. The operator's entered value is accepted without error feedback.

**Prevention:**
Validate L input to at most one decimal place. Reject or round-to-nearest-0.1 in the input handler. Display the effective value that will be sent to the PLC: "PLC'ye gönderilecek: 150.1 mm".

**Phase to address:** Parameter input validation phase.

---

### Pitfall 13: `write_registers` Not Available on `MachineControl`'s Synchronous Client Path

**What goes wrong:**
`MachineControl` uses `pymodbus.client.ModbusTcpClient` (synchronous). The synchronous `ModbusTcpClient` does have `write_registers`, but the developer may not notice it is a different method signature from `write_register`. Passing a Python list `[low_word, high_word]` vs a `list[int]` — the sync client accepts it directly but the async client may require explicit argument forms. Confusion between the two clients may cause a `TypeError` at runtime that is silent in exception-swallowing wrappers.

**Prevention:**
Write the Double Word write method in `MachineControl` as an explicit test first. Confirm `self.client.write_registers(address=2064, values=[low, high])` returns a non-error response.

**Phase to address:** Modbus Double Word write implementation phase.

---

### Pitfall 14: QTimer for D2056 Polling Created Outside GUI Thread

**What goes wrong:**
Qt documentation states: "Timers can only be started and stopped from the thread they belong to." If `QTimer` for the D2056 display refresh is created or started in a method that gets called from the asyncio thread (e.g., a callback triggered by the async loop), it is created in the wrong thread. Its `timeout` signal fires but the connected slot runs in the wrong thread context, causing unpredictable behavior on touchscreen panels.

**Prevention:**
Create all `QTimer` instances in `__init__` (which is called from the GUI thread) or inside `showEvent` (also GUI thread). Never create or start a `QTimer` in a method called from asyncio.

**Phase to address:** Display refresh timer phase.

---

## Integration Gotchas

Specific mistakes when connecting the new page to the existing system.

| Integration Point | Common Mistake | Correct Approach |
|-------------------|---------------|------------------|
| Shared register 20 (bits 20.3, 20.4, 20.9–20.14) | Concurrent bit writes from two code paths (auto page + existing control panel) | Route all register 20 writes through `MachineControl` singleton — one serialization point |
| D2064 Double Word write | Using two `write_register` calls (FC6 twice) | Add `write_registers` (FC16) to `AsyncModbusService` and call once with `[low_word, high_word]` |
| C and S parameters (shared with manual cutting) | Writing C and S on every auto page show event or timer tick | Write C and S only on explicit operator action; read back current values on page open |
| Sidebar page index | Hardcoding new page at index 1 without updating all downstream lambdas | Use named constants for page indices; update all `_switch_page(N)` calls atomically |
| D2056 read (current count) | Adding to the existing 44-register async read block | Read via `MachineControl` synchronous client from GUI timer thread (200ms) |
| START/RESET signals | Wiring to `clicked` only (works for mouse, not touch) | Wire to both `touch_pressed`/`touch_released` AND `pressed`/`released` |
| asyncio from auto page | Calling `run_coroutine_threadsafe` without storing the future | Store the future and add a done callback to catch exceptions: `f.add_done_callback(lambda fut: fut.exception() and logger.error(…))` |

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| `AsyncModbusService` extension | Missing `write_registers` method | Add and unit-test before any Double Word write code is written |
| `MachineControl` extension | New bit constants duplicating existing or wrong indices | Audit all existing constants; add named methods for 20.13 and 20.14 only |
| D2064 Double Word write | Wrong word order (Mitsubishi: low word at lower address) | Test write with known value against PLC monitoring before GUI integration |
| L×10 / S×100 conversion | Floating-point truncation error | Use `int(round(value * scale))` universally; unit test edge cases |
| Sidebar insertion | Page index collision (camera button broken) | Use symbolic constants; verify all sidebar buttons after insertion |
| Hold-delay RESET button | Mouse-only wiring misses touch events | Connect to `touch_pressed`/`touch_released` AND `pressed`/`released` |
| Parameter → START gate | START enabled on empty parameters | Implement `_validate_params()` before START button connection |
| Page initialization | Writing to PLC on page show | No PLC writes in `__init__` or `showEvent`; only reads |
| Concurrent register 20 access | Race condition between auto page and existing control panel buttons | Confirm only `MachineControl` singleton path reaches register 20 |
| D2056 display refresh | Extra async read destabilizing 10 Hz loop | Use synchronous `MachineControl` read from GUI timer; never add to async read batch |

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong word order for D2064 | LOW | Swap `[low, high]` → `[high, low]` in the split function; retested in minutes |
| Two sequential `write_register` calls for Double Word | LOW | Refactor to single `write_registers` call; add method to `AsyncModbusService` |
| Register 20 race condition (bit write from two paths) | MEDIUM | Consolidate to `MachineControl` singleton path; remove the second write path |
| RESET hold-delay not firing on touch | LOW | Add `touch_pressed` / `touch_released` connections; test on physical panel |
| `int()` truncation instead of `int(round())` | LOW | Global search-replace in the parameter conversion code; 5 minutes |
| Sidebar index collision (Kamera broken) | LOW | Update `PageIndex` constants and all `_switch_page` lambdas; 30 minutes |
| START fires on unvalidated params | MEDIUM | Add `_validate_params()` and connect to `setEnabled`; test all zero-value permutations |
| PLC registers written on page navigation | MEDIUM | Identify all write calls in `__init__`/`showEvent`; move to explicit confirm action |
| D2056 read destabilizing async loop | LOW | Move read to synchronous MachineControl path; no async changes needed |
| MachineControl bit constants duplicated outside class | LOW | Move constants to `MachineControl`; update import sites |

---

## Sources

- [pymodbus.org — Working with Data Types](https://www.pymodbus.org/docs/data-types) — BinaryPayloadBuilder word order options and 32-bit integer writing pattern
- [pymodbus.org — Writing Registers](https://www.pymodbus.org/docs/writing-registers) — write_registers (FC16) vs write_register (FC6)
- [PLCtalk — Modbus client word order issue when reading Dword](https://www.plctalk.net/forums/threads/modbus-client-word-order-issue-when-reading-dword.148891/) — confirms Mitsubishi low-word-at-lower-address convention
- [Continental Control Systems — Common Modbus Protocol Misconceptions](https://ctlsys.com/support/common_modbus_protocol_misconceptions/) — word order is not defined in Modbus standard, varies by vendor
- [Chipkin — How Real and 32-bit Data is Encoded in Modbus](https://store.chipkin.com/articles/how-real-floating-point-and-32-bit-data-is-encoded-in-modbus-rtu-messages) — four byte/word order variants explained
- [ABB — Using an HMI for reset and start](https://new.abb.com/low-voltage/products/safety-products/using-an-hmi-for-reset-and-start) — HMI button must write 1 on press only; no latching/toggling at HMI level
- [Machinery Safety 101 — Manual reset using an HMI](https://machinerysafety101.com/2021/06/02/manual-reset-using-an-hmi/) — HMI button press during E-stop can latch in PLC memory, causing auto-restart on E-stop reset
- [PySide6 QTimer documentation](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QTimer.html) — timers must be started/stopped from their owning thread
- [pymodbus Issue #2409 — struct.error with write_registers in 3.7.4](https://github.com/pymodbus-dev/pymodbus/issues/2409) — documents expected list[int] type for write_registers values parameter
- Codebase: `src/services/control/machine_control.py` — existing bit constants, `_set_bit`, synchronous read-modify-write pattern
- Codebase: `src/services/modbus/client.py` — `write_register` exists (FC6), `write_registers` (FC16) is absent and must be added
- Codebase: `src/gui/controllers/main_controller.py` — hardcoded page indices, conditional camera page construction pattern
- Codebase: `src/gui/widgets/touch_button.py` — `touch_pressed`/`touch_released` signals separate from `pressed`/`released`

---
*Pitfalls research for: automatic cutting page with PLC bit operations and Double Word Modbus writes — v2.1 Otomatik Kesim Sayfası*
*Researched: 2026-04-08*
