# Phase 26: OtomatikKesimController - Research

**Researched:** 2026-04-09
**Domain:** PySide6 GUI widget, MachineControl integration, QTimer polling, ML mode sync
**Confidence:** HIGH

## Summary

Phase 26 creates OtomatikKesimController -- a full-page QWidget subclass following the exact conventions of all existing page controllers (PositioningController, ControlPanelController). The MachineControl backend for all auto-cutting operations was completed in Phase 25 and is fully verified. The NumpadDialog, TouchButton, and ControlMode enum are all already in production and ready to reuse. The only new code required is the page widget itself plus an allow_decimal addition to NumpadDialog.

All integration points confirmed by direct codebase inspection: MachineControl auto cutting methods at lines 596-637 of machine_control.py, TouchButton signals touch_pressed/touch_released plus standard pressed/released, and the NumpadDialog exec() pattern in control_panel_controller.py lines 1558-1590. The stop_timers() contract is mandatory for every page controller.

**Primary recommendation:** Create src/gui/controllers/otomatik_kesim_controller.py as a QWidget subclass following the PositioningController structural template. Add allow_decimal to NumpadDialog. Wire D2056 polling via 500ms QTimer with _previous_count comparison for ML state reset detection.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Sol-Sag iki sutun layout. Sol sutun: parametre alanlari. Sag sutun: sayac gosterimi (ust) + kontrol butonlari (alt).
- D-02: P ve X yan yana (ust satir), aralarinda/altlarinda PxX toplam etiketi. L, C, S alt kisimda tek sutun dikey sirali.
- D-03: Sag sutun ust bolumunde buyuk sayac gosterimi "X / Y" formatinda + yatay gradient progress bar. Alt bolumunde START, RESET, IPTAL + ML modu butonlari.
- D-04: Tum parametre alanlarina dokunuldugunda NumpadDialog acilir. NumpadDialog(parent, initial_value=str) kullanimi.
- D-05: NumpadDialog a allow_decimal=True parametresi eklenir. True oldugunda "." butonu gorunur (L alani icin). Mevcut tamsayi davranisi varsayilan olarak korunur.
- D-06: Deger araliklarip P 1-9999 tamsayi, L 1-99999 mm ondalikli (0.1mm hassasiyet), X 1-999 tamsayi. C ve S: 0-500 m/dk.
- D-07: C ve S parametreleri MachineControl.write_cutting_speed() ve MachineControl.write_descent_speed() ile yazilir.
- D-08: PxX toplam etiketi "Toplam: {PxX} adet" formatinda, P veya X degistiginde anlik guncellenir.
- D-09: START butonu: Once _validate_params() calisir. Hata varsa START altinda kirmizi Turkce uyari mesaji (3 saniye). Gecerliyse start_auto_cutting() cagrilir.
- D-10: Aktif kesim sirasinda START devre disi olur, metni "DEVAM EDIYOR..." olarak degisir. RESET ve IPTAL aktif kalir.
- D-11: RESET butonu: TouchButton. 1500ms basili tutma. Sol->sag doluluk animasyonu. Erken birakilirsa animasyon sifirlanir. Suredolunca reset_auto_cutting(True), birakilinca reset_auto_cutting(False).
- D-12: IPTAL butonu: cancel_auto_cutting() cagrilir. Parametre alanlari tekrar aktif, sayac/progress sifirlanir.
- D-13: Sayac 500ms QTimer ile D2056 dan okunur (read_kesilmis_adet()). Format: "X / Y".
- D-14: Aktif kesim sirasinda (D2056 > 0 ve hedef asilmamis) P, L, X, C, S alanlari setEnabled(False).
- D-15: Hedef adede ulasildiginda sayac ve progress bar yesile doner, "Tamamlandi!" mesaji. Parametreler tekrar aktif.
- D-16: Manual/AI buton cifti (iki toggle buton), kontrol panelindeki ayni pattern.
- D-17: Sayfa acildiginda mevcut mod control_manager dan okunarak butonlar senkronize edilir. Iki yonlu senkron: ayni set_mode() cagrisi.
- D-18: Her yeni kesim baslangiicinda ML state sifirlanir. D2056 degisiminde ML state reset tetiklenir.

