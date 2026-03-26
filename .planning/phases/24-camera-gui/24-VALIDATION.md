---
phase: 24
slug: camera-gui
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 24 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml |
| **Quick run command** | `python -m pytest tests/test_detection_worker.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_detection_worker.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green + visual inspection
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 24-01-xx | 01 | 1 | D-02 backend | unit | `python -m pytest tests/test_detection_worker.py -x -q` | ✅ (needs extension) | ⬜ pending |
| 24-01-xx | 01 | 1 | GUI-01 | manual-only | — | N/A | ⬜ pending |
| 24-01-xx | 01 | 1 | GUI-02 | manual-only | — | N/A | ⬜ pending |
| 24-01-xx | 01 | 1 | GUI-03 | manual-only | — | N/A | ⬜ pending |
| 24-01-xx | 01 | 1 | GUI-04 | manual-only | — | N/A | ⬜ pending |
| 24-01-xx | 01 | 1 | GUI-05 | manual-only | — | N/A | ⬜ pending |
| 24-02-xx | 02 | 1 | GUI-06 | manual-only | — | N/A | ⬜ pending |
| 24-02-xx | 02 | 1 | GUI-07 | manual-only | — | N/A | ⬜ pending |
| 24-02-xx | 02 | 1 | GUI-08 | manual-only | — | N/A | ⬜ pending |
| 24-02-xx | 02 | 1 | GUI-09 | manual-only | — | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. GUI portions are visual-only per D-09.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live feed shows annotated frame | GUI-01 | PySide6 QLabel rendering — visual output | Launch app with camera enabled, verify bounding boxes visible on live feed |
| Broken count/timestamp displayed | GUI-02 | QLabel text rendering | Verify broken count and last detection timestamp appear on camera page |
| Crack count/timestamp displayed | GUI-03 | QLabel text rendering | Verify crack count and last detection timestamp appear on camera page |
| Wear bar green→red direction | GUI-04 | QProgressBar gradient visual | Verify low wear = green, high wear = red on progress bar |
| Health bar red→green direction | GUI-05 | QProgressBar gradient visual | Verify low health = red, high health = green on progress bar (inverse) |
| Sidebar button conditional | GUI-06 | Sidebar widget visibility | Set camera.enabled=false in config, verify no camera button; set true, verify button appears |
| 4 thumbnails visible | GUI-07 | QLabel thumbnail rendering | Trigger 4+ detections, verify 4 thumbnails in strip |
| OK/alert icon changes | GUI-08 | Icon swap visual | Trigger detection with broken>0, verify alert icon; reset, verify OK icon |
| Wear visualization overlay | GUI-09 | Progress bar presence | Verify wear progress bar visible alongside numeric value |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
