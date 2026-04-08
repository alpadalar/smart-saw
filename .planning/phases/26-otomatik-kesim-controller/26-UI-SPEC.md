---
phase: 26
phase_name: otomatik-kesim-controller
status: draft
created: 2026-04-09
tool: none
registry: not_applicable
---

# UI-SPEC: Phase 26 — OtomatikKesimController

## Design System

**Tool:** None (PySide6 Qt stylesheet system — project-wide standard)
**Component Library:** PySide6 6.9.2 (QWidget, QFrame, QPushButton, QLabel, QTimer)
**Custom Widgets in Use:**
- `TouchButton` — `src/gui/widgets/touch_button.py` (RESET hold-delay)
- `NumpadDialog` — `src/gui/numpad.py` (parameter input; modified with `allow_decimal`)
**Design token source:** Verified from `src/gui/controllers/control_panel_controller.py` and `positioning_controller.py`

---

## Spacing

**Scale:** 8-point base, multiples of 4px only.

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Inner label padding |
| sm | 8px | Gap between sibling labels |
| md | 16px | Gap between param fields vertically |
| lg | 24px | Frame top/left padding (matches existing `27px` left margins) |
| xl | 32px | Section gap (between param group and counter area) |
| 2xl | 48px | Frame top margin from page edge (matches existing `y=30` origin) |

**Page canvas:** 1528 × 1080 px (absolute coordinate layout — no QLayout managers).
**Touch target minimum:** 55px height for all interactive buttons (matches existing `55px` button heights in control_panel_controller).

**Source:** Verified from control_panel_controller.py absolute geometries (e.g., `QFrame(33, 127, 440, 344)`, button height `55px`).

---

## Typography

**Font family:** `Plus Jakarta Sans` (project-wide, verified across all controllers)
**Rendering:** Qt stylesheet `font-family: 'Plus Jakarta Sans'`

| Role | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Counter display | 80px | bold (700) | 1.0 | "X / Y" kesilmiş adet counter |
| Frame title / param value | 24px | bold (700) | 1.2 | Section headers (P/X Parametreleri, Sayaç, Kontrol); current entered value inside each param frame |
| Button label / body / validation error | 20px | bold (700) or medium (500) | 1.2 body; 1.3 error | START, RESET, İPTAL, Manuel, Yapay Zeka (bold); sub-labels and hints (medium); inline validation error below START (bold, `#DC2626`) |
| Small / unit | 16px | medium (500) | 1.3 | Unit labels (adet, mm, m/dk), "Toplam:" label, range hints |

**Weights declared:** bold (700) and medium (500) only.

**Typography notes:**
- Validation error (formerly 18px) is rendered at 20px bold `#DC2626` at line-height 1.3. The semantic-error color provides the visual urgency previously carried by the larger size; no separate size entry is needed.
- Parameter value display (formerly 48px) is rendered at 24px bold `#F4F6FC`. Param frames are touch targets (min 140px height) so a 24px value label is comfortably legible at arm's length. The 80px size is reserved exclusively for the counter display in the right column.
- The 14px "Log / detail" role is removed. No component in this phase uses secondary detail text at a size below the 16px unit-label role.

**Source:** Verified from control_panel_controller.py lines 676–1133. Typography fix applied per checker revision 2026-04-09.

---

## Color

**Theme:** Dark navy gradient. Verified from all existing page controllers.

### Palette

