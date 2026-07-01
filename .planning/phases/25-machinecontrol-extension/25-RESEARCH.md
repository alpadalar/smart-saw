# Phase 25: MachineControl Extension - Research

**Researched:** 2026-04-09
**Domain:** pymodbus FC16 Double Word writes + MachineControl singleton extension
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 (Bit 20.4 Conflict):** Existing `CUTTING_STOP_BIT = 4` constant is preserved. `cancel_auto_cutting()` reuses this same constant. One stop/cancel bit on the PLC, one constant in code.
- **D-02 (Start Latch):** `start_auto_cutting()` sets bit 20.13 and releases (fire-and-forget). PLC clears the bit after acknowledging. No timer, delay, or pulse logic in MachineControl. Consistent with existing `start_cutting()` pattern.
- **D-03 (Double Word API):** A general-purpose `_write_double_word(register: int, value: int) -> bool` private method is added. Mitsubishi low-word-first convention: `low_word = value & 0xFFFF`, `high_word = (value >> 16) & 0xFFFF`. Call: `client.write_registers(address=register, values=[low_word, high_word])` (FC16). General-purpose despite single current use site (D2064).
- **D-04 (Class Organization):** All new additions go under a new `# Auto Cutting Control (Otomatik Kesim)` section, in this order:
  1. Register address constants: `TARGET_ADET_REGISTER = 2050`, `TARGET_LENGTH_REGISTER = 2064`, `CUT_COUNT_REGISTER = 2056`
  2. Bit position constants: `AUTO_CUTTING_START_BIT = 13`, `AUTO_CUTTING_RESET_BIT = 14`
  3. Public methods: `write_target_adet(p, x)`, `write_target_uzunluk(l_mm)`, `read_kesilmis_adet()`, `start_auto_cutting()`, `reset_auto_cutting(active)`, `cancel_auto_cutting()`

### Claude's Discretion

- Error logging detail level and exception handling pattern for new methods — must be consistent with existing `_write_register` / `_read_register` patterns
- `_ensure_connected()` call placement and error handling inside `_write_double_word` — Claude decides

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PLC-04 | MachineControl'a Double Word yazma desteği eklenir (write_registers FC16) | `_write_double_word` private method using `client.write_registers(address, [low, high])` — FC16 signature confirmed |
| PLC-01 | P×X hesaplanıp D2050'ye Word olarak yazılır | `write_target_adet(p, x)` delegates to `_write_register(TARGET_ADET_REGISTER, p*x)` — existing FC6 path |
| PLC-02 | L×10 değeri D2064'e Double Word olarak yazılır | `write_target_uzunluk(l_mm)` computes `int(l_mm * 10)`, delegates to `_write_double_word(TARGET_LENGTH_REGISTER, value)` |
| PLC-03 | D2056'dan kesilmiş adet periyodik olarak okunur | `read_kesilmis_adet()` delegates to `_read_register(CUT_COUNT_REGISTER)` — returns `Optional[int]` |
| CTRL-01 | START butonu Adres 20 Bit 13'ü set eder | `start_auto_cutting()` calls `_set_bit(CONTROL_REGISTER, AUTO_CUTTING_START_BIT, True)` |
| CTRL-02 | RESET butonu Adres 20 Bit 14'ü basılı tutma süresince set eder | `reset_auto_cutting(active: bool)` calls `_set_bit(CONTROL_REGISTER, AUTO_CUTTING_RESET_BIT, active)` |
| CTRL-03 | İPTAL butonu Adres 20 Bit 4'ü set eder | `cancel_auto_cutting()` calls `_set_bit(CONTROL_REGISTER, CUTTING_STOP_BIT, True)` — reuses existing constant |
</phase_requirements>

---

## Summary

Phase 25 is a pure Python code-extension phase: no new dependencies, no new files, no architectural change. All work is confined to a single class (`MachineControl`) in a single file (`src/services/control/machine_control.py`). The class already has all required infrastructure (`_write_register`, `_read_register`, `_set_bit`, `_ensure_connected`, `_write_register_atomic`) so every new method is a thin wrapper.

