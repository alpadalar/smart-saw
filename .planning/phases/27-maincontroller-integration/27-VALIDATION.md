---
phase: 27
slug: maincontroller-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-09
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — no pytest.ini or [tool.pytest] section |
| **Quick run command** | `python -m pytest tests/test_main_controller_integration.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_main_controller_integration.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 27-01-01 | 01 | 0 | GUI-01 | — | N/A | unit | `python -m pytest tests/test_page_index.py -x -q` | ❌ W0 | ⬜ pending |
| 27-01-02 | 01 | 0 | GUI-01 | — | N/A | unit | `python -m pytest tests/test_main_controller_integration.py -x -q` | ❌ W0 | ⬜ pending |
| 27-01-03 | 01 | 1 | GUI-01 | — | N/A | unit | `python -m pytest tests/test_main_controller_integration.py::test_close_event_stops_otomatik_kesim_timers -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_main_controller_integration.py` — GUI-01 navigasyon ve closeEvent testleri; `__new__` injection pattern ile QApplication gerektirmez
- [ ] `tests/test_page_index.py` — PageIndex enum değer doğrulaması

*Mevcut test altyapısı var; pytest kurulu; `__new__` injection pattern biliniyor*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Sidebar buton görsel sıralaması doğru | GUI-01 | Y-koordinat layout visual check | Uygulamayı başlat, sidebar buton sıralamasını kontrol et: Kontrol Paneli → Otomatik Kesim → Konumlandırma → Sensör → İzleme → Kamera |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