| Token | Hex | Role |
|-------|-----|------|
| `surface-primary` | `rgba(6, 11, 38, 240)` → `rgba(26, 31, 55, 0)` gradient | Page background (transparent over app bg) |
| `surface-frame` | `qlineargradient stop:0 rgba(6,11,38,240) stop:1 rgba(26,31,55,0)` | All QFrame backgrounds (`border-radius: 20px`) |
| `surface-nested` | same as surface-frame | Nested child frames |
| `text-primary` | `#F4F6FC` | All label and button text |
| `text-disabled` | `rgba(244, 246, 252, 100)` | Disabled parameter frame labels |
| `accent` | `#950952` (rgb 149, 9, 82) | Active/checked toggle states, scrollbar handle, progress fill |
| `accent-gradient` | `qlineargradient stop:0 rgba(149,9,82,255) stop:1 rgba(26,31,55,255)` | Checked button state |
| `button-default` | `qlineargradient stop:0 #000000 stop:0.38 rgba(26,31,55,200)` | Unchecked button background |
| `button-hover` | `rgba(255, 255, 255, 0.1)` | All button hover state |
| `button-disabled` | `rgba(26, 31, 55, 100)` | Disabled buttons |
| `border-default` | `#F4F6FC` at `2px` or `3px` solid | Button borders |
| `semantic-destructive` | `#DC2626` | İPTAL button (destructive action) |
| `semantic-destructive-hover` | `#B91C1C` | İPTAL hover |
| `semantic-destructive-pressed` | `#991B1B` | İPTAL pressed |
| `semantic-success` | `#22C55E` | Counter and progress bar when target reached (Tamamlandı state) |
| `semantic-error` | `#DC2626` | Validation error label text |

**60/30/10 split:**
- 60% dominant: transparent page background over app's navy gradient
- 30% secondary: `surface-frame` gradient applied to all QFrames (param frames, counter frame, control frame)
- 10% accent: `#950952` reserved for — checked ML mode button, RESET hold progress fill, scrollbar handle, active page sidebar icon

**Accent reserved for:**
1. Checked state of Manual/AI mode toggle buttons
2. RESET hold-progress animation fill (QPainter overlay, left→right)
3. Progress bar fill during active cutting (before completion)
4. Scrollbar handles within any scroll areas

**Source:** Verified from control_panel_controller.py lines 650–726, positioning_controller.py lines 116–188, positioning_controller.py lines 358–384.

---

## Layout

**Pattern:** Absolute coordinate geometry (QFrame.setGeometry). No QLayout managers.
**Page size:** 1528 × 1080 px.

### Two-Column Structure

```
+--------------------------------------------------+
|  [Left Column x=30, w=700]  |  [Right Column x=760, w=740]  |
|                              |                               |
|  PARAM FRAMES (top)          |  COUNTER FRAME (top)          |
|  - P + X row (top)           |    "X / Y" large counter      |
|  - P×X total label           |    Horizontal progress bar    |
|  - L (full-width)            |                               |
|  - C (full-width)            |  CONTROL FRAME (bottom)       |
|  - S (full-width)            |    START / RESET / İPTAL      |
|                              |    Manuel / Yapay Zeka        |
+--------------------------------------------------+
```

**Coordinate grid (reference):**

| Area | x | y | w | h |
|------|---|---|---|---|
| Left column origin | 30 | 30 | 700 | — |
| P frame | 30 | 30 | 340 | 160 |
| X frame | 380 | 30 | 340 | 160 |
| P×X total label | 30 | 200 | 690 | 40 |
| L frame | 30 | 255 | 690 | 140 |
| C frame | 30 | 410 | 690 | 140 |
| S frame | 30 | 565 | 690 | 140 |
| Right column origin | 760 | 30 | 740 | — |
| Counter frame | 760 | 30 | 740 | 380 |
| Control frame | 760 | 425 | 740 | 625 |

All coordinates are Claude's discretion (per CONTEXT.md) — must fit within 1528×1080.

---

## Components

### Param Frame (×5: P, X, L, C, S)

| Property | Spec |
|----------|------|
| Widget | `QFrame` with gradient background, `border-radius: 20px` |
| Cursor | `Qt.PointingHandCursor` |
| Click target | `frame.mousePressEvent` override |
| Guard | `if not self._params_enabled: return` at top of handler |
| Disabled state | `background: rgba(26, 31, 55, 100)`, text `rgba(244, 246, 252, 100)` |
| Title label | Frame name + unit in `()`, 24px bold `#F4F6FC` |
| Value label | Current value, 24px bold `#F4F6FC`, default "—" when empty |

### NumpadDialog (parameter input)