The only technically novel element is the `_write_double_word` private helper that uses pymodbus `write_registers()` (FC16) to write two consecutive 16-bit registers atomically. The Mitsubishi low-word-first convention means `[low_word, high_word]` maps to `[address, address+1]`, which is exactly what `write_registers(address=2064, values=[low, high])` produces. This was verified mathematically: L=1000mm → value=10000 (0x2710) → low_word=0x2710, high_word=0x0000, so D2064=0x2710 and D2065=0x0000.

A unit test file (`tests/test_machine_control_auto_cutting.py`) must be created as part of this phase to satisfy success criterion #5 (word-order verification test). The test infrastructure (pytest 9.0.2, `unittest.mock`) is already available and follows the pattern established in existing test files.

**Primary recommendation:** Add the new `# Auto Cutting Control` section at the bottom of the existing `# Speed Control` section, immediately before `# Status Methods`. Use `unittest.mock.MagicMock` to mock `ModbusTcpClient` for the unit test — the same pattern used by `test_camera_service.py`.

---

## Standard Stack

### Core (Already Installed — No New Dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pymodbus | 3.5.4 | Modbus TCP client | Already used throughout the project |
| threading | stdlib | Singleton lock | Already used in MachineControl |
| pytest | 9.0.2 | Unit testing | Already installed, used in tests/ |
| unittest.mock | stdlib | Mock Modbus client | Already used in test_camera_service.py |

[VERIFIED: `python -c "import pymodbus; print(pymodbus.__version__)"` → 3.5.4]
[VERIFIED: `python -m pytest --version` → pytest 9.0.2]

### pymodbus FC6 vs FC16

| Function Code | pymodbus Method | Writes | Use in This Phase |
|---------------|-----------------|--------|-------------------|
| FC6 (Write Single Register) | `client.write_register(address, value)` | 1 register | `write_target_adet` (D2050), existing bit ops |
| FC16 (Write Multiple Registers) | `client.write_registers(address, values=[...])` | N registers atomically | `_write_double_word` → D2064+D2065 |

[VERIFIED: `help(ModbusTcpClient.write_registers)` confirms signature `(self, address: int, values: Union[List[int], int], slave: int = 0, **kwargs)`]
[VERIFIED: `help(ModbusTcpClient.write_register)` confirms signature `(self, address: int, value: int, slave: int = 0, **kwargs)`]

---

## Architecture Patterns

### Existing MachineControl Structure (as-is)

```
class MachineControl:
    # Class-level register constants
    # Class-level bit position constants
    __new__ / __init__  (singleton + ModbusTcpClient setup)

    # Private infrastructure
    _should_attempt_connect()
    _ensure_connected()
    _read_register(register)
    _write_register(register, value)
    _set_bit(register, bit_position, value)
    _get_bit(register, bit_position)
    _write_register_atomic(register, set_bits, clear_bits)

    # === Vise Control (Mengene) ===
    # === Material Positioning (Malzeme Konumlandırma) ===
    # === Saw Positioning (Testere Konumlandırma) ===
    # === Cutting Control (Kesim Kontrol) ===
    # === Coolant Control (Soğutma Sıvısı) ===
    # === Chip Cleaning (Talaş Temizlik) ===
    # === Speed Control (Hız Kontrol) ===
    # === Status Methods ===
```

### Target Structure After Phase 25

The new section inserts between `# Speed Control` and `# Status Methods`:

```
    # === Speed Control (Hız Kontrol) ===
    CUTTING_SPEED_REGISTER = 2066
    DESCENT_SPEED_REGISTER = 2041
    write_cutting_speed / write_descent_speed / read_cutting_speed / read_descent_speed

    # ========================================================================
    # Auto Cutting Control (Otomatik Kesim)
    # ========================================================================
    TARGET_ADET_REGISTER = 2050
    TARGET_LENGTH_REGISTER = 2064
    CUT_COUNT_REGISTER = 2056
    AUTO_CUTTING_START_BIT = 13   # 20.13: Auto cutting start
    AUTO_CUTTING_RESET_BIT = 14   # 20.14: Auto cutting reset

    _write_double_word(register, value)
    write_target_adet(p, x)
    write_target_uzunluk(l_mm)
    read_kesilmis_adet()
    start_auto_cutting()
    reset_auto_cutting(active)
    cancel_auto_cutting()

    # === Status Methods ===
```

