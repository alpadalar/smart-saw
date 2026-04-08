# Project Research Summary

**Project:** Smart Saw Control System — v2.1 Otomatik Kesim Sayfası
**Domain:** Industrial PLC HMI — automatic/serial cutting page added to existing PySide6 + pymodbus control system
**Researched:** 2026-04-08
**Confidence:** HIGH

## Executive Summary

v2.1 adds a single new GUI page — the Otomatik Kesim (Automatic Cutting) page — to an already-working industrial band saw HMI. This is not greenfield: the PySide6 GUI framework, pymodbus 3.5.4 client, `MachineControl` singleton, `NumpadDialog`, and `TouchButton` widget are all in place. The core new capability is a complete automatic/serial cutting workflow: the operator enters job parameters (target count, length, speed), the page writes them to PLC registers, and then monitors the live cut counter while the PLC executes the cycle. All required Modbus operations (single-register write, double-word two-register write, single-register read, bit set/clear via read-modify-write) are supported by the installed stack with zero new dependencies. The only new infrastructure item is one method on `MachineControl`: a double-word write using `client.write_registers()` (FC 16) for D2064/D2065.

The recommended build order follows strict dependency layering: first extend `MachineControl` with new constants and methods (the foundation everything else calls), then build `OtomatikKesimController` as a new `QWidget` following `PositioningController` as a structural template, and finally wire it into `MainController` at sidebar position 1 (shifting all existing pages up by one index). The most architecturally sensitive decision — already answered clearly by research — is that all register 20 bit operations must stay routed through the `MachineControl` singleton. Using the `AsyncModbusService` path for any auto-page bit write would introduce a read-modify-write race condition on register 20 that silently drops PLC commands.

The primary implementation risk is the double-word word order for D2064/D2065. Mitsubishi PLCs store 32-bit Double Words with the low word at the lower address (D2064 = low 16 bits, D2065 = high 16 bits), which is opposite to `pymodbus BinaryPayloadBuilder`'s default behavior. The correct approach — explicit struct-based splitting with `[low_word, high_word]` — is confirmed by both the existing `_decode_ieee754()` pattern in `ModbusReader` and community sources on Mitsubishi Modbus DWORD layout. Verification against PLC monitoring with a known round-number value must happen before any GUI integration test. A secondary risk is the sidebar index shift: inserting the new page at index 1 displaces every existing page, and the camera page's conditional `_switch_page(N)` lambda is the one most likely to break if the update is not done atomically.

---

## Key Findings

### Recommended Stack

No new dependencies are required for this milestone. `requirements.txt` is unchanged. Every needed capability — FC 16 multi-register write, bit-level read-modify-write, hold-delay button patterns, and integer numpad input — is already present in the installed stack.

**Core technologies:**
- `pymodbus 3.5.4`: `write_registers(address, values: List[int])` confirmed available on `ModbusTcpClient` (sync); handles FC 16 two-register write for D2064/D2065 in a single atomic call
- `PySide6 6.9.2`: `QTimer.setSingleShot(True)` with `pressed`/`released` + `touch_pressed`/`touch_released` signals handles hold-delay RESET pattern; `QStackedWidget` page insertion is a standard operation
- `stdlib struct`: Used for explicit low/high word splitting — `int & 0xFFFF` and `int >> 16` are the correct and readable approach; no `BinaryPayloadBuilder` needed
- `MachineControl` (existing sync singleton): All GUI-thread-to-PLC writes go through this class; `_set_bit()`, `_write_register()`, `_write_register_atomic()` are already proven for register 20 bit operations
- `NumpadDialog` (existing): Integer-only digit input, no decimal key; the same dialog handles all five parameter fields (P, X, L, C, S) with a thin validation wrapper per field

See [STACK.md](./STACK.md) for full API verification details, implementation patterns, and rationale for what NOT to add.

### Expected Features

The PLC register spec from PROJECT.md defines the complete set of required operations. Features map directly to PLC register interactions; there is no ambiguity about what must be implemented.