### Claude Discretion Areas
- Sayfa widget sinif yapisi ve ic metod organizasyonu
- Frame boyutlari ve koordinatlari (1528x1080 icerik alanina uygun)
- Gradient renkleri ve font boyutlari (mevcut tema ile tutarli)
- Hata mesaji timeout mekanizmasi (QTimer veya QPropertyAnimation)
- RESET progress animasyonunun implementasyon detayi (QPainter overlay veya style sheet)
- D2056 degisim algilama mekanizmasi (onceki deger karsilastirmasi)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PARAM-01 | Kullanici P (hedef adet) degerini girebilir | NumpadDialog integer 1-9999; mousePressEvent on P frame -> exec() -> get_value() |
| PARAM-02 | Kullanici L (uzunluk mm, ondalikli) degerini girebilir | NumpadDialog with allow_decimal=True; value parsed as float |
| PARAM-03 | Kullanici C (kesim hizi m/dk) degerini girebilir | NumpadDialog integer 0-500; write_cutting_speed() |
| PARAM-04 | Kullanici S (inme hizi m/dk) degerini girebilir | NumpadDialog integer 0-500; write_descent_speed() |
| PARAM-05 | Kullanici X (paketteki adet) degerini girebilir | NumpadDialog integer 1-999; triggers PxX recalculation |
| GUI-02 | Aktif kesim sirasinda parametre giris alanlari devre disi kalir | D2056 > 0 -> setEnabled(False) on all 5 frames; re-enabled on cancel/complete |
| GUI-03 | Kesilmis adet sayisi sayfada gercek zamanli goruntulenir | 500ms QTimer -> read_kesilmis_adet() -> "X / Y" label + progress bar |
| ML-01 | Kullanici ML kesim modunu etkinlestirebilir | Manual/AI toggle buttons; asyncio.run_coroutine_threadsafe(control_manager.set_mode()) |
| ML-02 | Seri kesimde her yeni kesim basladiginda ML state sifirlanir | D2056 polling: compare vs _previous_count; on change -> set_mode(ML) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | 6.9.2 | Qt GUI framework | Project-wide, all controllers use it [VERIFIED: pip show PySide6] |
| Python | 3.13.12 | Runtime | Project runtime [VERIFIED: python3 --version] |
| pytest | 9.0.2 | Test execution | Project standard [VERIFIED: pip show pytest] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| QTimer (PySide6.QtCore) | bundled | 500ms D2056 polling + 3s error timeout | Counter polling + validation error auto-hide |
| asyncio (stdlib) | bundled | run_coroutine_threadsafe for ML mode switch | control_manager.set_mode() is a coroutine |

No new external packages required. All libraries already in project dependencies.

## Architecture Patterns

### Recommended Project Structure

New files:
  src/gui/controllers/otomatik_kesim_controller.py  (NEW)
  tests/test_otomatik_kesim_controller.py           (NEW)

Modified files:
  src/gui/numpad.py  (MODIFY: add allow_decimal parameter)

### Pattern 1: Page Controller Class Template
What: Every page is a QWidget subclass with control_manager, data_pipeline, event_loop constructor params.
Timers are children of self (Qt auto-cleanup). stop_timers() method required by MainController.closeEvent.
Source: src/gui/controllers/positioning_controller.py lines 41-79 [VERIFIED]