### Pattern 1: Thin Public Method Wrapping Private Helper

All six new public methods are thin wrappers. No method contains business logic beyond unit conversion.

**Example — write_target_adet (FC6 path):**
```python
# Source: Established pattern in write_cutting_speed (line 428-447 of machine_control.py)
def write_target_adet(self, p: int, x: int) -> bool:
    """
    Write target cut count to register 2050 (D2050).

    Args:
        p: Number of packages (hedef paket adedi)
        x: Pieces per package (paketteki adet)

    Returns:
        True if write succeeded
    """
    try:
        value = int(p) * int(x)
        logger.debug(f"Writing target adet: {p} * {x} = {value} -> register {self.TARGET_ADET_REGISTER}")
        success = self._write_register(self.TARGET_ADET_REGISTER, value)
        if success:
            logger.info(f"Target adet set to {value} (P={p}, X={x})")
        return success
    except Exception as e:
        logger.error(f"Target adet write error: {e}")
        return False
```

**Example — _write_double_word (FC16 path):**
```python
# Source: D-03 decision + write_registers signature verified via pymodbus 3.5.4
def _write_double_word(self, register: int, value: int) -> bool:
    """Write a 32-bit value to two consecutive registers (FC16, low-word first)."""
    try:
        if not self._ensure_connected():
            return False

        low_word = value & 0xFFFF
        high_word = (value >> 16) & 0xFFFF

        result = self.client.write_registers(address=register, values=[low_word, high_word])
        if result.isError():
            logger.error(f"Double word write error (register {register}): {result}")
            return False

        logger.debug(f"Double word written: register {register} = 0x{value:08X} (low=0x{low_word:04X}, high=0x{high_word:04X})")
        return True
    except Exception as e:
        logger.error(f"Double word write exception (register {register}): {e}")
        return False
```

**Example — write_target_uzunluk:**
```python
def write_target_uzunluk(self, l_mm: float) -> bool:
    """
    Write target length to registers 2064-2065 (D2064/D2065) as Double Word.

    Value is scaled: l_mm * 10. Uses FC16 write_registers with Mitsubishi
    low-word-first convention (D2064=low_word, D2065=high_word).

    Args:
        l_mm: Target length in mm (e.g., 1000.0)

    Returns:
        True if write succeeded
    """
    try:
        value = int(l_mm * 10)
        logger.debug(f"Writing target uzunluk: {l_mm}mm -> {value} (x10) -> register {self.TARGET_LENGTH_REGISTER}")
        success = self._write_double_word(self.TARGET_LENGTH_REGISTER, value)
        if success:
            logger.info(f"Target uzunluk set to {l_mm}mm (modbus: {value})")
        return success
    except Exception as e:
        logger.error(f"Target uzunluk write error: {e}")
        return False
```

**Example — reset_auto_cutting (active bool pattern):**
```python
def reset_auto_cutting(self, active: bool) -> bool:
    """
    Set or clear the auto cutting reset bit (20.14).

    Args:
        active: True to assert reset, False to release

    Returns:
        True if operation succeeded
    """
    return self._set_bit(self.CONTROL_REGISTER, self.AUTO_CUTTING_RESET_BIT, active)
```

**Example — cancel_auto_cutting (reuses existing constant):**
```python
def cancel_auto_cutting(self) -> bool:
    """Cancel auto cutting by setting stop bit (20.4)."""
    return self._set_bit(self.CONTROL_REGISTER, self.CUTTING_STOP_BIT, True)
```

### Pattern 2: Unit Test with Mocked ModbusTcpClient

The test file should mock `ModbusTcpClient` to avoid needing real PLC hardware.