**Must have (table stakes) — v2.1 launch:**
- Parameter entry: P (hedef adet), X (paketteki adet), L (uzunluk mm), C (kesim hızı), S (inme hızı) — five touch numpad fields
- Write D2050 (Word): P x X — total target pieces to PLC
- Write D2064/D2065 (Double Word): L x 10 — target length with 0.1mm precision
- Live D2056 read at 5 Hz — kesilmiş adet (current cut count) display
- START button — momentary set of bit 20.13
- RESET button — hold-delay set/clear of bit 20.14 (prevents accidental reset)
- IPTAL button — momentary set of bit 20.4 (reuses existing `CUTTING_STOP_BIT`)
- Sidebar navigation button at position 1 (between Kontrol Paneli and Konumlandırma)
- PLC connection guard — disable START/RESET/IPTAL when `MachineControl.is_connected` is False

**Should have (low-cost differentiators — same milestone):**
- "Hesaplanan toplam: PxX parca" preview label — updates dynamically as P or X change
- "X / Y" progress format alongside raw counter (kesilmis / hedef)
- Parameter lock during active job — `setEnabled(False)` on input fields when D2056 is counting
- Input validation with Turkish reason messages per field

**Defer (v2.2+):**
- Job history / log panel — belongs in Monitoring page, requires layout redesign
- Save/load job programs — requires job library screen and more PLC registers
- Completion audio alert — no speaker output defined in system

**Anti-features to avoid:** auto-restart after completion, ML mode during auto cutting, decimal point in NumpadDialog, progress bar widget, confirmation dialog before START.

See [FEATURES.md](./FEATURES.md) for full feature dependency graph, complexity ratings, and the PLC register dependency map.

### Architecture Approach

The new page follows the exact same structural pattern as `PositioningController`. Three files change: one new controller is created (`otomatik_kesim_controller.py`), `MachineControl` gets additive-only new constants and methods, and `MainController` is updated to insert the new page at index 1. No other files are touched — `AsyncModbusService`, `ControlManager`, `DataProcessingPipeline`, all database schemas, and the camera subsystem are explicitly out of scope.

**Major components (build order = dependency order):**
1. **MachineControl extensions** (`src/services/control/machine_control.py`) — Add `TARGET_ADET_REGISTER=2050`, `TARGET_UZUNLUK_REGISTER=2064`, `KESILMIS_ADET_REGISTER=2056`, `AUTO_START_BIT=13`, `AUTO_RESET_BIT=14`; implement `write_target_adet()`, `write_target_uzunluk()` (FC 16 double-word), `read_kesilmis_adet()`, `start_auto_cutting()`, `reset_auto_cutting(bool)`, `cancel_auto_cutting()`. Zero modifications to existing methods; purely additive.
2. **OtomatikKesimController** (`src/gui/controllers/otomatik_kesim_controller.py`) — New `QWidget` page: five parameter fields via `NumpadDialog`, START/RESET/IPTAL buttons, 500ms `QTimer` for D2056 polling, `stop_timers()` lifecycle method, `_validate_params()` gate on START button.
3. **MainController integration** (`src/gui/controllers/main_controller.py`) — Insert new page at `stackedWidget` index 1; shift all existing button lambdas and y-coordinates; update `nav_buttons` list; add `otomatik_kesim_page` to `closeEvent` stop loop. Final assembly step.

**Key patterns:**
- MachineControl for all GUI-thread writes (not `asyncio.run_coroutine_threadsafe`) — same as `PositioningController`
- QTimer at 500ms for D2056 read (synchronous `MachineControl._read_register()` — not added to the async 10 Hz loop)
- TouchButton with four signal connections (`pressed`/`released` + `touch_pressed`/`touch_released`) for RESET hold-delay
- No PLC writes in `__init__` or `showEvent` — read current values on page show, write only on explicit operator action

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full data flow diagram, code patterns with signatures, and the complete build order with rationale.

### Critical Pitfalls

