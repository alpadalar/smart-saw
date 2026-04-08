# Feature Landscape: Otomatik Kesim Sayfası (v2.1)

**Domain:** Industrial HMI automatic/serial cutting page with PLC integration
**Researched:** 2026-04-08
**Confidence:** HIGH (PROJECT.md PLC register spec + codebase analysis + industrial HMI domain research)

---

## Context: New GUI Page on Existing Codebase

This is not greenfield. v2.1 adds one new page (Otomatik Kesim / Automatic Cutting) to an already
working PySide6 HMI that has sidebar navigation, a touch numpad, TouchButton widget, and
AsyncModbusService. All new features are scoped to this single page and its PLC integration.

**What the PLC spec requires (from PROJECT.md):**
- Write D2050 (Word): `P × X` — hedef adet × paket adeti → toplam parça
- Write D2064 (Double Word): `L × 10` — uzunluk mm × 10
- Read D2056 (Word): kesilmiş adet — live counter from PLC
- Write bit 20.13: START (momentary)
- Write bit 20.14: RESET (hold-delay pattern like existing TouchButton operations)
- Write bit 20.4: İPTAL / Cancel (existing CUTTING_STOP_BIT, already in MachineControl)
- Shared with manual page: C (kesim hızı → D2066) and S (inme hızı → D2041)

---

## Table Stakes

Features operators expect from any automatic/serial cutting HMI page. Missing any of these makes
the page feel broken or incomplete — operators will not trust it.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Parameter entry: P (hedef adet) | Every auto-cut system requires quantity target before job start | LOW | Touch numpad opens on tap; integer ≥ 1; validates before write; shared pattern with existing kesme hizi input |
| Parameter entry: X (paketteki adet) | Serial production needs batch-size; P×X gives total to PLC D2050 | LOW | Touch numpad; integer ≥ 1; P and X entered together; product written to D2050 as Word |
| Parameter entry: L (uzunluk mm) | Cut length is the core job parameter — no cut without it | LOW | Touch numpad; positive integer; value ×10 written to D2064 as Double Word (2 registers) |
| Parameter entry: C (kesim hızı) | Speed affects cut quality; operator must confirm before auto job | LOW | Shared register D2066 with control panel; same numpad pattern; labeled mm/dk |
| Parameter entry: S (inme hızı) | Descent speed affects material and blade; required for auto mode | LOW | Shared register D2041 with control panel; same numpad ×100 scaling |
| Live kesilmiş adet counter display | Operator must see job progress in real time; core feedback loop | LOW | Read D2056 at 5 Hz via QTimer; large, prominent display near parameter fields |
| START button | Initiates the automatic cutting cycle on PLC | LOW | Momentary write to bit 20.13; no hold-delay needed; standard QPushButton |
| RESET button (hold-delay) | Clears PLC counter and state; accidental press must be prevented | MEDIUM | Same hold-delay pattern as existing positioning TouchButton ops; write to bit 20.14 on sustained press |
| İPTAL / Cancel button | Operator must be able to abort a running cycle safely | LOW | Writes bit 20.4 (CUTTING_STOP_BIT already in MachineControl); momentary; confirm dialog or immediate |
| Sidebar navigation button (2nd slot) | All pages have sidebar entries; missing button = page inaccessible | LOW | Add btnOtomatikKesim between Kontrol Paneli and Konumlandırma; same nav_btn_style |
| Connection status awareness | Buttons must not mislead operator when PLC is disconnected | LOW | Disable START/RESET/İPTAL if MachineControl.is_connected is False; show "Bağlantı yok" label |

---

## Differentiators

Features that increase operator trust and operational efficiency beyond the bare minimum. None of
these block the job from running, but all reduce errors and save time at the machine.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Parameter lock during active job | Prevents mid-job parameter edits that would create PLC data inconsistency | LOW | setEnabled(False) on all numpad-tap labels/fields when job is running; job state inferred from D2056 counting up |
| Progress display: kesilmiş / hedef | "3 / 10" format gives immediate sense of job completion — more readable than counter alone | LOW | Single QLabel showing "{kesilmiş_adet} / {hedef_adet}" formatted string; hedef_adet is local state |
| Completion visual feedback | Operator needs to know job is done without staring at screen | LOW | Color change or icon on counter label when kesilmiş_adet reaches hedef_adet; ISA-101: use consistent status color |
| Input validation with reason | Touch operator miskeys often; show what's wrong, not just "invalid" | LOW | Label shows "P: minimum 1 olmalı" or "L: boş bırakılamaz" rather than silent reject |
| Parameter persistence across navigation | Operator sets P/L/C/S, navigates away, returns — values should not reset | LOW | Store last-entered values in controller state dict; repopulate labels on page show |
| "Hesaplanan toplam" display | Show P×X before writing to PLC so operator can verify the product | LOW | Dynamic label updates on P or X change: "Toplam: 25 parça (5×5)"; no extra PLC write |

