# Roadmap: Smart Saw Database Field Additions

## Overview

Database schema guncellemesi icin uc asamali uygulama. ML predictions tablosuna tork ve kafa yuksekligi alanlari, anomaly events tablosuna kafa yuksekligi alani eklenerek gecmise donuk analiz icin veri zenginlestirilecek.

## Domain Expertise

None

## Milestones

- [v1.0 Database Field Additions](milestones/v1.0-ROADMAP.md) (Phases 1-3) — SHIPPED 2026-01-15
- 🚧 **v1.1 Modbus Connection Resilience** - Phase 4 (in progress)

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

### 🚧 v1.1 Modbus Connection Resilience (In Progress)

**Milestone Goal:** Modbus bağlantısı olmadığında uygulamanın donmasını engellemek, proper timeout handling ile graceful error handling sağlamak.

#### Phase 4: Modbus Connection Timeout Handling

**Goal**: Fix blocking calls when Modbus connection unavailable - add proper timeout handling so application responds gracefully instead of freezing
**Depends on**: Previous milestone complete
**Research**: Unlikely (internal patterns - fixing timeout in existing code)
**Plans**: 1

Plans:
- [ ] 04-01: Connection cooldown and operation timeouts

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. ML Schema Update | v1.0 | 1/1 | Complete | 2026-01-15 |
| 2. Anomaly Schema Update | v1.0 | 1/1 | Complete | 2026-01-15 |
| 3. Data Population | v1.0 | 2/2 | Complete | 2026-01-15 |
| 4. Modbus Connection Timeout Handling | v1.1 | 0/1 | Planned | - |