1. **Wrong word order for D2064 Double Word (CRITICAL)** — `BinaryPayloadBuilder` defaults (high word first) are opposite to Mitsubishi convention (low word at lower address). Use explicit bit-mask split: `[value & 0xFFFF, (value >> 16) & 0xFFFF]`. Verify with L=1000mm (10000 = 0x2710) before any GUI integration test: D2064 must read 0x2710, D2065 must read 0x0000.

2. **Two sequential `write_register` calls instead of one `write_registers` (CRITICAL)** — Calling FC 6 twice for D2064 and D2065 creates a window where the PLC sees a half-updated 32-bit value. Use a single FC 16 `write_registers(2064, [low, high])` call. `AsyncModbusService` does not currently have this method — but for the auto page this is irrelevant since `MachineControl` (sync client) is used.

3. **Register 20 read-modify-write race condition (CRITICAL)** — If auto page bit operations bypass `MachineControl` and use `AsyncModbusService` directly, concurrent writes from two threads both read register 20 and the second write overwrites the first's bit change. Prevention: route ALL register 20 operations through `MachineControl` singleton.

4. **RESET hold-delay wired to mouse signals only — misses touch events (CRITICAL for factory panel)** — `TouchButton.pressed`/`.released` do not fire on touchscreen; only `touch_pressed`/`touch_released` fire. Connect all four signals. Guard against double-trigger with a `_hold_active` flag.

5. **Sidebar index collision when inserting at position 1 (MODERATE)** — Every existing `_switch_page(N)` lambda after the insertion point becomes wrong. The camera page's conditional construction makes its final index especially easy to break. Use `PageIndex` named constants and update all lambdas atomically.

See [PITFALLS.md](./PITFALLS.md) for 14 pitfalls including floating-point truncation in L x 10 scaling, `QTimer` thread ownership rules, START button enabled on unvalidated parameters, and accidental PLC writes on page navigation.

---

## Implications for Roadmap

### Phase 1: MachineControl Extension
**Rationale:** `OtomatikKesimController` depends on these methods. Building them first lets the double-word write be verified against real PLC hardware before any GUI is involved. This is the only phase with new infrastructure logic (FC 16 write) — all other phases are wiring and layout.
**Delivers:** New constants (`TARGET_ADET_REGISTER`, `TARGET_UZUNLUK_REGISTER`, `KESILMIS_ADET_REGISTER`, `AUTO_START_BIT=13`, `AUTO_RESET_BIT=14`) and methods (`write_target_adet`, `write_target_uzunluk`, `read_kesilmis_adet`, `start_auto_cutting`, `reset_auto_cutting`, `cancel_auto_cutting`) in `machine_control.py`. Unit tests for D2064 encoding (including `int(round())` edge cases for L x 10 at 0.1mm precision).
**Addresses:** D2050 Word write, D2064/D2065 Double Word write, D2056 read, bits 20.13 and 20.14
**Avoids:** Pitfall 1 (wrong word order), Pitfall 2 (two write_register calls), Pitfall 3 (register 20 race condition), Pitfall 5 (float truncation), Pitfall 10 (bit constants outside MachineControl)
**Research flag:** Standard patterns — no additional research needed; all APIs confirmed via direct pymodbus inspection

### Phase 2: OtomatikKesimController (Page Logic)
**Rationale:** With Phase 1 done, the controller can be built and tested against the real Modbus layer. This is the largest unit of work — five parameter fields, three action buttons, a polling timer, and parameter validation logic.
**Delivers:** `src/gui/controllers/otomatik_kesim_controller.py` — full QWidget page with five NumpadDialog tap handlers (P, X, L, C, S), computed P x X preview label, write-on-confirm action, 500ms QTimer for D2056, START/RESET/IPTAL button wiring (with all four signal connections on RESET TouchButton), `_validate_params()` START gate, parameter lock when counter active, `stop_timers()` lifecycle method.
**Uses:** Phase 1 `MachineControl` methods, existing `NumpadDialog`, existing `TouchButton`
**Avoids:** Pitfall 4 (RESET touch signals), Pitfall 7 (accidental PLC write on page show), Pitfall 8 (START on unvalidated params), Pitfall 9 (D2056 added to async read loop), Pitfall 14 (QTimer created outside GUI thread)
**Research flag:** Standard patterns — follows `PositioningController` as template; no new research needed