---

## Anti-Features

Commonly considered additions that would be harmful, wasteful, or out of scope for this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Job history / log panel on this page | Adds significant layout complexity; log data already goes to existing SQLite databases | Use Monitoring page for historical data; this page is for real-time job control only |
| Alarm/fault display on this page | Alarm state is PLC-managed; duplicating alarm logic creates maintenance surface | Route alarms to existing Control Panel page display; reference existing alarm_status register (1031) |
| Auto-restart after completion | "When done, start again" — sounds convenient but risks material overrun if operator is not at machine | Require explicit re-press of START; completion state must be acknowledged, not auto-cleared |
| ML mode during auto cutting | Mixing ML speed adjustment with PLC auto-cycle causes speed register contention | Auto-cut page uses fixed C/S values only; ML mode belongs to Control Panel page |
| Decimal length input | D2064 = L × 10 → PLC expects integer tenths of mm; decimal UI would require two-field design | Integer mm input only; label "(×0.1 mm hassasiyet)" for documentation; single numpad field |
| Save/load job programs | Multi-job program storage requires a job library screen and more registers | Out of scope v2.1; single current job only; operator enters fresh each session |
| Progress bar widget | QProgressBar for piece count adds visual polish but requires hedef_adet always-current sync | Use text counter "X / Y" instead; simpler, less error-prone when target changes mid-display |
| Confirmation dialog before START | Adds an extra tap on a touchscreen — operators in production find this patronizing | Parameter lock prevents accidental changes; START intent is clear from context |

---

## Feature Dependencies

```
Otomatik Kesim Page (GUI controller)
    requires --> MachineControl singleton (existing)
        └── _write_register(2050, P*X)          # Word write
        └── _write_double_register(2064, L*10)  # Double Word write — NEEDS NEW METHOD
        └── _read_register(2056)                # Read kesilmiş adet
        └── _set_bit(20, 13, True)              # START momentary
        └── _set_bit(20, 14, True/False)        # RESET hold-delay
        └── _set_bit(20, 4, True)               # İPTAL (CUTTING_STOP_BIT exists)
    requires --> ModbusWriter (existing)
        └── write_speeds(C, S)                  # Shared registers D2066 / D2041
    requires --> NumpadDialog (existing)         # Touch numpad, already works
    requires --> TouchButton widget (existing)   # For RESET hold-delay behavior
    requires --> MainController sidebar          # Add new nav button

MachineControl — new method needed
    requires --> Double Word write capability (2 consecutive Word registers)
        └── D2064 = L*10 → registers[2064] = high word, registers[2065] = low word
        └── pymodbus write_registers() for 2-register block

D2056 reader (kesilmiş adet)
    requires --> MachineControl._read_register(2056) at 5 Hz via QTimer
    reads independently from AsyncModbusService (same pattern as positioning page)

Sidebar nav button
    requires --> MainController._setup_ui() modification
    requires --> nav_buttons list extension
    requires --> stackedWidget page index assignment
```

### Dependency Notes

- **Double Word write is the one new infrastructure item.** D2064 requires writing two consecutive
  16-bit registers (high word + low word) as a single atomic 32-bit value. `MachineControl` currently
  only has `_write_register()` (single Word). A `_write_double_register()` method using
  `client.write_registers(address, [high, low])` must be added.

- **MachineControl is a singleton.** The new page calls the same singleton already used by the
  positioning controller. No new Modbus connection — same instance, same lock.

- **Shared speed registers.** C (D2066) and S (D2041) are written via the existing `ModbusWriter`.
  Writing from the auto-cut page uses the same path as the control panel — no register conflict,
  but both pages must show the current values. The auto-cut page should read back current speed
  values on page-show to pre-populate its fields.

- **D2056 read vs AsyncModbusService reads.** The existing 10 Hz Modbus poll reads register 1014
  (`kesilen_parca_adeti` from address block 1000–1043). D2056 is outside this block and is NOT
  currently read. The auto-cut page needs a separate periodic read of D2056 using
  `MachineControl._read_register(2056)` — same synchronous pattern as the positioning controller.

