# Phase 18: Anomaly DB Schema Update - Research

**Researched:** 2026-03-16
**Domain:** SQLite schema migration, anomaly event logging
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Field Sources (carried from Phase 17)**
- makine_id: From raw_data.makine_id (INTEGER, already available at record_anomaly call site in data_processor.py)
- serit_id: From raw_data.serit_id (INTEGER, already available at record_anomaly call site)
- malzeme_cinsi: From raw_data.malzeme_cinsi (TEXT, already available at record_anomaly call site)

**Default Values (carried from Phase 17)**
- Existing records: NULL values — these anomaly events predate traceability
- Runtime unavailable: Store NULL when source unavailable — indicates genuinely missing

**Data Types (carried from Phase 17)**
- makine_id: INTEGER (numeric machine ID)
- serit_id: INTEGER (numeric blade ID)
- malzeme_cinsi: TEXT (material type string, matches ML schema pattern)

**Nullability (carried from Phase 17)**
- All three fields are optional (nullable) — no NOT NULL, no DEFAULT
- No anomaly events skipped due to missing traceability fields

**Indexing (carried from Phase 17)**
- No indexes on makine_id, serit_id, malzeme_cinsi (low cardinality)
- Existing indexes on timestamp, sensor_name, kesim_id are sufficient

**Value Conversion (carried from Phase 17)**
- Falsy-to-None conversion at call site — store NULL when source is 0 or empty string

### Claude's Discretion
- Column ordering within the schema definition
- Exact parameter ordering in record_anomaly() method signature

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ANDB-01 | Anomaly events table includes makine_id field for machine identification | raw_data.makine_id (int) is in scope at the record_anomaly call site (data_processor.py line 284); pass with falsy-to-None conversion |
| ANDB-02 | Anomaly events table includes serit_id field for blade identification | raw_data.serit_id (int) is in scope at the record_anomaly call site (data_processor.py line 284); pass with falsy-to-None conversion |
| ANDB-03 | Anomaly events table includes malzeme_cinsi field for material type | raw_data.malzeme_cinsi (str) is in scope at the record_anomaly call site (data_processor.py line 284); pass with falsy-to-None conversion |
</phase_requirements>

---

## Summary

Phase 18 is a direct repeat of the Phase 17 pattern applied to the anomaly database. Three traceability fields (makine_id, serit_id, malzeme_cinsi) are added to the `anomaly_events` table in `anomaly.db`. The work touches exactly two files: `schemas.py` (SCHEMA_ANOMALY_DB definition) and `anomaly_tracker.py` (record_anomaly signature + _save_anomaly_to_db SQL).

All three values are already present as `raw_data` fields at the exact call site (data_processor.py line 284) where `record_anomaly` is called. The `raw_data` object is the local parameter of `_process_raw_data`, and `raw_data.makine_id`, `raw_data.serit_id`, and `raw_data.malzeme_cinsi` are all populated from PLC Modbus registers before that point.

The `SQLiteService` auto-recreation mechanism handles existing `anomaly.db` instances automatically: if a schema mismatch is detected on the first write, it backs up and recreates the database from the updated schema string. No migration scripts or ALTER TABLE statements are needed.

**Primary recommendation:** Add three nullable columns to `SCHEMA_ANOMALY_DB` in `schemas.py`, then update `record_anomaly()` and `_save_anomaly_to_db()` in `anomaly_tracker.py` to accept and store the new values. Pass the values with falsy-to-None conversion at the call site in `data_processor.py`.

---

## Standard Stack

### Core
| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| SQLite (stdlib `sqlite3`) | Python 3.10+ | Database engine | Already used; zero new dependencies |
| `schemas.py` | project-local | Schema SQL string definitions | Single source of truth for all table schemas |
| `anomaly_tracker.py` `record_anomaly` / `_save_anomaly_to_db` | project-local | Anomaly event INSERT logic | Existing logging path; modify in-place |

### No New Dependencies Required
All data sources are already in scope at the logging call site. No additional libraries or services needed.

---

## Architecture Patterns

### Established v1.0 Pattern: Two-File Schema + Population

Every prior schema addition in this project follows an identical two-step pattern:

**Step 1 — Schema definition** (`src/services/database/schemas.py`)
Add new columns to the `CREATE TABLE IF NOT EXISTS` SQL string. New columns must be nullable (no `NOT NULL`, no `DEFAULT`) so fresh database creation works and `SQLiteService`'s schema-mismatch auto-recreation works correctly.

**Step 2 — Data population** (the file that does the INSERT)
Add the new column names to the INSERT column list, add `?` placeholders to the VALUES clause, add the new values to the params tuple, and update the method signature if needed.

Phase 17 repeated this pattern for `ml_predictions`. Phase 18 repeats it for `anomaly_events`.