### Phase 3: MainController Integration
**Rationale:** Pure assembly — insert the finished page into the navigation system. Done last because it is safest to integrate a complete, tested component rather than scaffold the nav wiring first.
**Delivers:** Updated `main_controller.py`: `OtomatikKesimController` at `stackedWidget` index 1, `PageIndex` named constants for all page numbers, all `_switch_page(N)` lambdas updated with new indices, `btnOtomatikKesim` sidebar button at y=286, all existing buttons shifted (Konumlandirma to y=407, Sensor to y=528, Izleme to y=649, Kamera to y=770), `otomatik_kesim_page` added to `closeEvent` stop loop.
**Avoids:** Pitfall 6 (sidebar index collision breaking camera button)
**Research flag:** Standard patterns — no additional research needed; page insertion has been done four times already in this project

### Phase Ordering Rationale

- **MachineControl before GUI:** The double-word write is the only technically novel operation and the most likely source of PLC data errors. Isolating it in Phase 1 lets it be unit-tested and verified against PLC hardware independently.
- **Controller before integration:** `OtomatikKesimController` in Phase 2 is fully self-contained and testable after Phase 1. Integration into `MainController` in Phase 3 is then pure assembly with no logic risk.
- **Index collision handled at assembly time:** The sidebar re-index affects `MainController` only. Doing it as the last step means there is exactly one moment where all lambdas are updated, reducing the chance of a partial update.
- **D2056 via synchronous client from GUI timer (never via async loop):** This decision, driven by Pitfall 9, means the polling timer is a self-contained part of Phase 2 with no async pipeline changes and no risk to the 10 Hz data collection loop.

### Research Flags

**Phases needing deeper investigation during planning:**
- **Phase 1 (MachineControl):** Word order for D2064/D2065 must be verified against actual PLC hardware or PLC documentation before Phase 2 starts. Research confirms Mitsubishi convention (low word at lower address) but this is an open verification item, not a resolved fact. Write L=1000mm and check D2064 = 0x2710, D2065 = 0x0000 via PLC monitoring before proceeding.
- **Phase 1 (MachineControl):** Confirm whether bit 20.13 (AUTO START) must be explicitly cleared by the GUI after PLC acknowledgment, or whether the PLC self-latches. This affects whether `start_auto_cutting()` needs a paired `stop_auto_cutting()` call.

**Phases with standard patterns (skip research-phase):**
- **Phase 2 (Controller):** `PositioningController` is a direct structural template. `NumpadDialog`, `TouchButton`, `QTimer` polling, `MachineControl` singleton init — all established patterns with existing working implementations.
- **Phase 3 (Integration):** Page insertion into `QStackedWidget` and sidebar button addition have been done four times already; the pattern is fully established.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All required APIs verified via direct inspection of installed pymodbus 3.5.4 and PySide6 6.9.2; zero new dependencies confirmed by exhaustive capability mapping |
| Features | HIGH | PLC register spec from PROJECT.md is authoritative; all features traced to specific registers (D2050, D2056, D2064, bits 20.4/20.13/20.14); feature complexity ratings validated against existing analogous implementations |
| Architecture | HIGH | Based on direct codebase inspection of `PositioningController`, `MachineControl`, `MainController`, `TouchButton`, and `NumpadDialog`; all patterns are copies of working production code, not novel designs |
| Pitfalls | HIGH | Critical pitfalls verified against pymodbus official docs, PLCtalk community Mitsubishi DWORD thread, PySide6 QTimer thread ownership docs, and direct code review of `AsyncModbusService` confirming absence of `write_registers` |

**Overall confidence:** HIGH

### Gaps to Address

