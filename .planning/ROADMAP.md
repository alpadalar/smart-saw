# Roadmap: Smart Saw Database Field Additions

## Overview

Database schema guncellemesi icin uc asamali uygulama. ML predictions tablosuna tork ve kafa yuksekligi alanlari, anomaly events tablosuna kafa yuksekligi alani eklenerek gecmise donuk analiz icin veri zenginlestirilecek.

## Domain Expertise

None

## Milestones

- [v1.0 Database Field Additions](milestones/v1.0-ROADMAP.md) (Phases 1-3) — SHIPPED 2026-01-15
- [v1.1 Modbus Connection Resilience](milestones/v1.1-ROADMAP.md) (Phase 4) — SHIPPED 2026-01-15
- 🚧 **v1.2 ML Speed Memory & Chart UX** — Phases 5-6 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

<details>
<summary>v1.0 Database Field Additions (Phases 1-3) — SHIPPED 2026-01-15</summary>

- [x] Phase 1: ML Schema Update (1/1 plans) — completed 2026-01-15
- [x] Phase 2: Anomaly Schema Update (1/1 plans) — completed 2026-01-15
- [x] Phase 3: Data Population (2/2 plans) — completed 2026-01-15

</details>

<details>
<summary>v1.1 Modbus Connection Resilience (Phase 4) — SHIPPED 2026-01-15</summary>

- [x] Phase 4: Modbus Connection Timeout Handling (1/1 plans) — completed 2026-01-15

</details>

### 🚧 v1.2 ML Speed Memory & Chart UX (In Progress)

**Milestone Goal:** ML kesim sonrası hız restorasyonu ve grafik kullanılabilirliği

#### Phase 5: ML Speed Restoration — COMPLETE

**Goal**: Save/restore kesme and inme speeds around ML cuts
**Depends on**: Phase 4 (previous milestone complete)
**Research**: Unlikely (internal patterns — state machine logic, Modbus writes)
**Plans**: 1/1 complete

Plans:
- [x] 05-01: Implement save/restore of cutting speeds around ML cuts — completed 2026-01-15

#### Phase 6: Dynamic Chart Axis Labels

**Goal**: Add dynamic axis labels to sensor data charts
**Depends on**: Phase 5
**Research**: Unlikely (internal patterns — PyQtGraph axis configuration)
**Plans**: TBD

Plans:
- [ ] 06-01: TBD (run /gsd:plan-phase 6 to break down)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. ML Schema Update | v1.0 | 1/1 | Complete | 2026-01-15 |
| 2. Anomaly Schema Update | v1.0 | 1/1 | Complete | 2026-01-15 |
| 3. Data Population | v1.0 | 2/2 | Complete | 2026-01-15 |
| 4. Modbus Connection Timeout Handling | v1.1 | 1/1 | Complete | 2026-01-15 |
| 5. ML Speed Restoration | v1.2 | 1/1 | Complete | 2026-01-15 |
| 6. Dynamic Chart Axis Labels | v1.2 | 0/? | Not started | - |