| Property | Spec |
|----------|------|
| Source | `src/gui/numpad.py` |
| Signature | `NumpadDialog(parent, initial_value=str, allow_decimal=False)` |
| L field | `allow_decimal=True` |
| P, X, C, S fields | `allow_decimal=False` (default) |
| Decimal button | Pre-built in UI, `show()`/`hide()` only — no geometry change |
| Double-decimal guard | `if digit == '.' and '.' in self.value: return` |

### P×X Total Label

| Property | Spec |
|----------|------|
| Format | `"Toplam: {P × X} adet"` |
| Font | 16px medium `#F4F6FC` |
| Update trigger | On every P or X NumpadDialog acceptance |

### Counter Frame (right column top)

| Property | Spec |
|----------|------|
| Counter label | `"{count} / {target}"` format, 80px bold `#F4F6FC` |
| Progress bar | Horizontal custom-painted `QWidget`, height 24px, `border-radius: 12px` |
| Progress fill — active | `#950952` accent, left→right |
| Progress fill — complete | `#22C55E` semantic-success |
| Progress background | `rgba(26, 31, 55, 200)` |
| Empty/idle state | Counter shows `"0 / 0"`, progress bar empty |

### RESET Button Hold Animation

| Property | Spec |
|----------|------|
| Widget | `TouchButton` from `src/gui/widgets/touch_button.py` |
| Hold duration | 1500ms |
| Animation | QPainter overlay: fills button left→right using `#950952` at `alpha=120` |
| Progress update | 50ms tick timer, `self._reset_progress` float 0.0→1.0 |
| Cancel | Early release → `_reset_progress = 0.0`, `btnReset.update()` |
| Complete | At 1.0 → `reset_auto_cutting(True)` |
| Release after complete | `reset_auto_cutting(False)` |
| Double-fire guard | `self._reset_in_progress` flag prevents pressed + touch_pressed double-start |

### START Button

| Property | Spec |
|----------|------|
| Default text | `"START"` |
| Active cutting text | `"DEVAM EDİYOR..."` |
| Disabled style | `button-disabled` token, `setEnabled(False)` |
| Size | 160px × 80px minimum |
| Font | 20px bold |

### İPTAL Button

| Property | Spec |
|----------|------|
| Background | `#DC2626` semantic-destructive |
| Hover | `#B91C1C` |
| Pressed | `#991B1B` |
| Font | 20px bold `#FFFFFF` |
| Action | `cancel_auto_cutting()` → re-enable params → reset counter display → empty progress bar |

### ML Mode Toggle Pair

| Property | Spec |
|----------|------|
| Widget | Two `QPushButton`, both `setCheckable(True)` |
| Labels | `"Manuel"` and `"Yapay Zeka"` |
| Default | `btnManual.setChecked(True)` (read from `control_manager` on page open) |
| Unchecked style | `button-default` gradient, `border: 2px solid #F4F6FC` |
| Checked style | `accent-gradient` |
| Hover style | `button-hover` |
| Size | 195px × 55px each |
| Source pattern | Mirrors `btnManualMode`/`btnAiMode` in control_panel_controller.py lines 750–790 |

---

## States

### Idle (no active cut)

- All 5 param frames enabled, `Qt.PointingHandCursor`
- Counter shows `"0 / 0"` or last-reset value
- Progress bar empty
- START enabled, text `"START"`
- RESET and İPTAL enabled (may be no-ops if no cut in progress)
- Validation error label hidden

### Active Cutting (D2056 > 0 and count < target)

- P, L, X, C, S frames `setEnabled(False)` — `rgba(26, 31, 55, 100)` bg, text fades
- Python handler guard `if not self._params_enabled: return` blocks NumpadDialog
- START disabled, text `"DEVAM EDİYOR..."`, button background `button-disabled`
- RESET and İPTAL remain enabled
- Counter updates every 500ms with `"{count} / {target}"`
- Progress bar fills with `#950952` proportionally

### Completed (count >= target)

- Counter label text stays `"{target} / {target}"`
- Counter label color transitions to `#22C55E`
- Progress bar fills to 100% with `#22C55E`
- Overlay label `"Tamamlandı!"` appears at 24px bold `#22C55E` below counter
- All 5 param frames re-enabled
- START re-enabled, text resets to `"START"`

