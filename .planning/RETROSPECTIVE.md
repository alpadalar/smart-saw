# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.6 — Touch UX & Data Traceability

**Shipped:** 2026-03-16
**Phases:** 4 | **Plans:** 4

### What Was Built
- TouchButton widget with Qt touch events for industrial HMI positioning buttons
- Emergency stop overlay during jog operations with safety mechanisms
- ML prediction logging fix (deferred logging pattern for complete data capture)
- ML predictions traceability: kesim_id, makine_id, serit_id, malzeme_cinsi
- Anomaly events traceability: makine_id, serit_id, malzeme_cinsi

### What Worked
- Phase 17/18 symmetry: anomaly traceability was a direct repeat of ML traceability pattern, executed in 2 min each
- Falsy-to-None conversion pattern: established once in Phase 17, applied identically in Phase 18
- Investigation-first approach (Phase 16): root cause analysis before fix prevented wasted effort
- Zero deviations from plan across all 4 phases

### What Was Inefficient
- Phase 16 gap between completion (2026-02-04) and Phase 17 start (2026-03-15) — 39 days idle
- MLDB-05 requirement checkbox not updated after Phase 16 fix — required manual correction during milestone completion

### Patterns Established
- Traceability column pattern: nullable columns (no NOT NULL, no DEFAULT), falsy-to-None conversion at call site
- Deferred logging: log after all computed values available, not during computation
- TouchButton dual-input pattern: Qt touch events + inherited QPushButton mouse behavior

### Key Lessons
1. Schema extension phases are fast (2 min avg) when following established ALTER TABLE pattern
2. Investigation phases (Phase 16) are valuable — root cause analysis prevents wrong-direction fixes
3. Keep requirement checkboxes in sync with phase completion to avoid confusion at milestone close

### Cost Observations
- Sessions: ~4
- Notable: Phases 17-18 combined took 4 min total — fastest milestone phases due to established patterns

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Key Change |
|-----------|--------|------------|
| v1.0 | 3 | Initial schema extension pattern established |
| v1.1 | 1 | Single-phase milestone for urgent fix |
| v1.2 | 2 | Feature + UX improvement pairing |
| v1.3 | 3 | Performance optimization trilogy |
| v1.4 | 2 | Bug fix milestone |
| v1.5 | 3 | Parity verification + UX polish |
| v1.6 | 4 | Touch UX + traceability data enrichment |

### Top Lessons (Verified Across Milestones)

1. ALTER TABLE pattern is reliable and fast — used in v1.0, v1.6 without issues
2. Investigation phases prevent wasted effort — v1.5 (ML parity) and v1.6 (None values) both benefited
3. Symmetric patterns (same change to different tables) execute fastest when done back-to-back