```python
class OtomatikKesimController(QWidget):
    def __init__(self, control_manager=None, data_pipeline=None, parent=None, event_loop=None):
        super().__init__(parent)
        self.control_manager = control_manager
        self.data_pipeline = data_pipeline
        self.event_loop = event_loop
        self.machine_control = MachineControl()
        self._setup_ui()
        self._setup_timers()

    def stop_timers(self):
        if hasattr(self, '_polling_timer') and self._polling_timer:
            self._polling_timer.stop()
        if hasattr(self, '_reset_tick_timer') and self._reset_tick_timer:
            self._reset_tick_timer.stop()
```

### Pattern 2: NumpadDialog Frame Click
What: Assign frame.mousePressEvent = handler. Handler creates NumpadDialog, calls exec(), on Accepted calls get_value().
Source: src/gui/controllers/control_panel_controller.py lines 1558-1590 [VERIFIED]

```python
def _handle_p_frame_click(self, event=None):
    if not self._params_enabled:
        return  # guard: setEnabled(False) does not block Python mousePressEvent override
    if event:
        event.accept()
    initial_str = self._p_value if self._p_value else ''
    dialog = NumpadDialog(self, initial_value=initial_str)
    result = dialog.exec()
    if result == QDialog.Accepted:
        value_str = dialog.get_value()
        try:
            value = int(value_str) if value_str else 0
        except Exception:
            value = 0
        value = max(1, min(9999, value))
        self._p_value = str(value)
        self.labelP.setText(str(value))
        self._update_total_label()
```

### Pattern 3: allow_decimal Extension to NumpadDialog
What: Add allow_decimal=False param to NumpadDialog.__init__. Pre-build decimal button in Ui_Dialog,
hide by default, show when allow_decimal=True. Use show()/hide() to avoid geometry shifts.
Source: src/gui/numpad.py line 192 [VERIFIED -- current: def __init__(self, parent=None, initial_value='')]

```python
# NumpadDialog.__init__ signature change:
def __init__(self, parent=None, initial_value='', allow_decimal=False):
    # ... existing init ...
    if allow_decimal:
        self.ui.decimalButton.show()
    else:
        self.ui.decimalButton.hide()

# add_digit guard:
def add_digit(self, digit):
    if digit == '.' and '.' in self.value:
        return  # prevent double decimal
    # ... rest unchanged
```

### Pattern 4: TouchButton Hold-Delay for RESET (1500ms)
What: Connect all 4 signals. On press: record time, start 50ms tick timer. On tick: update progress, check elapsed.
On timeout: call reset_auto_cutting(True). On release before timeout: call reset_auto_cutting(False), stop timer.
Source: src/gui/widgets/touch_button.py lines 47-48 [VERIFIED signals] + D-11 [VERIFIED decision]

```python
self.btnReset.pressed.connect(self._on_reset_press)
self.btnReset.released.connect(self._on_reset_release)
self.btnReset.touch_pressed.connect(self._on_reset_press)
self.btnReset.touch_released.connect(self._on_reset_release)

def _on_reset_press(self):
    if self._reset_in_progress:
        return  # guard against double-fire (pressed + touch_pressed both fire on touchscreen)
    self._reset_in_progress = True
    self._reset_start = time.monotonic()
    self._reset_tick_timer.start(50)

def _on_reset_release(self):
    if not self._reset_in_progress:
        return
    self._reset_tick_timer.stop()
    elapsed = time.monotonic() - self._reset_start
    if elapsed < 1.5:
        self.machine_control.reset_auto_cutting(False)
    self._reset_in_progress = False
    self._reset_progress = 0.0
    self.btnReset.update()

def _on_reset_tick(self):
    elapsed = time.monotonic() - self._reset_start
    self._reset_progress = min(1.0, elapsed / 1.5)
    self.btnReset.update()
    if elapsed >= 1.5:
        self._reset_tick_timer.stop()
        self.machine_control.reset_auto_cutting(True)
```

### Pattern 5: D2056 Polling with ML State Reset Detection
What: 500ms QTimer. Read count, update UI, detect new-cut transition via _previous_count comparison.
Source: D-13, D-14, D-18 decisions [VERIFIED] + project QTimer patterns [VERIFIED]