### Validation Error (START clicked with missing P/L/X)

- Error label below START button becomes visible
- Text: Turkish error string (e.g., `"P (hedef adet) girilmedi"`)
- Color: `#DC2626` semantic-error
- Font: 20px bold
- Auto-hides after 3000ms via `QTimer.singleShot`

### RESET Hold Progress

- Overlay painted on `btnReset` surface: left→right fill `rgba(149, 9, 82, 120)`
- Button text remains `"RESET"` throughout
- On early release: overlay clears, button returns to default
- On completion: overlay fills 100%, then `reset_auto_cutting(True)` fires

---

## Copywriting

All text is Turkish, matching project-wide convention.

| Element | Copy |
|---------|------|
| Page title (sidebar) | `"Otomatik Kesim"` |
| P frame title | `"P — Hedef Adet"` |
| P frame hint | `"(1 - 9999)"` |
| X frame title | `"X — Paketteki Adet"` |
| X frame hint | `"(1 - 999)"` |
| P×X total label | `"Toplam: {P × X} adet"` |
| L frame title | `"L — Uzunluk (mm)"` |
| L frame hint | `"(1 - 99999, ondalıklı)"` |
| C frame title | `"C — Kesim Hızı (m/dk)"` |
| C frame hint | `"(0 - 500)"` |
| S frame title | `"S — İnme Hızı (m/dk)"` |
| S frame hint | `"(0 - 500)"` |
| Counter label | `"{kesilmiş} / {hedef}"` |
| Completion overlay | `"Tamamlandı!"` |
| START button — idle | `"START"` |
| START button — active | `"DEVAM EDİYOR..."` |
| RESET button | `"RESET"` |
| İPTAL button | `"İPTAL"` |
| ML Manuel button | `"Manuel"` |
| ML AI button | `"Yapay Zeka"` |
| Error — missing P | `"P (hedef adet) girilmedi"` |
| Error — missing L | `"L (uzunluk) girilmedi"` |
| Error — missing X | `"X (paketteki adet) girilmedi"` |
| Empty state (param frame, no value) | `"—"` (em dash, 24px bold) |

**Destructive action in this phase:** İPTAL. No separate confirmation dialog — action is recoverable (cut can be restarted). Visual differentiation via `#DC2626` background is sufficient per project pattern.

---

## Interaction Contracts

### Parameter Frame Click Flow

1. User taps param frame
2. Handler checks `if not self._params_enabled: return`
3. `NumpadDialog(parent, initial_value=current_str, allow_decimal=<L only>)` opens
4. On `Accepted`: validate range, clamp, update internal state, update value label, recalculate P×X
5. C and S additionally call `MachineControl.write_cutting_speed()` / `write_descent_speed()` immediately on accept
6. P and X do NOT write to PLC immediately — written in batch at START

### START Click Flow

1. `_validate_params()` — checks P > 0, L > 0, X > 0
2. If invalid: show error label, 3-second auto-hide, return
3. If valid: `write_target_adet(p, x)` → `write_target_uzunluk(l_mm)` → optional speed writes → `start_auto_cutting()`
4. `btnStart.setEnabled(False)`, `btnStart.setText("DEVAM EDİYOR...")`
5. Param frames disabled

### İPTAL Click Flow

1. `cancel_auto_cutting()` called
2. Param frames re-enabled
3. Counter display reset to `"0 / 0"`
4. Progress bar emptied
5. START re-enabled with `"START"` text

### D2056 Polling (500ms QTimer)

1. `read_kesilmis_adet()` returns `Optional[int]`
2. If `None`: skip update (connection issue)
3. ML reset detection: if `_previous_count is not None` and `count < _previous_count` and `count > 0`: trigger `_trigger_ml_state_reset()`
4. Update `labelCounter.setText(f'{count} / {target}')`
5. Update progress bar proportionally
6. If `count >= target > 0`: call `_on_cutting_complete()`
7. Otherwise: `_set_params_enabled(count == 0)` — idle (0) = enabled, active (>0 and <target) = disabled
8. Store `_previous_count = count`

