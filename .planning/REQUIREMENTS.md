# Requirements: Smart Saw v1.6

**Defined:** 2026-01-29
**Core Value:** Dokunmatik ekran kullanilabilirligi ve veritabani veri izlenebilirligi

## v1.6 Requirements

Requirements for v1.6 Touch UX & Data Traceability milestone. Each maps to roadmap phases.

### Touch UX

- [x] **TOUCH-01**: User can long press positioning buttons with touch input (testere konumlandirma, malzeme konumlandirma) — completed 2026-01-30
- [x] **TOUCH-02**: Mouse long press continues to work on positioning buttons (no regression) — completed 2026-01-30
- [x] **TOUCH-03**: Visual feedback appears when touch press is detected on positioning buttons — completed 2026-01-30

### ML Database

- [x] **MLDB-01**: ML predictions table includes kesim_id field linking to cut sessions
- [x] **MLDB-02**: ML predictions table includes makine_id field for machine identification
- [x] **MLDB-03**: ML predictions table includes serit_id field for blade identification
- [x] **MLDB-04**: ML predictions table includes malzeme_cinsi field for material type
- [ ] **MLDB-05**: yeni_kesme_hizi, yeni_inme_hizi, katsayi fields contain actual values (not None)

### Anomaly Database

- [x] **ANDB-01**: Anomaly events table includes makine_id field for machine identification
- [x] **ANDB-02**: Anomaly events table includes serit_id field for blade identification
- [x] **ANDB-03**: Anomaly events table includes malzeme_cinsi field for material type

## Future Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### Touch UX Enhancements

- **TOUCH-F01**: Configurable long press duration threshold
- **TOUCH-F02**: Haptic feedback on touchscreen devices (hardware dependent)

### Database Enhancements

- **DB-F01**: Audit trail for database changes (who, when, what)
- **DB-F02**: Data export functionality for traceability reports

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Multi-touch gestures | Not needed for positioning buttons - simple hold action |
| Touch gestures (swipe, pinch) | Industrial HMI - button-based interface preferred |
| Database migration framework (Alembic) | Overkill - SQLite ALTER TABLE sufficient |
| Real-time traceability dashboards | Data collection focus first, visualization later |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TOUCH-01 | Phase 15 | Pending |
| TOUCH-02 | Phase 15 | Pending |
| TOUCH-03 | Phase 15 | Pending |
| MLDB-01 | Phase 17 | Complete |
| MLDB-02 | Phase 17 | Complete |
| MLDB-03 | Phase 17 | Complete |
| MLDB-04 | Phase 17 | Complete |
| MLDB-05 | Phase 16 | Pending |
| ANDB-01 | Phase 18 | Complete |
| ANDB-02 | Phase 18 | Complete |
| ANDB-03 | Phase 18 | Complete |

**Coverage:**
- v1.6 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0

---
*Requirements defined: 2026-01-29*
*Last updated: 2026-01-29 after roadmap creation*
