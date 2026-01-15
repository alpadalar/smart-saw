# Roadmap: Smart Saw Database Field Additions

## Overview

Database schema guncellemesi icin uc asamali uygulama. ML predictions tablosuna tork ve kafa yuksekligi alanlari, anomaly events tablosuna kafa yuksekligi alani eklenerek gecmise donuk analiz icin veri zenginlestirilecek.

## Domain Expertise

None

## Milestones

- [v1.0 Database Field Additions](milestones/v1.0-ROADMAP.md) (Phases 1-3) — SHIPPED 2026-01-15
- [v1.1 Modbus Connection Resilience](milestones/v1.1-ROADMAP.md) (Phase 4) — SHIPPED 2026-01-15
- [v1.2 ML Speed Memory & Chart UX](milestones/v1.2-ROADMAP.md) (Phases 5-6) — SHIPPED 2026-01-15
- [v1.3 Processing Performance](milestones/v1.3-ROADMAP.md) (Phases 7-9) — SHIPPED 2026-01-15
- 🚧 **v1.4 Control Mode Fixes** — Phases 10-11 (in progress)

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

<details>
<summary>v1.2 ML Speed Memory & Chart UX (Phases 5-6) — SHIPPED 2026-01-15</summary>

**Milestone Goal:** ML kesim sonrası hız restorasyonu ve grafik kullanılabilirliği

#### Phase 5: ML Speed Restoration — COMPLETE

**Goal**: Save/restore kesme and inme speeds around ML cuts
**Depends on**: Phase 4 (previous milestone complete)
**Research**: Unlikely (internal patterns — state machine logic, Modbus writes)
**Plans**: 1/1 complete

Plans:
- [x] 05-01: Implement save/restore of cutting speeds around ML cuts — completed 2026-01-15

#### Phase 6: Dynamic Chart Axis Labels — COMPLETE

**Goal**: Add dynamic axis labels to sensor data charts
**Depends on**: Phase 5
**Research**: Unlikely (internal patterns — PyQtGraph axis configuration)
**Plans**: 1/1 complete

Plans:
- [x] 06-01: Add dynamic Y-axis and X-axis title labels to cutting graph — completed 2026-01-15

</details>

<details>
<summary>v1.3 Processing Performance (Phases 7-9) — SHIPPED 2026-01-15</summary>

**Milestone Goal:** Data processor cycle time'ı 100ms hedefine düşürmek için lock contention ve algoritma optimizasyonları

#### Phase 7: MQTT Lock-Free Queue — COMPLETE

**Goal**: Lock-free asyncio.Queue ile queue_telemetry decoupling
**Depends on**: Phase 6 (previous milestone complete)
**Research**: Unlikely (internal patterns — asyncio.Queue, producer-consumer pattern)
**Plans**: 1/1 complete

Plans:
- [x] 07-01: Replace deque + Lock with lock-free asyncio.Queue — completed 2026-01-15

#### Phase 8: Vibration DBSCAN to IQR — COMPLETE

**Goal**: Vibration anomaly detektörlerini IQR method'a geçir
**Depends on**: Phase 7
**Research**: Unlikely (internal patterns — IQR already implemented for other detectors)
**Plans**: 1/1 complete

Plans:
- [x] 08-01: Replace DBSCAN with IQR for vibration detectors — completed 2026-01-15

#### Phase 9: AnomalyManager Lock Consolidation — COMPLETE

**Goal**: Tek lock acquisition ile tum detektor isleme
**Depends on**: Phase 8
**Research**: Unlikely (internal patterns — threading lock refactoring)
**Plans**: 1/1 complete

Plans:
- [x] 09-01: Consolidate lock acquisitions in process_data() — completed 2026-01-15

</details>

### 🚧 v1.4 Control Mode Fixes (In Progress)

**Milestone Goal:** Kontrol modu geçişleri ve başlangıç davranışı düzeltmeleri — AI mode switch hatası ve manuel mod initial delay sorunu

#### Phase 10: AI Mode Switch Fix

**Goal**: GUI thread'den asyncio çağrısı için cross-thread coordination
**Depends on**: Phase 9 (previous milestone complete)
**Research**: Unlikely (internal patterns — asyncio/threading coordination)
**Plans**: TBD

Plans:
- [ ] 10-01: TBD (run /gsd:plan-phase 10 to break down)

#### Phase 11: Initial Delay Logic

**Goal**: Manuel mod için `initial_delay=False` default, ML mod için mevcut davranış korunsun
**Depends on**: Phase 10
**Research**: Unlikely (internal patterns — simple flag logic)
**Plans**: TBD

Plans:
- [ ] 11-01: TBD (run /gsd:plan-phase 11 to break down)

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
| 6. Dynamic Chart Axis Labels | v1.2 | 1/1 | Complete | 2026-01-15 |
| 7. MQTT Lock-Free Queue | v1.3 | 1/1 | Complete | 2026-01-15 |
| 8. Vibration DBSCAN to IQR | v1.3 | 1/1 | Complete | 2026-01-15 |
| 9. AnomalyManager Lock Consolidation | v1.3 | 1/1 | Complete | 2026-01-15 |
| 10. AI Mode Switch Fix | v1.4 | 0/? | Not started | - |
| 11. Initial Delay Logic | v1.4 | 0/? | Not started | - |