```python
def _on_polling_timer(self):
    count = self.machine_control.read_kesilmis_adet()
    if count is None:
        return
    target = self._get_target()  # p_val * x_val; 0 if not set

    # ML state reset: detect new cut starting (count decreased = PLC reset counter)
    if self._previous_count is not None and self._previous_count != count:
        if count > 0 and count < self._previous_count:
            self._trigger_ml_state_reset()
    self._previous_count = count

    self.labelCounter.setText(f'{count} / {target}')
    progress = min(1.0, count / target) if target > 0 else 0.0
    self._update_progress_bar(progress)

    if target > 0 and count >= target:
        self._on_cutting_complete()
        return

    cutting_active = (count > 0)
    self._set_params_enabled(not cutting_active)

def _trigger_ml_state_reset(self):
    if self.control_manager and self.event_loop:
        from src.domain.enums import ControlMode
        asyncio.run_coroutine_threadsafe(
            self.control_manager.set_mode(ControlMode.ML), self.event_loop
        )
```

### Pattern 6: ML Mode Toggle (Two-Way Sync)
What: Two checkable QPushButtons. Click calls asyncio.run_coroutine_threadsafe(control_manager.set_mode()).
On page load, read current mode and sync button states.
Source: src/gui/controllers/control_panel_controller.py lines 1397-1438 [VERIFIED]

```python
import asyncio
from src.domain.enums import ControlMode

def _switch_to_mode(self, mode):
    self.btnManual.setChecked(mode == ControlMode.MANUAL)
    self.btnAI.setChecked(mode == ControlMode.ML)
    if self.control_manager and self.event_loop:
        asyncio.run_coroutine_threadsafe(
            self.control_manager.set_mode(mode), self.event_loop
        )
```

### Pattern 7: Absolute Coordinate Layout
What: All widgets via QFrame.setGeometry(x, y, w, h). No QLayout managers.
Source: Entire positioning_controller.py [VERIFIED]

Coordinate reference (1528x1080 content area):
  Full page: 0, 0, 1528, 1080
  Left column (params): x~30, width~700
  Right column (counter + buttons): x~760, width~740
  Top padding: y~30

### Anti-Patterns to Avoid
- Using QLayout: Project uses absolute coordinates exclusively. Never mix.
- Connecting only mouse signals on RESET: All 4 TouchButton signals required for factory touchscreen.
- Not implementing stop_timers(): MainController.closeEvent calls it on each page.
- Direct async call from GUI thread: control_manager.set_mode() needs run_coroutine_threadsafe.
- Not releasing bit 20.14: reset_auto_cutting(True) without subsequent False leaves bit permanently set.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Touch hold button | Custom QEvent filter | TouchButton widget | Handles touch/mouse duality, bounds checking, multi-touch exclusion |
| Numeric touch keyboard | Custom QDialog | NumpadDialog with allow_decimal | Production-tested, styled to match theme |
| ML mode switching | Direct attribute set | control_manager.set_mode() via run_coroutine_threadsafe | Thread-safe; consistent state across all pages |
| PLC register operations | Direct pymodbus calls | MachineControl methods | Singleton with reconnect logic and cooldown |

Key insight: All low-level operations are abstracted. Phase 26 is purely GUI composition.

## Common Pitfalls

### Pitfall 1: Double-fire on RESET (pressed + touch_pressed both fire on touchscreen)
What goes wrong: Both pressed and touch_pressed fire, starting two concurrent hold timers.
Root cause: TouchButton emits both touch signals AND the system synthesizes mouse events.
How to avoid: Guard with self._reset_in_progress flag. Set True on first press, clear on release.
Warning signs: reset_auto_cutting called twice in logs within 1ms.

