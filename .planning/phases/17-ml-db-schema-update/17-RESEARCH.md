# Phase 17: ML DB Schema Update - Research

**Researched:** 2026-03-16
**Domain:** SQLite schema migration, ML prediction logging
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Field Sources**
- kesim_id: From active KesimSession or cut tracking system (there's a running session ID)
- makine_id: From runtime state (DataProcessor or similar runtime object)
- serit_id: From local state (stored locally in DataProcessor or config)
- malzeme_cinsi: From local state (from operator input or job setup)

**Default Values**
- Existing records: NULL values — these predictions predate traceability
- Runtime unavailable: Store NULL when source unavailable — indicates genuinely missing

**Data Types**
- kesim_id: INTEGER (numeric ID matching existing session tracking)
- makine_id: INTEGER (numeric machine ID)
- serit_id: INTEGER (numeric blade ID)
- malzeme_cinsi: Claude's discretion (match existing material tracking pattern)

**Nullability**
- All four fields are optional (nullable) — graceful degradation if source unavailable
- No predictions skipped due to missing traceability fields

### Claude's Discretion
- malzeme_cinsi data type (TEXT vs INTEGER based on existing pattern)
- Whether to add indexes on traceability fields for query performance
- Foreign key constraints based on existing schema patterns

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MLDB-01 | ML predictions table includes kesim_id field linking to cut sessions | CuttingTracker.get_current_kesim_id() already exists; `processed_data.cutting_session_id` is the value to pass through |
| MLDB-02 | ML predictions table includes makine_id field for machine identification | raw_data.makine_id (INTEGER) already available in RawSensorData; accessible from processed_data.raw_data in MLController |
| MLDB-03 | ML predictions table includes serit_id field for blade identification | raw_data.serit_id (INTEGER) already available in RawSensorData; accessible from processed_data.raw_data in MLController |
| MLDB-04 | ML predictions table includes malzeme_cinsi field for material type | raw_data.malzeme_cinsi (TEXT str) already available in RawSensorData; use TEXT type to match existing pattern |
</phase_requirements>

---

## Summary

Phase 17 adds four traceability fields to the `ml_predictions` table in `ml.db`. The work is straightforward: update the schema definition in `schemas.py` and update the `_log_ml_prediction` method in `ml_controller.py` to pass the new values. This is the same two-file pattern used in Phases 1 and 3 (schema update + data population).

All four values are already present in `RawSensorData` (the data object flowing through the pipeline at prediction time). The MLController already receives `processed_data` which contains `raw_data` with `makine_id`, `serit_id`, and `malzeme_cinsi`. The `cutting_session_id` is available on `processed_data` directly. No new data sources, no new service dependencies.

The `SQLiteService` has a schema-mismatch auto-recovery mechanism: if an existing `ml.db` has the old schema and a write is attempted with new columns, the service backs up and recreates the database. This means new schema columns added to `SCHEMA_ML_DB` will be picked up on next startup for fresh databases, and existing databases will be migrated automatically via the backup-and-recreate path if a mismatch is detected.

**Primary recommendation:** Update `SCHEMA_ML_DB` in `schemas.py` to add four nullable columns, then update `_log_ml_prediction` in `ml_controller.py` to populate them from `processed_data.raw_data`.

---

## Standard Stack

### Core
| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| SQLite (stdlib `sqlite3`) | Python 3.10+ | Database engine | Already used; zero new dependencies |
| `schemas.py` | project-local | Schema SQL string definitions | Single source of truth for all table schemas |
| `ml_controller.py` `_log_ml_prediction` | project-local | ML prediction INSERT logic | Existing logging path; modify in-place |

### No New Dependencies Required
All data sources are already in-scope at the logging call site. No additional libraries or services needed.

---

## Architecture Patterns

### Established v1.0 Pattern: Two-File Schema + Population

Every prior schema addition in this project follows an identical two-step pattern:

**Step 1 — Schema definition** (`src/services/database/schemas.py`)
Add new columns to the `CREATE TABLE IF NOT EXISTS` SQL string. New columns must be nullable (no `NOT NULL`, no `DEFAULT`) so fresh database creation works and `SQLiteService`'s schema-mismatch auto-recreation works correctly.

**Step 2 — Data population** (the file that does the INSERT)
Add the new column names to the INSERT column list, add values to the params tuple, and add the new values to the method signature if needed.

This was done in Phase 1+3 for `serit_motor_tork` and `kafa_yuksekligi`. Phase 17 repeats the exact same pattern for the four traceability fields.

### Recommended Project Structure (unchanged)
```
src/
├── services/database/schemas.py         # Step 1: add columns to SCHEMA_ML_DB
├── services/control/ml_controller.py    # Step 2: update _log_ml_prediction
└── (no other files need modification)
```

### Pattern: Nullable Column Addition to SQLite

SQLite `ALTER TABLE ... ADD COLUMN` is the standard migration command but this project does NOT use `ALTER TABLE`. Instead, the `SQLiteService._backup_and_recreate_database()` mechanism handles existing databases automatically when a schema mismatch is detected on the first write attempt. The schema definition in `SCHEMA_ML_DB` is the only source that needs updating.

```python
# Source: src/services/database/schemas.py (SCHEMA_ML_DB pattern)
# Add after existing columns, before closing parenthesis:
#
#     -- Traceability fields
#     kesim_id INTEGER,         -- Cut session ID (NULL if session unavailable)
#     makine_id INTEGER,        -- Machine ID (NULL if unavailable)
#     serit_id INTEGER,         -- Blade ID (NULL if unavailable)
#     malzeme_cinsi TEXT        -- Material type (NULL if unavailable)
```

### Pattern: _log_ml_prediction Extension

The current `_log_ml_prediction` signature (ml_controller.py line ~743):
```python
def _log_ml_prediction(
    self,
    input_df,
    coefficient: float,
    serit_motor_tork: float,
    kafa_yuksekligi: float,
    yeni_kesme_hizi: float,
    yeni_inme_hizi: float,
    katsayi: float
):
```

The call site is in `calculate_speeds` (line ~233–242). `processed_data` is already in scope at the call site, which means all four new values are reachable without changing method signatures upstream.

Values available at the `_log_ml_prediction` call site:
- `processed_data.cutting_session_id` — Optional[int], the kesim_id
- `processed_data.raw_data.makine_id` — int
- `processed_data.raw_data.serit_id` — int
- `processed_data.raw_data.malzeme_cinsi` — str (TEXT)

### malzeme_cinsi Data Type Decision (Claude's Discretion)

**Use TEXT.** Evidence:
1. `RawSensorData.malzeme_cinsi` is declared as `str = ""` (models.py line 66)
2. `sensor_data` table in `SCHEMA_TOTAL_DB` stores `malzeme_cinsi TEXT` (schemas.py line 128)
3. The raw register `reg_1006_malzeme_cinsi` is INTEGER in raw_registers, but by the time it reaches `RawSensorData` it has been decoded/converted to a string label

Storing as TEXT in ml_predictions is consistent with how `sensor_data` (total.db) stores the same field.

### Index Decision (Claude's Discretion)

**Add index on `kesim_id` only.** Reasoning:
- `kesim_id` is the primary foreign-key-like join column — queries like "show all ML predictions for cut session 42" will filter on this
- `makine_id` and `serit_id` are low-cardinality on a single-machine deployment; no index needed
- `malzeme_cinsi` is text, low query frequency; no index needed
- Existing precedent: `idx_ml_timestamp` already exists; `idx_anomaly_kesim` exists on anomaly_events table which has the same pattern

```sql
CREATE INDEX IF NOT EXISTS idx_ml_kesim_id ON ml_predictions(kesim_id);
```

### Foreign Key Constraints (Claude's Discretion)

**Do not add foreign key constraints.** Reasoning:
- No existing table in this project uses `FOREIGN KEY` constraints (confirmed by reviewing all schemas in schemas.py)
- SQLite foreign key enforcement requires `PRAGMA foreign_keys=ON` at each connection — not set anywhere in `SQLiteService`
- NULL values in kesim_id (for predictions outside a cut session) would require `DEFERRABLE` or `MATCH PARTIAL`, which adds complexity
- The project's philosophy is lightweight SQLite without relational enforcement

### Anti-Patterns to Avoid

- **ALTER TABLE at startup:** This project does not run migration scripts. Do not add `ALTER TABLE` to initialization code. The `SCHEMA_ML_DB` string is the schema definition; `SQLiteService` handles fresh vs. existing databases.
- **Changing `_log_ml_prediction` call signature upstream of `calculate_speeds`:** `processed_data` is already available at the call site; pass values from it directly without touching `_predict_coefficient` or the `calculate_speeds` public interface.
- **NOT NULL columns without DEFAULT:** All four new columns must remain nullable. The schema has no migration path for existing rows; `NOT NULL` would break the backup-and-recreate pattern on retry.
- **Skipping predictions when traceability fields are None:** User decision is graceful degradation — store NULL, never skip the log entry.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema migration | Custom ALTER TABLE migration script | Update `SCHEMA_ML_DB` string + rely on `SQLiteService` auto-recreation | Existing mechanism already handles schema mismatches with backup |
| Accessing kesim_id | New CuttingTracker method or direct DB query | `processed_data.cutting_session_id` | Already populated by `CuttingTracker.update()` in `_process_raw_data` and stored on `ProcessedData` |
| Accessing makine_id/serit_id | New Modbus read or config lookup | `processed_data.raw_data.makine_id` / `.serit_id` | Already read from PLC at 10 Hz and stored in RawSensorData |

---

## Common Pitfalls

### Pitfall 1: Wrong Parameter Passing Path
**What goes wrong:** Developer adds parameters to `_predict_coefficient` to get traceability values there, as Phase 3 did for a different reason. This adds unnecessary complexity.
**Why it happens:** `_predict_coefficient` was modified in Phase 3 to pass `raw_data` — developer follows that pattern by reflex.
**How to avoid:** The `_log_ml_prediction` call is in `calculate_speeds` where `processed_data` is already in scope. Pass the four new values directly at the call site without touching `_predict_coefficient`.
**Warning signs:** If you're modifying `_predict_coefficient`'s signature for this phase, stop — that's unnecessary.

### Pitfall 2: Schema String Placement
**What goes wrong:** New columns added AFTER the closing parenthesis of the CREATE TABLE, or inserted between existing columns in a way that breaks the SQL.
**Why it happens:** SQL string manipulation without running a syntax check.
**How to avoid:** Place new columns at the end of the column list, before the closing `)`. Verify with `python -m py_compile src/services/database/schemas.py`.

### Pitfall 3: Mismatched INSERT Parameter Count
**What goes wrong:** Adding 4 columns to the INSERT column list but only 3 `?` placeholders (or vice versa), causing `sqlite3.ProgrammingError: Binding X has no name`.
**Why it happens:** Counting columns and `?` markers separately.
**How to avoid:** After updating both the column list and params tuple, count: columns in INSERT = count of `?` = len(params tuple). Run `python -m py_compile src/services/control/ml_controller.py`.

### Pitfall 4: Using INTEGER for malzeme_cinsi
**What goes wrong:** Storing the raw integer register value instead of the string label, inconsistent with how `sensor_data` stores the same field.
**Why it happens:** The raw register `reg_1006_malzeme_cinsi` is INTEGER; developer copies that type.
**How to avoid:** Use TEXT. `RawSensorData.malzeme_cinsi` is already a `str`; the conversion from register integer to string happens in the Modbus reader layer before it reaches this code.

---

## Code Examples

### Updated SCHEMA_ML_DB (schemas.py)

```python
# Source: src/services/database/schemas.py — SCHEMA_ML_DB
SCHEMA_ML_DB = """
CREATE TABLE IF NOT EXISTS ml_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,

    -- Input features
    akim_input REAL,
    sapma_input REAL,
    kesme_hizi_input REAL,
    inme_hizi_input REAL,
    serit_motor_tork REAL,  -- Band motor torque (%)
    kafa_yuksekligi REAL,   -- Head height (mm)

    -- Output speeds
    yeni_kesme_hizi REAL,
    yeni_inme_hizi REAL,

    -- ML outputs
    katsayi REAL,
    ml_output REAL,

    -- Traceability fields
    kesim_id INTEGER,       -- Cut session ID (NULL if not cutting)
    makine_id INTEGER,      -- Machine ID
    serit_id INTEGER,       -- Blade ID
    malzeme_cinsi TEXT      -- Material type
);

CREATE INDEX IF NOT EXISTS idx_ml_timestamp ON ml_predictions(timestamp);
CREATE INDEX IF NOT EXISTS idx_ml_kesim_id ON ml_predictions(kesim_id);
"""
```

### Updated _log_ml_prediction signature and SQL (ml_controller.py)

```python
# Source: src/services/control/ml_controller.py
def _log_ml_prediction(
    self,
    input_df,
    coefficient: float,
    serit_motor_tork: float,
    kafa_yuksekligi: float,
    yeni_kesme_hizi: float,
    yeni_inme_hizi: float,
    katsayi: float,
    kesim_id: Optional[int] = None,
    makine_id: Optional[int] = None,
    serit_id: Optional[int] = None,
    malzeme_cinsi: Optional[str] = None
):
    sql = """
        INSERT INTO ml_predictions (
            timestamp,
            akim_input,
            sapma_input,
            kesme_hizi_input,
            inme_hizi_input,
            serit_motor_tork,
            kafa_yuksekligi,
            yeni_kesme_hizi,
            yeni_inme_hizi,
            katsayi,
            ml_output,
            kesim_id,
            makine_id,
            serit_id,
            malzeme_cinsi
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        datetime.now().isoformat(),
        float(input_df['akim_input'].iloc[0]),
        float(input_df['sapma_input'].iloc[0]),
        float(input_df['kesme_hizi'].iloc[0]),
        float(input_df['inme_hizi'].iloc[0]),
        float(serit_motor_tork),
        float(kafa_yuksekligi),
        float(yeni_kesme_hizi),
        float(yeni_inme_hizi),
        float(katsayi),
        float(coefficient),
        kesim_id,          # int or None
        makine_id,         # int or None
        serit_id,          # int or None
        malzeme_cinsi      # str or None
    )
    self.db.write_async(sql, params)
```

### Updated call site in calculate_speeds (ml_controller.py)

```python
# Source: src/services/control/ml_controller.py — calculate_speeds(), around line 233
# Current call:
self._log_ml_prediction(
    input_df,
    coefficient,
    raw_data.serit_motor_tork_percentage,
    raw_data.kafa_yuksekligi_mm,
    speed_changes['kesme_hizi'],
    speed_changes['inme_hizi'],
    self.katsayi
)

# Updated call:
self._log_ml_prediction(
    input_df,
    coefficient,
    raw_data.serit_motor_tork_percentage,
    raw_data.kafa_yuksekligi_mm,
    speed_changes['kesme_hizi'],
    speed_changes['inme_hizi'],
    self.katsayi,
    kesim_id=processed_data.cutting_session_id,
    makine_id=raw_data.makine_id if raw_data.makine_id else None,
    serit_id=raw_data.serit_id if raw_data.serit_id else None,
    malzeme_cinsi=raw_data.malzeme_cinsi if raw_data.malzeme_cinsi else None
)
```

Note: `processed_data` is already in scope in `calculate_speeds` — it is the method's input parameter.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Schema-only update (Phases 1-2) | Schema update + data population (Phases 1-3 together) | v1.0 | Phase 17 is both in one go |
| No traceability in ml_predictions | Add kesim_id, makine_id, serit_id, malzeme_cinsi | Phase 17 | Enables session-level ML analysis |

---

## Open Questions

1. **makine_id default value of 1**
   - What we know: `RawSensorData.makine_id` defaults to `int = 1` (models.py line 62), meaning it will never be `None` or `0` from the model layer even if the PLC hasn't provided it yet.
   - What's unclear: Should `makine_id=1` be stored as-is, or treated as "not set" and stored as NULL?
   - Recommendation: Store as-is (integer 1). The user decision says "store NULL when source unavailable" — `1` is a valid PLC-provided value. If `raw_data.makine_id` equals the PLC default, that reflects the actual register value. The conversion to None in the call site example above (`if raw_data.makine_id else None`) would convert `0` to NULL but not `1`. Only use `None` if PLC explicitly signals "unknown" with a zero or sentinel.

2. **serit_id default value of 1**
   - Same consideration as makine_id above. Default is `int = 1`.
   - Recommendation: Same — store as-is unless PLC signals 0 (which would be falsy).

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None detected — no test files, no pytest.ini |
| Config file | None — Wave 0 gap |
| Quick run command | `python -m py_compile src/services/database/schemas.py && python -m py_compile src/services/control/ml_controller.py` |
| Full suite command | Same (no test suite exists) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MLDB-01 | ml_predictions table has kesim_id column | smoke | `python -c "from src.services.database.schemas import SCHEMA_ML_DB; assert 'kesim_id' in SCHEMA_ML_DB"` | ❌ inline |
| MLDB-02 | ml_predictions table has makine_id column | smoke | `python -c "from src.services.database.schemas import SCHEMA_ML_DB; assert 'makine_id' in SCHEMA_ML_DB"` | ❌ inline |
| MLDB-03 | ml_predictions table has serit_id column | smoke | `python -c "from src.services.database.schemas import SCHEMA_ML_DB; assert 'serit_id' in SCHEMA_ML_DB"` | ❌ inline |
| MLDB-04 | ml_predictions table has malzeme_cinsi column | smoke | `python -c "from src.services.database.schemas import SCHEMA_ML_DB; assert 'malzeme_cinsi' in SCHEMA_ML_DB"` | ❌ inline |

### Sampling Rate
- **Per task commit:** `python -m py_compile src/services/database/schemas.py && python -m py_compile src/services/control/ml_controller.py`
- **Per wave merge:** Same (no test suite)
- **Phase gate:** Column presence checks + compile checks green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] No test infrastructure exists — project has no pytest setup
- [ ] Column presence can be verified inline without a test framework using `python -c` one-liners as shown above

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `src/services/database/schemas.py` — current SCHEMA_ML_DB definition, existing column pattern
- Direct code inspection: `src/services/control/ml_controller.py` — `_log_ml_prediction` method signature and call site
- Direct code inspection: `src/domain/models.py` — `RawSensorData` field types, confirming makine_id (int), serit_id (int), malzeme_cinsi (str)
- Direct code inspection: `src/services/processing/data_processor.py` — `processed_data.cutting_session_id` is already populated and in scope
- Direct code inspection: `.planning/phases/01-ml-schema-update/01-01-PLAN.md` and `.planning/phases/03-data-population/03-01-PLAN.md` — established two-file pattern
- Direct code inspection: `src/services/database/sqlite_service.py` — auto-recreation mechanism via `_backup_and_recreate_database`

### Secondary (MEDIUM confidence)
- `src/services/database/schemas.py` SCHEMA_TOTAL_DB confirms `malzeme_cinsi TEXT` is the project standard for that field in processed-data tables

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — same SQLite + project files used in all prior phases
- Architecture: HIGH — established two-file pattern verified in Phase 1/3 plans and current code
- Pitfalls: HIGH — derived from direct code inspection of the exact files being modified
- Data sources: HIGH — all four values confirmed present in RawSensorData and ProcessedData at the call site

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable codebase, no fast-moving dependencies)
