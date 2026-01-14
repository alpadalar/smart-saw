# Roadmap: Smart Saw Database Field Additions

## Overview

Database schema güncellemesi için üç aşamalı uygulama. ML predictions tablosuna tork ve kafa yüksekliği alanları, anomaly events tablosuna kafa yüksekliği alanı eklenerek geçmişe dönük analiz için veri zenginleştirilecek.

## Domain Expertise

None

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: ML Schema Update** - Add tork and kafa yüksekliği fields to ML predictions table
- [x] **Phase 2: Anomaly Schema Update** - Add kafa yüksekliği field to anomaly events table
- [ ] **Phase 3: Data Population** - Update data writing logic to populate new fields

## Phase Details

### Phase 1: ML Schema Update
**Goal**: ML predictions tablosuna serit_motor_tork ve kafa_yuksekligi alanlarını eklemek
**Depends on**: Nothing (first phase)
**Research**: Unlikely (internal database schema, existing patterns)
**Plans**: TBD

Plans:
- [x] 01-01: Schema migration for ML database

### Phase 2: Anomaly Schema Update
**Goal**: Anomaly events tablosuna kafa_yuksekligi alanını eklemek
**Depends on**: Phase 1
**Research**: Unlikely (internal database schema, existing patterns)
**Plans**: TBD

Plans:
- [x] 02-01: Schema migration for anomaly database

### Phase 3: Data Population
**Goal**: Yeni alanların veri yazma mantığına entegrasyonu
**Depends on**: Phase 2
**Research**: Unlikely (data already available in RawSensorData/ProcessedData)
**Plans**: 2 plans in 1 wave (parallel)

Plans:
- [ ] 03-01: Update ML data writing logic (ml_controller.py)
- [ ] 03-02: Update anomaly data writing logic (anomaly_tracker.py, data_processor.py)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. ML Schema Update | 1/1 | Complete | 2026-01-15 |
| 2. Anomaly Schema Update | 1/1 | Complete | 2026-01-15 |
| 3. Data Population | 0/2 | Planned | - |