### ML State Reset

1. Triggered when D2056 count decreases (new cut cycle started)
2. `asyncio.run_coroutine_threadsafe(control_manager.set_mode(ControlMode.ML), event_loop)`
3. Button states re-synced: `btnAI.setChecked(True)`, `btnManual.setChecked(False)`

---

## Registry

**shadcn:** Not applicable (PySide6 desktop application, not a web framework).
**Third-party registries:** None.
**Registry safety gate:** Not applicable.

---

## Accessibility

This is an industrial factory touchscreen HMI (local LAN, closed network). Standard web accessibility (WCAG) does not apply. Touch-target requirements:

- All interactive buttons: minimum 55px height (verified from existing controller patterns)
- RESET hold feedback: visual fill animation provides confirmation of hold progress
- Error messages: visible for 3 seconds minimum before auto-hide
- Disabled states: visually distinct opacity (text at `rgba(244,246,252,100)` = ~40% opacity)

---

## Pre-Population Audit

| Field | Source | Notes |
|-------|--------|-------|
| Two-column layout | CONTEXT.md D-01 | Locked decision |
| P/X row + L/C/S column | CONTEXT.md D-02 | Locked decision |
| Counter + progress + buttons in right column | CONTEXT.md D-03 | Locked decision |
| NumpadDialog pattern | CONTEXT.md D-04, RESEARCH.md Pattern 2 | Verified in codebase |
| allow_decimal parameter | CONTEXT.md D-05, RESEARCH.md Pattern 3 | Modification spec confirmed |
| Value ranges | CONTEXT.md D-06 | Locked decision |
| C/S write methods | CONTEXT.md D-07 | Locked decision |
| P×X total label format | CONTEXT.md D-08 | Locked decision |
| START validation + error display | CONTEXT.md D-09 | Locked decision |
| START disabled during cut | CONTEXT.md D-10 | Locked decision |
| RESET hold 1500ms + animation | CONTEXT.md D-11, RESEARCH.md Pattern 4 | Locked decision |
| İPTAL action + re-enable | CONTEXT.md D-12 | Locked decision |
| Counter polling 500ms | CONTEXT.md D-13 | Locked decision |
| Params disabled during cut | CONTEXT.md D-14 | Locked decision |
| Completion state (green) | CONTEXT.md D-15 | Locked decision |
| ML toggle pair | CONTEXT.md D-16 | Locked decision |
| ML two-way sync | CONTEXT.md D-17 | Locked decision |
| ML state reset on new cut | CONTEXT.md D-18 | Locked decision |
| Font: Plus Jakarta Sans | codebase scan | Verified across all controllers |
| Colors: #F4F6FC, #950952, #1A1F37 | codebase scan | Verified in control_panel, positioning, numpad |
| Frame style (gradient + border-radius 20px) | codebase scan | Verified in all page controllers |
| Button sizes (195×55px) | codebase scan (control_panel_controller.py line 751) | Verified |
| Error color #DC2626 | codebase scan (positioning_controller.py line 362) | Verified |
| Page canvas 1528×1080 | codebase scan (all controllers) | Verified |
| Absolute coordinate layout | RESEARCH.md Pattern 7 | Project-wide anti-pattern enforced |
| Success color #22C55E | Claude's discretion | Not yet used in codebase; standard green |
| Validation error copy (Turkish) | Claude's discretion | Consistent with Turkish UI convention |
| Counter display 80px | Claude's discretion (CONTEXT.md "büyük font") | Matches existing 80px speed value label |
| Typography collapsed to 4 sizes | Checker revision 2026-04-09 | Dropped 14px (unused), merged 18px→20px, merged 48px→24px |

---

*Phase: 26-otomatik-kesim-controller*
*UI-SPEC created: 2026-04-09*
*UI-SPEC revised: 2026-04-09 — typography collapsed from 7 to 4 sizes per checker*
*Status: draft — awaiting gsd-ui-checker validation*
