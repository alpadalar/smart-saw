# Phase 17: ML DB Schema Update - Context

**Gathered:** 2026-02-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Add traceability fields (kesim_id, makine_id, serit_id, malzeme_cinsi) to ML predictions table. Enables historical analysis by linking predictions to cut sessions, machines, blades, and materials.

</domain>

<decisions>
## Implementation Decisions

### Field Sources
- kesim_id: From active KesimSession or cut tracking system (there's a running session ID)
- makine_id: From runtime state (DataProcessor or similar runtime object)
- serit_id: From local state (stored locally in DataProcessor or config)
- malzeme_cinsi: From local state (from operator input or job setup)

### Default Values
- Existing records: NULL values — these predictions predate traceability
- Runtime unavailable: Store NULL when source unavailable — indicates genuinely missing

### Data Types
- kesim_id: INTEGER (numeric ID matching existing session tracking)
- makine_id: INTEGER (numeric machine ID)
- serit_id: INTEGER (numeric blade ID)
- malzeme_cinsi: Claude's discretion (match existing material tracking pattern)

### Nullability
- All four fields are optional (nullable) — graceful degradation if source unavailable
- No predictions skipped due to missing traceability fields

### Claude's Discretion
- malzeme_cinsi data type (TEXT vs INTEGER based on existing pattern)
- Whether to add indexes on traceability fields for query performance
- Foreign key constraints based on existing schema patterns

</decisions>

<specifics>
## Specific Ideas

No specific requirements — follow established v1.0 ALTER TABLE pattern from earlier phases.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 17-ml-db-schema-update*
*Context gathered: 2026-02-04*
