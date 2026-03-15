---
phase: 17
slug: ml-db-schema-update
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — no test framework in project |
| **Config file** | None — Wave 0 gap |
| **Quick run command** | `python -m py_compile src/services/database/schemas.py && python -m py_compile src/services/control/ml_controller.py` |
| **Full suite command** | Same (no test suite exists) |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m py_compile src/services/database/schemas.py && python -m py_compile src/services/control/ml_controller.py`
- **After every plan wave:** Run full compile check
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 17-01-01 | 01 | 1 | MLDB-01 | smoke | `python -c "from src.services.database.schemas import SCHEMA_ML_DB; assert 'kesim_id' in SCHEMA_ML_DB"` | ❌ inline | ⬜ pending |
| 17-01-02 | 01 | 1 | MLDB-02 | smoke | `python -c "from src.services.database.schemas import SCHEMA_ML_DB; assert 'makine_id' in SCHEMA_ML_DB"` | ❌ inline | ⬜ pending |
| 17-01-03 | 01 | 1 | MLDB-03 | smoke | `python -c "from src.services.database.schemas import SCHEMA_ML_DB; assert 'serit_id' in SCHEMA_ML_DB"` | ❌ inline | ⬜ pending |
| 17-01-04 | 01 | 1 | MLDB-04 | smoke | `python -c "from src.services.database.schemas import SCHEMA_ML_DB; assert 'malzeme_cinsi' in SCHEMA_ML_DB"` | ❌ inline | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements — column presence verified with inline `python -c` one-liners and py_compile checks.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Existing records preserved | All | Requires live ml.db with data | Verify row count before/after schema recreation matches |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 2s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