### Recommended Project Structure (unchanged)
```
src/
├── services/database/schemas.py                   # Step 1: add columns to SCHEMA_ANOMALY_DB
├── services/processing/anomaly_tracker.py         # Step 2: update record_anomaly + _save_anomaly_to_db
└── services/processing/data_processor.py          # Step 3: pass values at call site (line 284)
```

Note: Phase 17 only needed two files because the call site was already in the file being modified. Phase 18 requires touching three files: the schema, the tracker (which owns the INSERT), and the data processor (the call site that invokes the tracker). The call site modification is a small keyword-argument addition.

### Pattern: Nullable Column Addition to SCHEMA_ANOMALY_DB

```python
# Source: src/services/database/schemas.py (SCHEMA_ANOMALY_DB)
# Current anomaly_events columns end with:
#     kesim_id INTEGER,
#     kafa_yuksekligi REAL  -- Head height at anomaly detection (mm)
#
# Add after kafa_yuksekligi, before closing parenthesis:
#
#     -- Traceability fields
#     makine_id INTEGER,       -- Machine ID (NULL if unavailable)
#     serit_id INTEGER,        -- Blade ID (NULL if unavailable)
#     malzeme_cinsi TEXT       -- Material type (NULL if unavailable)
```

### Pattern: record_anomaly Extension

Current `record_anomaly` signature (`anomaly_tracker.py` lines 74-81):
```python
def record_anomaly(
    self,
    sensor_name: str,
    sensor_value: float,
    detection_method: str = "unknown",
    kesim_id: Optional[int] = None,
    kafa_yuksekligi: Optional[float] = None
):
```

Three new optional keyword parameters are appended. The existing `_save_anomaly_to_db` private method handles the actual INSERT and must also be updated.

### Pattern: Call Site in data_processor.py

Current call at line 284 (inside the `for sensor_name, is_anomaly in anomaly_results.items()` loop in `_process_raw_data`):
```python
self.anomaly_tracker.record_anomaly(
    sensor_name=sensor_name,
    sensor_value=sensor_value,
    detection_method=self.anomaly_manager.get_method_for_sensor(sensor_name),
    kesim_id=kesim_id,
    kafa_yuksekligi=raw_data.kafa_yuksekligi_mm
)
```

`raw_data` is the parameter of `_process_raw_data` and is directly accessible here. No new variable lookups needed.

### Anti-Patterns to Avoid

- **ALTER TABLE at startup:** This project does not run migration scripts. Do not add `ALTER TABLE` to initialization code.
- **NOT NULL columns without DEFAULT:** All three new columns must remain nullable. The `SQLiteService` backup-and-recreate path cannot handle `NOT NULL` without defaults on existing rows.
- **Skipping anomaly events when traceability fields are None:** User decision is graceful degradation — store NULL, never skip the record.
- **Modifying `record_anomaly`'s callers other than data_processor.py:** Check if there are any other call sites before assuming data_processor.py is the only one.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema migration | Custom ALTER TABLE script | Update `SCHEMA_ANOMALY_DB` string + rely on `SQLiteService` auto-recreation | Existing mechanism already handles schema mismatches with backup |
| Accessing makine_id / serit_id | New Modbus read or config lookup | `raw_data.makine_id` / `.serit_id` at the record_anomaly call site | Already read from PLC at 10 Hz and stored in RawSensorData |
| Accessing malzeme_cinsi | String decoding logic | `raw_data.malzeme_cinsi` (already a str) | Conversion from register integer to string label happens in Modbus reader layer |

---

## Common Pitfalls

### Pitfall 1: Missing Other record_anomaly Call Sites

**What goes wrong:** Developer updates only the data_processor.py call site but there are additional callers of `record_anomaly` elsewhere that also need updating.
**Why it happens:** Assuming there is only one call site without checking.
**How to avoid:** Grep for `record_anomaly` across the entire codebase before finalizing the plan. Confirm all call sites.
**Warning signs:** If `record_anomaly` is called from anywhere other than data_processor.py, those callers need compatible (keyword-argument) updates too — or the new parameters must be optional with defaults (which they are, so existing callers continue to work without modification).

### Pitfall 2: Schema String Placement

**What goes wrong:** New columns added after the closing `)` of the CREATE TABLE, or inserted between existing columns in a way that breaks the SQL.
**Why it happens:** SQL string manipulation without a syntax check.
**How to avoid:** Place new columns at the end of the `anomaly_events` column list, before the closing `)`. Verify with `python -m py_compile src/services/database/schemas.py`.

### Pitfall 3: Mismatched INSERT Parameter Count in _save_anomaly_to_db

**What goes wrong:** Adding 3 columns to the INSERT column list but miscounting `?` placeholders or params tuple entries, causing `sqlite3.ProgrammingError`.
**Why it happens:** Counting columns and `?` markers separately.
**How to avoid:** After updating INSERT column list, VALUES clause, and params tuple — count: columns in INSERT = count of `?` = len(params tuple). Compile-check with `python -m py_compile src/services/processing/anomaly_tracker.py`.