### Pitfall 2: setEnabled(False) on QFrame does not block Python mousePressEvent override
What goes wrong: frame.mousePressEvent = handler bypasses Qt enabled/disabled state. NumpadDialog opens during active cutting.
Root cause: Python attribute assignment is not intercepted by Qt widget event machinery.
How to avoid: Add "if not self._params_enabled: return" guard at top of every frame click handler.
Warning signs: NumpadDialog opens during active cutting.

### Pitfall 3: QTimer not stopped in stop_timers()
What goes wrong: On Linux, QTimer destroyed from non-GUI thread causes segfault.
Root cause: MainController.closeEvent calls stop_timers() for listed pages -- Phase 27 must add this page.
How to avoid: Implement stop_timers() stopping both _polling_timer and _reset_tick_timer. Phase 27 must register this page in closeEvent.
Warning signs: Crash on app exit with "Timers cannot be stopped from another thread".

### Pitfall 4: ML state reset spuriously triggers on page open mid-cut
What goes wrong: _previous_count=0 at init. First poll returns N>0, looks like new cut.
Root cause: Initialization assumption that 0 = no cut is wrong if cut was already in progress.
How to avoid: Initialize _previous_count = None. On first poll, set without triggering reset.
Warning signs: ML mode resets when navigating to page while cut in progress.

### Pitfall 5: allow_decimal button geometry breaks existing numpad layout
What goes wrong: Adding "." button in bottom row shifts geometry, breaks integer-mode tests.
Root cause: Current bottom row [backspace][0][enter] has fixed geometry.
How to avoid: Pre-build decimal button in Ui_Dialog, hidden by default. Use show()/hide() only.
Warning signs: Integer-mode tests pass but decimal-mode has button overlap visually.

### Pitfall 6: Parameters not written to PLC before start_auto_cutting()
What goes wrong: start_auto_cutting() fires but PLC registers have stale values from previous run.
Root cause: Parameter frames only write to PLC on NumpadDialog acceptance. PLC may have been reset.
How to avoid: In _handle_start_click, after validation: call write_target_adet(p, x), write_target_uzunluk(l_mm), optional speed writes, THEN start_auto_cutting().
Warning signs: PLC cuts wrong quantity or length.

## Code Examples

### MachineControl Auto Cutting API (machine_control.py lines 596-637 [VERIFIED])
```python
machine_control.write_target_adet(p, x)       # writes P*X to D2050 (Word)
machine_control.write_target_uzunluk(l_mm)     # writes L*10 to D2064 (Double Word)
machine_control.start_auto_cutting()           # sets bit 20.13 (fire-and-forget)
machine_control.reset_auto_cutting(True)       # sets bit 20.14 (hold)
machine_control.reset_auto_cutting(False)      # clears bit 20.14 (release)
machine_control.cancel_auto_cutting()          # sets bit 20.4
machine_control.read_kesilmis_adet()           # reads D2056 -> Optional[int]
machine_control.write_cutting_speed(v)         # writes integer to register 2066
machine_control.write_descent_speed(v)         # writes v*100 to register 2041
```

### START Click Handler (D-09 + Pitfall 6)
```python
def _handle_start_click(self):
    error = self._validate_params()
    if error:
        self._show_validation_error(error)
        return
    p = int(self._p_value)
    x = int(self._x_value)
    l_mm = float(self._l_value)
    self.machine_control.write_target_adet(p, x)
    self.machine_control.write_target_uzunluk(l_mm)
    if self._c_value:
        self.machine_control.write_cutting_speed(int(self._c_value))
    if self._s_value:
        self.machine_control.write_descent_speed(float(self._s_value))
    self.machine_control.start_auto_cutting()
    self.btnStart.setEnabled(False)
    self.btnStart.setText('DEVAM EDIYOR...')
```

