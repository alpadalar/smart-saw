---
phase: 21
slug: ai-detection-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `tests/conftest.py` |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | DET-01, DET-02 | unit | `python -m pytest tests/test_detection_worker.py -v` | ❌ W0 | ⬜ pending |
| 21-01-02 | 01 | 1 | DET-05 | unit | `python -m pytest tests/test_detection_worker.py -v` | ❌ W0 | ⬜ pending |
| 21-01-03 | 01 | 1 | DET-06 | unit | `python -m pytest tests/test_detection_worker.py -v` | ❌ W0 | ⬜ pending |
| 21-02-01 | 02 | 2 | DET-03 | unit | `python -m pytest tests/test_ldc_worker.py -v` | ❌ W0 | ⬜ pending |
| 21-02-02 | 02 | 2 | DET-04 | unit | `python -m pytest tests/test_health_calculator.py -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_detection_worker.py` — stubs for DET-01, DET-02, DET-05, DET-06
- [ ] `tests/test_ldc_worker.py` — stubs for DET-03
- [ ] `tests/test_health_calculator.py` — stubs for DET-04

*Existing pytest infrastructure covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| RT-DETR model inference accuracy | DET-01, DET-02 | Requires actual model + GPU/CPU inference | Load model, run on sample image, verify bounding boxes |
| LDC model inference accuracy | DET-03 | Requires actual model + sample saw image | Load model, run inference, verify wear percentage |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