### Pitfall 4: Forgetting _save_anomaly_to_db When Updating record_anomaly

**What goes wrong:** Developer updates the `record_anomaly` public signature but forgets that it delegates to `_save_anomaly_to_db`, which has its own separate INSERT SQL and params tuple.
**Why it happens:** Two-method delegation pattern is easy to partially update.
**How to avoid:** `record_anomaly` calls `self._save_anomaly_to_db(...)` — both methods must be updated together.

### Pitfall 5: Falsy-to-None Conversion Omitted

**What goes wrong:** `raw_data.makine_id` (default `int = 1`) or `raw_data.serit_id` (default `int = 1`) passed directly without falsy-to-None conversion. For `malzeme_cinsi`, passing an empty string `""` instead of `None`.
**Why it happens:** Copying the raw field reference without the conversion guard.
**How to avoid:** Apply the same conversion as Phase 17: `raw_data.makine_id if raw_data.makine_id else None`, `raw_data.serit_id if raw_data.serit_id else None`, `raw_data.malzeme_cinsi if raw_data.malzeme_cinsi else None`. Note: this converts `0` to NULL but stores `1` as-is (see Open Questions below).

---

## Code Examples

### Updated SCHEMA_ANOMALY_DB (schemas.py)

```python
# Source: src/services/database/schemas.py — SCHEMA_ANOMALY_DB
SCHEMA_ANOMALY_DB = """
-- Individual anomaly events
CREATE TABLE IF NOT EXISTS anomaly_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    sensor_name TEXT NOT NULL,
    sensor_value REAL,
    detection_method TEXT,
    kesim_id INTEGER,
    kafa_yuksekligi REAL,  -- Head height at anomaly detection (mm)

    -- Traceability fields
    makine_id INTEGER,      -- Machine ID
    serit_id INTEGER,       -- Blade ID
    malzeme_cinsi TEXT      -- Material type
);

CREATE INDEX IF NOT EXISTS idx_anomaly_timestamp ON anomaly_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_anomaly_sensor ON anomaly_events(sensor_name);
CREATE INDEX IF NOT EXISTS idx_anomaly_kesim ON anomaly_events(kesim_id);

-- Reset history (tracks when anomalies were cleared)
CREATE TABLE IF NOT EXISTS anomaly_resets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reset_time TEXT NOT NULL,
    reset_by TEXT DEFAULT 'user'
);

CREATE INDEX IF NOT EXISTS idx_reset_time ON anomaly_resets(reset_time);
"""
```

### Updated record_anomaly signature (anomaly_tracker.py)

```python
# Source: src/services/processing/anomaly_tracker.py
def record_anomaly(
    self,
    sensor_name: str,
    sensor_value: float,
    detection_method: str = "unknown",
    kesim_id: Optional[int] = None,
    kafa_yuksekligi: Optional[float] = None,
    makine_id: Optional[int] = None,
    serit_id: Optional[int] = None,
    malzeme_cinsi: Optional[str] = None
):
    # ...
    if self.db:
        self._save_anomaly_to_db(
            timestamp=now,
            sensor_name=sensor_name,
            sensor_value=sensor_value,
            detection_method=detection_method,
            kesim_id=kesim_id,
            kafa_yuksekligi=kafa_yuksekligi,
            makine_id=makine_id,
            serit_id=serit_id,
            malzeme_cinsi=malzeme_cinsi
        )
```

### Updated _save_anomaly_to_db (anomaly_tracker.py)

```python
# Source: src/services/processing/anomaly_tracker.py
def _save_anomaly_to_db(
    self,
    timestamp: datetime,
    sensor_name: str,
    sensor_value: float,
    detection_method: str,
    kesim_id: Optional[int],
    kafa_yuksekligi: Optional[float],
    makine_id: Optional[int] = None,
    serit_id: Optional[int] = None,
    malzeme_cinsi: Optional[str] = None
):
    try:
        sql = """
            INSERT INTO anomaly_events (
                timestamp,
                sensor_name,
                sensor_value,
                detection_method,
                kesim_id,
                kafa_yuksekligi,
                makine_id,
                serit_id,
                malzeme_cinsi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            timestamp.isoformat(),
            sensor_name,
            sensor_value,
            detection_method,
            kesim_id,
            kafa_yuksekligi,
            makine_id,     # int or None
            serit_id,      # int or None
            malzeme_cinsi  # str or None
        )
        self.db.write_async(sql, params)
    except Exception as e:
        logger.error(f"Error saving anomaly to database: {e}")
```

### Updated call site in data_processor.py (line 284)

