---
phase: 18
slug: anomaly-db-schema-update
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None detected — compile checks + inline assertions |
| **Config file** | none |
| **Quick run command** | `python -m py_compile src/services/database/schemas.py && python -m py_compile src/services/processing/anomaly_tracker.py && python -m py_compile src/services/processing/data_processor.py` |
| **Full suite command** | `python -m py_compile src/services/database/schemas.py && python -m py_compile src/services/processing/anomaly_tracker.py && python -m py_compile src/services/processing/data_processor.py` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m py_compile src/services/database/schemas.py && python -m py_compile src/services/processing/anomaly_tracker.py && python -m py_compile src/services/processing/data_processor.py`
- **After every plan wave:** Run full suite + column presence inline checks
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | ANDB-01 | smoke | `python -c "from src.services.database.schemas import SCHEMA_ANOMALY_DB; assert 'makine_id' in SCHEMA_ANOMALY_DB"` | inline | pending |
| 18-01-02 | 01 | 1 | ANDB-02 | smoke | `python -c "from src.services.database.schemas import SCHEMA_ANOMALY_DB; assert 'serit_id' in SCHEMA_ANOMALY_DB"` | inline | pending |
| 18-01-03 | 01 | 1 | ANDB-03 | smoke | `python -c "from src.services.database.schemas import SCHEMA_ANOMALY_DB; assert 'malzeme_cinsi' in SCHEMA_ANOMALY_DB"` | inline | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 2s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
