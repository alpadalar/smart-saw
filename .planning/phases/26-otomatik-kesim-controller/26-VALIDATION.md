---
phase: 26
slug: otomatik-kesim-controller
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-09
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pytest.ini |
| **Quick run command** | `python -m pytest tests/ -x -q --timeout=10` |
| **Full suite command** | `python -m pytest tests/ -v --timeout=30` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q --timeout=10`
- **After every plan wave:** Run `python -m pytest tests/ -v --timeout=30`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 26-01-01 | 01 | 1 | PARAM-01 | — | N/A | unit | `python -m pytest tests/test_otomatik_kesim_controller.py -k "numpad"` | ❌ W0 | ⬜ pending |
| 26-01-02 | 01 | 1 | PARAM-05 | — | N/A | unit | `python -m pytest tests/test_numpad.py -k "decimal"` | ❌ W0 | ⬜ pending |
| 26-01-03 | 01 | 1 | GUI-02 | — | N/A | unit | `python -m pytest tests/test_otomatik_kesim_controller.py -k "validate"` | ❌ W0 | ⬜ pending |
| 26-01-04 | 01 | 1 | GUI-03 | — | N/A | unit | `python -m pytest tests/test_otomatik_kesim_controller.py -k "reset"` | ❌ W0 | ⬜ pending |
| 26-01-05 | 01 | 1 | PARAM-04 | — | N/A | unit | `python -m pytest tests/test_otomatik_kesim_controller.py -k "counter"` | ❌ W0 | ⬜ pending |
| 26-01-06 | 01 | 1 | ML-01 | — | N/A | unit | `python -m pytest tests/test_otomatik_kesim_controller.py -k "ml_mode"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_otomatik_kesim_controller.py` — stubs for PARAM-01..05, GUI-02, GUI-03, ML-01, ML-02
- [ ] `tests/test_numpad.py` — extend for allow_decimal parameter

*Existing infrastructure covers test framework requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Touch hold-to-reset animation | GUI-03 | Requires physical touch input | Hold RESET button on touchscreen for 1.5s, verify gradient fill animation |
| D2056 real-time counter display | PARAM-04 | Requires live PLC connection | Start auto cutting, observe counter updates at 500ms interval |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