```python
# Source: src/services/processing/data_processor.py — _process_raw_data()
# Inside `for sensor_name, is_anomaly in anomaly_results.items()` loop:
self.anomaly_tracker.record_anomaly(
    sensor_name=sensor_name,
    sensor_value=sensor_value,
    detection_method=self.anomaly_manager.get_method_for_sensor(sensor_name),
    kesim_id=kesim_id,
    kafa_yuksekligi=raw_data.kafa_yuksekligi_mm,
    makine_id=raw_data.makine_id if raw_data.makine_id else None,
    serit_id=raw_data.serit_id if raw_data.serit_id else None,
    malzeme_cinsi=raw_data.malzeme_cinsi if raw_data.malzeme_cinsi else None
)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No traceability in anomaly_events | Add makine_id, serit_id, malzeme_cinsi | Phase 18 | Enables machine/blade/material-level anomaly analysis |
| Phase 17 applied to ml_predictions | Same two-file pattern for anomaly_events | Phase 18 | Consistent traceability across both event tables |

---

## Open Questions

1. **Other callers of record_anomaly**
   - What we know: The call site in data_processor.py (line 284) is the primary known caller. The new parameters are optional with defaults of `None`, so any additional callers will continue to work without modification.
   - What's unclear: Whether any other code calls `record_anomaly` directly (test code, admin scripts, etc.)
   - Recommendation: Grep for `record_anomaly` before implementing. Since parameters are optional, no other callers need updating — but the implementer should confirm this.

2. **makine_id / serit_id default value of 1**
   - What we know: `RawSensorData.makine_id` defaults to `int = 1` (same as Phase 17 finding). The falsy-to-None conversion (`if raw_data.makine_id else None`) converts `0` to NULL but stores `1` as-is.
   - What's unclear: Whether `1` always represents a real PLC-provided value or sometimes represents "not set."
   - Recommendation: Follow Phase 17 decision — store as-is. `1` is a valid PLC register value. Only `0` (falsy) is treated as sentinel for "unknown."

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None detected — no test files, no pytest.ini |
| Config file | None |
| Quick run command | `python -m py_compile src/services/database/schemas.py && python -m py_compile src/services/processing/anomaly_tracker.py && python -m py_compile src/services/processing/data_processor.py` |
| Full suite command | Same (no test suite exists) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ANDB-01 | anomaly_events table has makine_id column | smoke | `python -c "from src.services.database.schemas import SCHEMA_ANOMALY_DB; assert 'makine_id' in SCHEMA_ANOMALY_DB"` | inline |
| ANDB-02 | anomaly_events table has serit_id column | smoke | `python -c "from src.services.database.schemas import SCHEMA_ANOMALY_DB; assert 'serit_id' in SCHEMA_ANOMALY_DB"` | inline |
| ANDB-03 | anomaly_events table has malzeme_cinsi column | smoke | `python -c "from src.services.database.schemas import SCHEMA_ANOMALY_DB; assert 'malzeme_cinsi' in SCHEMA_ANOMALY_DB"` | inline |

### Sampling Rate
- **Per task commit:** `python -m py_compile src/services/database/schemas.py && python -m py_compile src/services/processing/anomaly_tracker.py && python -m py_compile src/services/processing/data_processor.py`
- **Per wave merge:** Same + column presence inline checks
- **Phase gate:** Column presence checks + compile checks green before `/gsd:verify-work`

### Wave 0 Gaps
None — existing test infrastructure (compile checks + inline assertions) covers all phase requirements. No pytest setup needed for this phase.

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `src/services/database/schemas.py` — current SCHEMA_ANOMALY_DB definition (lines 231-255), existing column pattern, comparison to SCHEMA_ML_DB (Phase 17 complete)
- Direct code inspection: `src/services/processing/anomaly_tracker.py` — `record_anomaly` signature (lines 74-81), `_save_anomaly_to_db` SQL and params (lines 120-151)
- Direct code inspection: `src/services/processing/data_processor.py` — call site at line 284, `raw_data` in scope at that point, field names confirmed
- Direct code inspection: `.planning/phases/17-ml-db-schema-update/17-RESEARCH.md` — established two-file pattern, Phase 17 exact code examples and decisions carried forward
- Direct code inspection: `.planning/phases/18-anomaly-db-schema-update/18-CONTEXT.md` — locked decisions for this phase

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — same SQLite + project files used in all prior phases
- Architecture: HIGH — three-file pattern clearly derived from Phase 17 two-file pattern; anomaly_tracker.py has a delegation between record_anomaly and _save_anomaly_to_db that Phase 17's ml_controller.py did not have
- Pitfalls: HIGH — derived from direct code inspection of the exact files being modified
- Data sources: HIGH — all three values confirmed present in RawSensorData and in scope at the call site in data_processor.py

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable codebase, no fast-moving dependencies)
