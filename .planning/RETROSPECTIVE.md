# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v2.0 — Camera Vision & AI Detection

**Shipped:** 2026-04-08
**Phases:** 11 | **Plans:** 14

### What Was Built
- Config-driven camera module foundation (camera.enabled=false → zero imports/threads/disk)
- OpenCV frame capture with auto-discovery, 30s retry, JPEG recording pipeline
- RT-DETR broken tooth + crack detection, LDC edge-based wear calculation
- VisionService lifecycle orchestration with CUTTING state transition recording trigger
- SQLite camera.db integration (detection_events + wear_history tables)
- ThingsBoard IoT telemetry with 6 camera fields
- PySide6 camera GUI page: live annotated feed, detection stats, wear/health progress bars, thumbnails, sidebar button
- NumpadDialog close button + speed pre-fill (UI refinement insert)
- Graph axis labels repositioning + Şerit Gerginliği Y-axis button (UI insert)

### What Worked
- CameraResultsStore as single integration boundary: GUI, IoT, and DB all read from one thread-safe store — clean separation
- Lazy import pattern behind camera.enabled guard: zero risk of ImportError on systems without OpenCV/torch
- Milestone audit + gap closure phases (24.1, 24.2): caught config-code mismatches and missing verification artifacts before milestone close
- 50 unit tests with full mocking: no hardware dependency, all tests pass without camera/GPU
- Decimal phase insertion (19.1, 19.2, 19.3, 24.1, 24.2) for urgent work without disrupting main phase numbering

### What Was Inefficient
- Phase 23 IoT Integration had no phase directory or artifacts despite code being committed — required retroactive artifact creation in Phase 24.2
- Several SUMMARY.md files had empty "One-liner:" fields — extraction tooling couldn't populate milestone accomplishments automatically
- Milestone audit found 9 requirements with "partial" status due to missing VERIFICATION.md — all had working code, just lacked formal verification documents
- Config keys (camera.health.broken_weight/wear_weight) were written to config.yaml but never consumed by code until Phase 24.1 fix

### Patterns Established
- Camera pipeline architecture: CameraService → Worker threads → CameraResultsStore → consumers (GUI/IoT/DB)
- Config-driven feature toggling: camera.enabled flag with lazy imports — reusable for future optional modules
- Worker thread pattern: models loaded inside thread.run(), daemon threads, never touch asyncio event loop
- Milestone audit → gap closure phases workflow: systematic quality assurance before milestone close

### Key Lessons
1. Create phase artifacts (directory, SUMMARY, VERIFICATION) immediately after code is committed — retroactive creation is wasteful
2. Config keys must be consumed by code in the same phase they're added — dead config is confusing
3. CameraResultsStore-as-boundary pattern proved excellent: 6 consumers all decoupled via single store
4. SUMMARY.md one-liner field should be explicitly written, not left as placeholder — it feeds milestone documentation
5. Milestone audit is valuable even when all requirements have working code — it catches process gaps (missing verification, outdated checkboxes)

### Cost Observations
- Sessions: ~8
- Notable: Core camera pipeline (Phases 19-22) completed in 2 days; gap closure phases (24.1-24.2) took separate session
- 50 unit tests written without hardware — industrial projects need mockable architecture from the start

---

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
| v2.0 | 11 | First major feature milestone — camera vision pipeline + AI detection |

### Top Lessons (Verified Across Milestones)

1. ALTER TABLE pattern is reliable and fast — used in v1.0, v1.6 without issues
2. Investigation phases prevent wasted effort — v1.5 (ML parity) and v1.6 (None values) both benefited
3. Symmetric patterns (same change to different tables) execute fastest when done back-to-back
4. CameraResultsStore-as-boundary proves single integration point scales well (v2.0: 6 consumers)
5. Milestone audits catch process gaps even when code is complete — formal verification matters
6. Config-driven feature toggles (camera.enabled) enable safe incremental deployment
