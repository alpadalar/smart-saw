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
- [v1.4 Control Mode Fixes](milestones/v1.4-ROADMAP.md) (Phases 10-11) — SHIPPED 2026-01-28
- [v1.5 ML Parity & UX Polish](milestones/v1.5-ROADMAP.md) (Phases 12-14) — SHIPPED 2026-01-28
- [v1.6 Touch UX & Data Traceability](milestones/v1.6-ROADMAP.md) (Phases 15-18) — IN PROGRESS

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

<details>
<summary>v1.4 Control Mode Fixes (Phases 10-11) — SHIPPED 2026-01-28</summary>

- [x] Phase 10: AI Mode Switch Fix (1/1 plans) — completed 2026-01-15
- [x] Phase 11: Initial Delay Logic (1/1 plans) — completed 2026-01-15

</details>

<details>
<summary>v1.5 ML Parity & UX Polish (Phases 12-14) — SHIPPED 2026-01-28</summary>

**Milestone Goal:** Critical ML behavior fix ensuring new code matches old code predictions + comprehensive GUI labeling improvements

- [x] Phase 12: ML Prediction Parity Investigation & Fix (1/1 plans) — completed 2026-01-28
- [x] Phase 13: Unit Labels & Naming Fixes (1/1 plans) — completed 2026-01-28
- [x] Phase 14: Chart Axis Labels & Sapma Gauge Fix (1/1 plans) — completed 2026-01-28

</details>

<details open>
<summary>v1.6 Touch UX & Data Traceability (Phases 15-18) — IN PROGRESS</summary>

**Milestone Goal:** Dokunmatik ekran kullanılabilirliği ve veritabanı veri izlenebilirliği

#### Phase 15: Touch Long Press Fix — PENDING

**Goal**: Fix touch event handling on positioning buttons
**Depends on**: Phase 14 (previous milestone complete)
**Requirements**: TOUCH-01, TOUCH-02, TOUCH-03
**Research**: Unlikely (Qt touch events — well-documented pattern)
**Plans**: 0/? planned

**Success Criteria:**
1. User can long press positioning buttons with touch input and jog action activates
2. User can release touch press and jog action stops immediately
3. Visual feedback (button pressed state) appears during touch press
4. Mouse long press on positioning buttons continues to work without regression

#### Phase 16: ML DB None Values Investigation — PENDING

**Goal**: Investigate and fix None values in ML database fields
**Depends on**: Phase 15
**Requirements**: MLDB-05
**Research**: LIKELY (root cause analysis for None values in yeni_kesme_hizi, yeni_inme_hizi, katsayi)
**Plans**: 0/? planned

**Success Criteria:**
1. User can query ML predictions table and see actual numeric values in yeni_kesme_hizi field (not None)
2. User can query ML predictions table and see actual numeric values in yeni_inme_hizi field (not None)
3. User can query ML predictions table and see actual numeric values in katsayi field (not None)
4. Root cause of None values documented in investigation report

#### Phase 17: ML DB Schema Update — PENDING

**Goal**: Add traceability fields to ML predictions table
**Depends on**: Phase 16
**Requirements**: MLDB-01, MLDB-02, MLDB-03, MLDB-04
**Research**: Unlikely (established v1.0 ALTER TABLE pattern)
**Plans**: 0/? planned

**Success Criteria:**
1. User can query ML predictions table and see kesim_id field linking each prediction to cut session
2. User can query ML predictions table and see makine_id field identifying machine for each prediction
3. User can query ML predictions table and see serit_id field identifying blade for each prediction
4. User can query ML predictions table and see malzeme_cinsi field identifying material for each prediction
5. Existing ML prediction records preserved after schema migration (no data loss)

#### Phase 18: Anomaly DB Schema Update — PENDING

**Goal**: Add traceability fields to anomaly events table
**Depends on**: Phase 17
**Requirements**: ANDB-01, ANDB-02, ANDB-03
**Research**: Unlikely (repeat Phase 17 pattern for anomaly database)
**Plans**: 0/? planned

**Success Criteria:**
1. User can query anomaly events table and see makine_id field identifying machine for each anomaly
2. User can query anomaly events table and see serit_id field identifying blade for each anomaly
3. User can query anomaly events table and see malzeme_cinsi field identifying material for each anomaly
4. Existing anomaly records preserved after schema migration (no data loss)

</details>

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
| 10. AI Mode Switch Fix | v1.4 | 1/1 | Complete | 2026-01-15 |
| 11. Initial Delay Logic | v1.4 | 1/1 | Complete | 2026-01-15 |
| 12. ML Prediction Parity Investigation & Fix | v1.5 | 1/1 | Complete | 2026-01-28 |
| 13. Unit Labels & Naming Fixes | v1.5 | 1/1 | Complete | 2026-01-28 |
| 14. Chart Axis Labels & Sapma Gauge Fix | v1.5 | 1/1 | Complete | 2026-01-28 |
| 15. Touch Long Press Fix | v1.6 | 0/? | Pending | — |
| 16. ML DB None Values Investigation | v1.6 | 0/? | Pending | — |
| 17. ML DB Schema Update | v1.6 | 0/? | Pending | — |
| 18. Anomaly DB Schema Update | v1.6 | 0/? | Pending | — |