- **Bit 20.4 (İPTAL) already exists.** `CUTTING_STOP_BIT = 4` is defined in `MachineControl`.
  The new page can call `_set_bit(CONTROL_REGISTER, CUTTING_STOP_BIT, True)` directly.

- **Bits 20.13 and 20.14 are new.** AUTO_START_BIT = 13 and AUTO_RESET_BIT = 14 must be added as
  class constants to `MachineControl`. The underlying `_set_bit()` mechanism works for any bit.

---

## MVP Recommendation

### Build for v2.1 Launch

These directly map to PROJECT.md active requirements:

1. **Page scaffold + sidebar nav button** — add page to stacked widget, wire navigation
2. **P, X, L parameter entry** via NumpadDialog tap; computed P×X display label
3. **C, S parameter entry** (shared registers, same as control panel)
4. **Write D2050 and D2064** on confirm/apply (requires new `_write_double_register` in MachineControl)
5. **Write C/S speeds** using existing `ModbusWriter.write_speeds()`
6. **Live D2056 counter display** at 5 Hz via QTimer
7. **START button** — momentary bit 20.13 via MachineControl
8. **RESET button** — hold-delay pattern, bit 20.14 via TouchButton or timer
9. **İPTAL button** — momentary bit 20.4 (CUTTING_STOP_BIT, already exists)
10. **PLC connection guard** — disable action buttons when not connected

### Include as Low-Cost Differentiators (same milestone)

- Parameter lock when counter is active (setEnabled(False) on input labels)
- "X / Y" progress format label alongside raw counter
- "Hesaplanan toplam: P×X parça" preview label
- Input validation with Turkish reason messages

### Defer

- Job history panel: belongs in Monitoring page
- Save/load programs: v2.2+ feature
- Completion audio/alert: out of scope, no speaker output defined in system

---

## Complexity Summary

| Item | Complexity | Reason |
|------|------------|--------|
| Page scaffold + sidebar nav | LOW | Exact same pattern as existing pages |
| NumpadDialog integration for 5 fields | LOW | Dialog already exists and works |
| D2050 Word write | LOW | `_write_register()` already exists |
| D2064 Double Word write | MEDIUM | New `_write_double_register()` method needed in MachineControl |
| D2056 live read at 5 Hz | LOW | Same pattern as positioning controller's synchronous reads |
| START/İPTAL momentary bits | LOW | `_set_bit()` already works; just add bit constants |
| RESET hold-delay button | LOW | TouchButton or QTimer holds — existing pattern |
| Parameter lock during job | LOW | setEnabled(False) on widgets in timer callback |
| Progress "X / Y" display | LOW | String formatting in timer callback |

---

## Sources

- `/media/workspace/smart-saw/.planning/PROJECT.md` — PLC register spec (D2050, D2056, D2064, bit 20.x)
- `/media/workspace/smart-saw/src/services/control/machine_control.py` — Existing MachineControl singleton and bit patterns
- `/media/workspace/smart-saw/src/services/modbus/writer.py` — Speed register write patterns (D2066, D2041)
- `/media/workspace/smart-saw/src/gui/widgets/touch_button.py` — Hold-delay TouchButton pattern
- `/media/workspace/smart-saw/src/gui/controllers/main_controller.py` — Sidebar nav pattern
- `/media/workspace/smart-saw/src/gui/numpad.py` — Existing touch numpad dialog
- DoAll S-320CNC band saw HMI: https://www.doallsaws.com/s-320cnc-automatic-cnc-swivel-band-saw — reference for job counter, status feedback, and safety interlock patterns
- STHEMMA automatic bandsaw HMI: https://www.sthemma.com/Automatic-Bandsaw-AUTOMATIC-DIGITAL-BANDSAW-SUPER-TRAD-370-AO-CN-EVOLUTION_2,1,20,19/ — programmable piece counter, error notifications
- Industrial Monitor Direct: https://industrialmonitordirect.com/blogs/knowledgebase/design-patterns-for-process-vs-safety-interlocks-in-plc-systems — parameter locking during active cycle, interlock display colors
- ISA-101 HMI standard summary: https://www.iotindustries.sk/en/blog/isa-101/ — counter display with adjacent numeric value, state indicator color conventions
- Machinery Safety 101: https://machinerysafety101.com/2021/06/02/manual-reset-using-an-hmi/ — RESET via HMI acceptable for non-safety-critical process reset (bit 20.14 is process reset, not safety reset)

---

*Feature research for: v2.1 Otomatik Kesim Sayfası — PLC-integrated automatic cutting GUI page*
*Researched: 2026-04-08*