```python
# Source: Established pattern from tests/test_camera_service.py + unittest.mock
from unittest.mock import MagicMock, patch
import pytest
from src.services.control.machine_control import MachineControl

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset MachineControl singleton between tests."""
    MachineControl._instance = None
    yield
    MachineControl._instance = None

@patch("src.services.control.machine_control.ModbusTcpClient")
def test_write_target_uzunluk_word_order(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.connect.return_value = True
    mock_client.is_socket_open.return_value = True
    mock_response = MagicMock()
    mock_response.isError.return_value = False
    mock_client.write_registers.return_value = mock_response

    mc = MachineControl()
    result = mc.write_target_uzunluk(1000.0)

    assert result is True
    mock_client.write_registers.assert_called_once_with(
        address=2064, values=[0x2710, 0x0000]
    )
```

### Anti-Patterns to Avoid

- **Using AsyncModbusService for new bit ops:** All register 20 operations MUST go through `MachineControl`. AsyncModbusService runs in the async pipeline and would cause read-modify-write race conditions on register 20. [VERIFIED: STATE.md architectural decision]
- **Adding polling to the 10Hz async loop:** D2056 polling is Phase 26 responsibility (500ms QTimer). Phase 25 only provides the `read_kesilmis_adet()` method. [VERIFIED: STATE.md and ROADMAP.md]
- **Writing D2064 as two separate FC6 calls:** The FC16 atomic write is required. Two sequential FC6 calls risk partial writes if connection drops mid-sequence. [VERIFIED: D-03 decision]
- **Adding `_write_double_word` to the public API:** Keep it private (underscore prefix) per existing convention (`_write_register`, `_set_bit`, etc.).
- **Resetting singleton state in non-test code:** The `_initialized` guard in `__init__` must not be disturbed. Tests must reset `_instance` via fixture.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FC16 Double Word write | Custom socket-level Modbus framing | `client.write_registers(address, [low, high])` | pymodbus handles framing, CRC, error response parsing |
| Singleton thread safety | Custom lock/init guards | Existing `__new__` + `_lock` pattern already in MachineControl | Already correct; duplicating would create race conditions |
| Bit read-modify-write | Custom read-then-write inline | Existing `_set_bit(register, bit, value)` | Already handles None guard, logging, and return bool |
| Connection retry | Custom reconnect loop | Existing `_ensure_connected()` + `_should_attempt_connect()` | Already handles cooldown, logging |

---

## Common Pitfalls

### Pitfall 1: Singleton Not Resetting Between Tests
**What goes wrong:** MachineControl is a singleton. If test A creates an instance, test B gets the same instance with a real (failed) connection attempt.
**Why it happens:** `_instance` persists on the class between test function calls.
**How to avoid:** Add a `reset_singleton` autouse fixture that sets `MachineControl._instance = None` before and after each test.
**Warning signs:** First test passes, subsequent tests fail with "already connected" or wrong mock behavior.

### Pitfall 2: write_registers result.isError() not checked
**What goes wrong:** FC16 writes silently fail if the result object's `isError()` is not called.
**Why it happens:** pymodbus `write_registers` returns a response object (not raises on protocol errors).
**How to avoid:** Always call `result.isError()` after `write_registers`, exactly as done in `_write_register` for `write_register`.
**Warning signs:** Method returns True even when PLC refuses the write.

### Pitfall 3: l_mm float precision in write_target_uzunluk
**What goes wrong:** `int(l_mm * 10)` can suffer floating-point imprecision (e.g., `0.1 * 10 = 0.9999...`).
**Why it happens:** IEEE 754 float representation of decimal fractions.
**How to avoid:** Use `round(l_mm * 10)` before `int()`, or `int(round(l_mm * 10))`, to eliminate floating point drift.
**Warning signs:** Unit test for L=100.3mm produces value=1002 instead of 1003.