### Validation (D-09 [VERIFIED decision])
```python
def _validate_params(self):
    # Returns error string or None if valid
    if not self._p_value or int(self._p_value) <= 0:
        return 'P (hedef adet) girilmedi'
    if not self._l_value or float(self._l_value) <= 0:
        return 'L (uzunluk) girilmedi'
    if not self._x_value or int(self._x_value) <= 0:
        return 'X (paketteki adet) girilmedi'
    return None
```

### Error Message Auto-Hide [ASSUMED -- QTimer approach]
```python
def _show_validation_error(self, message):
    self.labelValidationError.setText(message)
    self.labelValidationError.setVisible(True)
    QTimer.singleShot(3000, lambda: self.labelValidationError.setVisible(False))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct pymodbus from GUI | MachineControl singleton | Phase 25 | All PLC writes go through one class with reconnect logic |
| Boolean checkbox for ML | Two toggle QPushButtons | Project design | Matches visual design of existing control panel |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | _validate_params() returns string or None | Code Examples | Low -- planner can choose return type |
| A2 | Error auto-hide uses QTimer.singleShot(3000) | Code Examples | Low -- QPropertyAnimation equally valid |
| A3 | RESET animation uses float progress + QPainter update() | Pattern 4 | Low -- stylesheet approach also viable |
| A4 | _previous_count = None initialization for ML reset detection | Pattern 5 | Medium -- wrong init causes spurious ML reset on page open mid-cut |
| A5 | ML state reset achieved by re-calling set_mode(ML) | Pattern 5/6 | Medium -- confirmed by CONTEXT.md specifics |
| A6 | Phase 27 will add OtomatikKesimController to MainController.closeEvent page list | Pitfall 3 | Medium -- without this, timer cleanup skipped on app exit |

## Open Questions

1. D2056 active cutting detection boundary
   - What we know: D-14 says D2056 > 0 and hedef asilmamis disables params.
   - What is unclear: Does D2056 read 0 between consecutive cuts, or hold last value?
   - Recommendation: Treat "active" as 0 < count < target. count >= target = complete. count == 0 = idle.

2. RESET hold duration: 1500ms unverified with PLC engineer
   - What we know: 1500ms per D-11. STATE.md flags this as unverified.
   - Recommendation: Implement 1500ms. If hardware requires different timing, only the constant changes.

3. ML state reset: set_mode(ML) vs separate reset method
   - What we know: CONTEXT.md specifics confirm set_mode() approach.
   - What is unclear: Whether re-calling set_mode(ML) when already in ML mode resets state or is no-op.
   - Recommendation: Use set_mode(ControlMode.ML). If it is a no-op, planner must investigate control_manager.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | Runtime | Yes | 3.13.12 | -- |
| PySide6 | GUI framework | Yes | 6.9.2 | -- |
| pytest | Test execution | Yes | 9.0.2 | -- |
| MachineControl | PLC operations | Yes (Phase 25) | production | -- |
| TouchButton | RESET button | Yes | production | -- |
| NumpadDialog | Parameter input | Yes | production | -- |

No missing dependencies. All tools available.

## Validation Architecture

workflow.nyquist_validation key absent from config.json -- treated as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml (dev deps: pytest>=7.4.0) |
| Quick run command | pytest tests/test_otomatik_kesim_controller.py -x |
| Full suite command | pytest tests/ -x |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PARAM-01 | P frame click -> NumpadDialog -> value stored + label updated + total recalc | unit (mock dialog) | pytest tests/test_otomatik_kesim_controller.py::test_param_p_accepted -x | No -- Wave 0 |
| PARAM-02 | L frame click with allow_decimal -> float value stored | unit | pytest tests/test_otomatik_kesim_controller.py::test_param_l_decimal -x | No -- Wave 0 |
| PARAM-03 | C frame click -> write_cutting_speed() called | unit (mock MC) | pytest tests/test_otomatik_kesim_controller.py::test_param_c_writes_speed -x | No -- Wave 0 |
| PARAM-04 | S frame click -> write_descent_speed() called | unit (mock MC) | pytest tests/test_otomatik_kesim_controller.py::test_param_s_writes_speed -x | No -- Wave 0 |
| PARAM-05 | X change -> PxX label recalculated | unit | pytest tests/test_otomatik_kesim_controller.py::test_total_label_recalc -x | No -- Wave 0 |
| GUI-02 | D2056 > 0 and < target -> setEnabled(False) on 5 frames | unit | pytest tests/test_otomatik_kesim_controller.py::test_params_disabled_during_cut -x | No -- Wave 0 |
| GUI-03 | Polling returns count -> label shows count / target | unit | pytest tests/test_otomatik_kesim_controller.py::test_counter_label_format -x | No -- Wave 0 |
| ML-01 | AI button click -> set_mode(ML) scheduled | unit (mock event_loop) | pytest tests/test_otomatik_kesim_controller.py::test_ml_mode_toggle -x | No -- Wave 0 |
| ML-02 | D2056 count decreases -> ML state reset triggered | unit | pytest tests/test_otomatik_kesim_controller.py::test_ml_reset_on_new_cut -x | No -- Wave 0 |
| D-05 | NumpadDialog allow_decimal=True shows decimal button | unit | pytest tests/test_otomatik_kesim_controller.py::test_numpad_allow_decimal -x | No -- Wave 0 |
| D-09 | _validate_params missing P/L/X returns error string | unit | pytest tests/test_otomatik_kesim_controller.py::test_validate_params_errors -x | No -- Wave 0 |

### Sampling Rate
- Per task commit: pytest tests/test_otomatik_kesim_controller.py -x
- Per wave merge: pytest tests/ -x
- Phase gate: Full suite green before /gsd-verify-work

### Wave 0 Gaps
- [ ] tests/test_otomatik_kesim_controller.py -- covers all Phase 26 requirements
- [ ] No new conftest.py needed (per-file fixtures match existing pattern)
- [ ] No new framework install needed

## Security Domain

This phase is a local industrial HMI application on a closed factory LAN with no network-facing endpoints, no authentication surfaces, and no external data ingestion. No ASVS categories apply to this GUI widget phase.

## Sources

### Primary (HIGH confidence)
- src/services/control/machine_control.py -- All MachineControl auto cutting methods [VERIFIED: codebase]
- src/gui/numpad.py -- NumpadDialog class, exec() flow, get_value(), current lack of decimal [VERIFIED: codebase]
- src/gui/widgets/touch_button.py -- TouchButton signals and event handling [VERIFIED: codebase]
- src/gui/controllers/control_panel_controller.py -- NumpadDialog usage, ML mode toggle, _switch_controller [VERIFIED: codebase]
- src/gui/controllers/main_controller.py -- Page structure, closeEvent stop_timers() contract [VERIFIED: codebase]
- src/gui/controllers/positioning_controller.py -- Page controller template, stop_timers() implementation [VERIFIED: codebase]
- src/domain/enums.py -- ControlMode enum (MANUAL, ML) [VERIFIED: codebase]
- pyproject.toml -- Python 3.10+, PySide6>=6.6.0, pytest>=7.4.0 [VERIFIED: codebase]
- tests/test_machine_control_auto_cutting.py -- Existing test patterns and mock structure [VERIFIED: codebase]

### Secondary (MEDIUM confidence)
- .planning/phases/26-otomatik-kesim-controller/26-CONTEXT.md -- All decisions D-01 through D-18 [VERIFIED: user decisions]
- .planning/STATE.md -- Open verification items for RESET hold duration and D2056 word order [VERIFIED: project state]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries verified in codebase and runtime
- Architecture: HIGH -- all patterns verified from production code
- Pitfalls: HIGH -- identified from concrete code inspection

**Research date:** 2026-04-09
**Valid until:** 2026-05-09 (stable project, no fast-moving external dependencies)