- **D2064 word order verification (HIGH priority — must resolve before Phase 2):** Write L=1000mm and verify D2064 = 0x2710, D2065 = 0x0000 via PLC monitoring software before building any GUI on top of the write method. Cannot be resolved by research alone.

- **Bit 20.13 latch behavior (MEDIUM — must resolve during Phase 1):** Jog bits use press-and-hold. Auto-start may be momentary (PLC latches) or may require GUI-side explicit clear. Confirm from PLC documentation before implementing `start_auto_cutting()`.

- **RESET hold duration requirement (LOW):** PLC may require bit 20.14 to be held for a minimum duration. Current suggestion of 1500ms is unverified. Confirm with PLC engineer or PLC program logic review.

- **Integer-only input for S (inme hizi) (LOW):** Research recommends accepting integer mm/min input. Confirm no fractional precision is operationally required before finalizing the NumpadDialog wrapper for S.

---

## Sources

### Primary (HIGH confidence — direct codebase inspection)
- `src/services/control/machine_control.py` — `_set_bit()`, `_write_register()`, `CONTROL_REGISTER=20`, sync client pattern, existing bit constants
- `src/gui/controllers/positioning_controller.py` — `MachineControl` singleton init pattern, `QTimer` polling, `TouchButton` wiring
- `src/gui/controllers/control_panel_controller.py` — `NumpadDialog` usage, asyncio path vs direct MachineControl distinction
- `src/gui/controllers/main_controller.py` — sidebar geometry (y=165/286/407/528/649), page index pattern, `closeEvent` pattern
- `src/services/modbus/client.py` — `write_register` (FC6) present; `write_registers` (FC16) absent from `AsyncModbusService`; `ModbusTcpClient` sync client has `write_registers`
- `src/services/modbus/reader.py` — `_decode_ieee754()` confirming low/high word order for multi-register reads
- `src/gui/widgets/touch_button.py` — `touch_pressed`/`touch_released` vs `pressed`/`released` signal behavior
- `src/gui/numpad.py` — integer-only digit input confirmed; no decimal key
- `.planning/PROJECT.md` — authoritative PLC register spec: D2050, D2056, D2064, bits 20.4/20.13/20.14
- pymodbus 3.5.4 (installed) — `write_registers(address, values: List[int])` confirmed via `help()` introspection
- PySide6 6.9.2 (installed) — `QTimer.setSingleShot(True)` confirmed

### Secondary (MEDIUM confidence — official docs and community sources)
- [pymodbus.org — Write Registers](https://www.pymodbus.org/docs/writing-registers) — FC6 vs FC16 distinction
- [PLCtalk — Modbus client word order issue when reading Dword](https://www.plctalk.net/forums/threads/modbus-client-word-order-issue-when-reading-dword.148891/) — confirms Mitsubishi low-word-at-lower-address DWORD convention
- [Continental Control Systems — Common Modbus Protocol Misconceptions](https://ctlsys.com/support/common_modbus_protocol_misconceptions/) — word order is vendor-defined, not in Modbus standard
- [Chipkin — How Real and 32-bit Data is Encoded in Modbus](https://store.chipkin.com/articles/how-real-floating-point-and-32-bit-data-is-encoded-in-modbus-rtu-messages) — four byte/word order variants documented
- [PySide6 QTimer documentation](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QTimer.html) — timers must be started/stopped from their owning thread
- [Machinery Safety 101 — Manual reset using an HMI](https://machinerysafety101.com/2021/06/02/manual-reset-using-an-hmi/) — bit 20.14 is a process reset, not a safety reset; HMI-initiated reset is acceptable
- [ISA-101 HMI standard summary](https://www.iotindustries.sk/en/blog/isa-101/) — status indicator color conventions for counter displays
- [DoAll S-320CNC band saw HMI](https://www.doallsaws.com/s-320cnc-automatic-cnc-swivel-band-saw) — reference for job counter, status feedback, and safety interlock patterns

---
*Research completed: 2026-04-08*
*Ready for roadmap: yes*