### Pitfall 4: P*X overflow for D2050 (Word register)
**What goes wrong:** D2050 is a 16-bit Word register (max 65535). If P and X are both large integers, `p * x` can exceed 0xFFFF.
**Why it happens:** No range guard in the method.
**How to avoid:** The planner should decide whether to add a clamp/raise or leave it as caller responsibility. Since Phase 26 will provide the GUI with limited input ranges, overflow is unlikely in practice. Logging the written value is sufficient for now.
**Warning signs:** PLC silently truncates or rejects writes > 65535.

### Pitfall 5: `_load_modbus_config` in test environment
**What goes wrong:** `MachineControl.__init__` calls `_load_modbus_config()` which opens `config/config.yaml`. In test environment the file may not exist (or may point to a real PLC IP).
**Why it happens:** Config loading is unconditional in `__init__`.
**How to avoid:** The existing `_load_modbus_config` already catches `Exception` and returns defaults. With `ModbusTcpClient` mocked, no real connection is attempted. No special handling needed.
**Warning signs:** Tests hang trying to connect to default IP `127.0.0.1:502`.

---

## Double Word Math Verification

[VERIFIED: computed via Python 3.13.12 in this session]

```
L = 1000 mm
value = int(1000 * 10) = 10000 = 0x00002710

low_word  = 0x00002710 & 0xFFFF = 0x2710  (10000)
high_word = (0x00002710 >> 16) & 0xFFFF = 0x0000  (0)

FC16 call: write_registers(address=2064, values=[0x2710, 0x0000])
  → D2064 = 0x2710  ✓ (matches success criterion)
  → D2065 = 0x0000  ✓ (matches success criterion)
```

Additional verification for large value (L=100000mm):
```
value = int(100000 * 10) = 1000000 = 0x000F4240

low_word  = 0x000F4240 & 0xFFFF = 0x4240
high_word = (0x000F4240 >> 16) & 0xFFFF = 0x000F

FC16 call: write_registers(address=2064, values=[0x4240, 0x000F])
  → D2064 = 0x4240
  → D2065 = 0x000F
```

This confirms the formula handles multi-word values correctly.

---

## Validation Architecture

