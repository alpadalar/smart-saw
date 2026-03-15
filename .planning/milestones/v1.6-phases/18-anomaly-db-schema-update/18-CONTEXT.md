# Phase 18: Anomaly DB Schema Update - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Add traceability fields (makine_id, serit_id, malzeme_cinsi) to anomaly events table. Enables historical analysis by linking anomaly events to machines, blades, and materials. Repeat of Phase 17 pattern applied to anomaly database.

</domain>

<decisions>
## Implementation Decisions

### Field Sources (carried from Phase 17)
- makine_id: From raw_data.makine_id (INTEGER, already available at record_anomaly call site in data_processor.py)
- serit_id: From raw_data.serit_id (INTEGER, already available at record_anomaly call site)
- malzeme_cinsi: From raw_data.malzeme_cinsi (TEXT, already available at record_anomaly call site)

### Default Values (carried from Phase 17)
- Existing records: NULL values — these anomaly events predate traceability
- Runtime unavailable: Store NULL when source unavailable — indicates genuinely missing

### Data Types (carried from Phase 17)
- makine_id: INTEGER (numeric machine ID)
- serit_id: INTEGER (numeric blade ID)
- malzeme_cinsi: TEXT (material type string, matches ML schema pattern)

### Nullability (carried from Phase 17)
- All three fields are optional (nullable) — no NOT NULL, no DEFAULT
- No anomaly events skipped due to missing traceability fields

### Indexing (carried from Phase 17)
- No indexes on makine_id, serit_id, malzeme_cinsi (low cardinality)
- Existing indexes on timestamp, sensor_name, kesim_id are sufficient

### Value Conversion (carried from Phase 17)
- Falsy-to-None conversion at call site — store NULL when source is 0 or empty string

### Claude's Discretion
- Column ordering within the schema definition
- Exact parameter ordering in record_anomaly() method signature

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Schema pattern
- `.planning/phases/17-ml-db-schema-update/17-RESEARCH.md` — Phase 17 research showing the exact ALTER TABLE + logging pattern to repeat
- `src/services/database/schemas.py` — SCHEMA_ANOMALY_DB definition (lines 231-245), SCHEMA_ML_DB for reference pattern

### Anomaly recording
- `src/services/processing/anomaly_tracker.py` — record_anomaly() method (line 74) that needs new parameters
- `src/services/processing/data_processor.py` — Call site (line 284) where raw_data fields are available

### Prior phase execution
- `.planning/phases/17-ml-db-schema-update/17-CONTEXT.md` — Phase 17 decisions that this phase carries forward

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `schemas.py` SCHEMA_ML_DB: Reference for how traceability columns were added (lines 219-223)
- Phase 17 commit: Exact pattern of schema + logging changes to replicate

### Established Patterns
- ALTER TABLE with nullable columns (no NOT NULL, no DEFAULT) — used in v1.0 and Phase 17
- SQLiteService auto schema mismatch detection and database recreation with backup
- Falsy-to-None conversion at call site before passing to tracker

### Integration Points
- `anomaly_tracker.py:record_anomaly()` — Add makine_id, serit_id, malzeme_cinsi parameters
- `data_processor.py:284` — Pass raw_data.makine_id, raw_data.serit_id, raw_data.malzeme_cinsi at existing call site
- `schemas.py:SCHEMA_ANOMALY_DB` — Add three columns to anomaly_events CREATE TABLE

</code_context>

<specifics>
## Specific Ideas

No specific requirements — direct repeat of Phase 17 pattern for anomaly database.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 18-anomaly-db-schema-update*
*Context gathered: 2026-03-16*