`workflow.nyquist_validation` key is absent from `.planning/config.json` — treated as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml (no `[tool.pytest.ini_options]` section — uses defaults) |
| Quick run command | `python -m pytest tests/test_machine_control_auto_cutting.py -x -q` |
| Full suite command | `python -m pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PLC-04 | `_write_double_word` calls `write_registers` with `[low, high]` | unit | `python -m pytest tests/test_machine_control_auto_cutting.py::test_write_double_word -x` | ❌ Wave 0 |
| PLC-01 | `write_target_adet(5, 10)` calls `write_register(2050, 50)` | unit | `python -m pytest tests/test_machine_control_auto_cutting.py::test_write_target_adet -x` | ❌ Wave 0 |
| PLC-02 | `write_target_uzunluk(1000.0)` calls `write_registers(2064, [0x2710, 0x0000])` | unit | `python -m pytest tests/test_machine_control_auto_cutting.py::test_write_target_uzunluk_word_order -x` | ❌ Wave 0 |
| PLC-03 | `read_kesilmis_adet()` calls `read_holding_registers(2056, 1)` | unit | `python -m pytest tests/test_machine_control_auto_cutting.py::test_read_kesilmis_adet -x` | ❌ Wave 0 |
| CTRL-01 | `start_auto_cutting()` sets bit 13 on register 20 | unit | `python -m pytest tests/test_machine_control_auto_cutting.py::test_start_auto_cutting -x` | ❌ Wave 0 |
| CTRL-02 | `reset_auto_cutting(True)` sets bit 14; `reset_auto_cutting(False)` clears bit 14 | unit | `python -m pytest tests/test_machine_control_auto_cutting.py::test_reset_auto_cutting -x` | ❌ Wave 0 |
| CTRL-03 | `cancel_auto_cutting()` sets bit 4 (CUTTING_STOP_BIT) on register 20 | unit | `python -m pytest tests/test_machine_control_auto_cutting.py::test_cancel_auto_cutting -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_machine_control_auto_cutting.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_machine_control_auto_cutting.py` — covers all 7 requirements (PLC-01..04, CTRL-01..03). Needs singleton reset fixture and ModbusTcpClient mock.

*(No framework install needed — pytest 9.0.2 already installed.)*

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pymodbus | `_write_double_word` FC16 | ✓ | 3.5.4 | — |
| pytest | Unit tests | ✓ | 9.0.2 | — |
| Python | All | ✓ | 3.13.12 | — |

[VERIFIED: all via `python -m pytest --version` and `python -c "import pymodbus; print(pymodbus.__version__)"`]

**No missing dependencies.** This is a pure code-extension phase with no external service calls or new installs required.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `write_registers` return value's `.isError()` method works the same as `write_register` return value | Code Examples | Pattern already verified in `_write_register` (line 178) — should be identical, but not tested live against real PLC | LOW |
| A2 | Bit 20.13 latch: PLC clears bit after acknowledge (fire-and-forget is correct) | Standard Stack | Per STATE.md "Open Verification Items" — unverified against real PLC hardware. If PLC does NOT auto-clear, GUI may need explicit clear in Phase 26 | MEDIUM |
| A3 | L values will be integer or simple decimal mm values (no micro-precision float input) | Pitfalls | `round()` mitigates; risk is negligible for industrial saw dimensions | LOW |

**Note:** A2 is flagged in STATE.md as an open verification item. The Phase 25 implementation follows D-02 (fire-and-forget), but this must be confirmed against real PLC before Phase 26 ships.

---

## Open Questions

1. **Bit 20.13 latch behavior (A2 above)**
   - What we know: D-02 decision says fire-and-forget; `start_cutting()` uses same pattern
   - What's unclear: Whether real Mitsubishi PLC auto-clears bit 13 after START acknowledge
   - Recommendation: Implement as decided (fire-and-forget). Document as open item in plan. Confirm before Phase 26 ships.

2. **Should `cancel_auto_cutting()` also clear the bit after setting it?**
   - What we know: `stop_cutting()` only sets bit 4 (never clears it) — same pattern intended for cancel
   - What's unclear: Whether stop/cancel bit should be pulsed or held
   - Recommendation: Implement as fire-and-forget (set only, no clear) consistent with D-01 and existing `stop_cutting()`.

---

## Sources

### Primary (HIGH confidence)
- `src/services/control/machine_control.py` — Direct source read, all private method signatures and patterns verified [VERIFIED: Read tool]
- `pymodbus 3.5.4` installed in environment — `write_registers` and `write_register` signatures verified [VERIFIED: `help()` in Python session]
- `python -c` math verification — Double Word bit-splitting for L=1000mm confirmed [VERIFIED: computed in session]
- `.planning/phases/25-machinecontrol-extension/25-CONTEXT.md` — All locked decisions read verbatim [VERIFIED: Read tool]
- `.planning/milestones/v2.1-ROADMAP.md` — Success criteria confirmed [VERIFIED: Read tool]
- `.planning/STATE.md` — Architectural decisions and open verification items [VERIFIED: Read tool]
- `.planning/codebase/CONVENTIONS.md` — Naming, logging, docstring conventions [VERIFIED: Read tool]
- `tests/test_camera_service.py` — Mock pattern for unittest.mock with singleton reset [VERIFIED: Read tool]
- `pyproject.toml` — pytest version, black line-length 100, ruff config [VERIFIED: Read tool]

### Secondary (MEDIUM confidence)
- Mitsubishi low-word-first convention alignment with D-03 decision — consistent with standard Mitsubishi MELSEC register convention [ASSUMED — unverified against physical PLC datasheet]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified in-environment
- Architecture: HIGH — source file read directly, patterns verified
- Math/bit-splitting: HIGH — computed in Python session
- Pitfalls: HIGH — derived from direct code inspection
- Latch behavior: LOW — open hardware verification item per STATE.md

**Research date:** 2026-04-09
**Valid until:** 2026-05-09 (stable domain — pymodbus minor versions only)
