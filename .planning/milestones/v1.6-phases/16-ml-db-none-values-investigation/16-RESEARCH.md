# Phase 16: ML DB None Values Investigation - Research

**Researched:** 2026-02-04
**Domain:** SQLite database schema/data integrity, Python application debugging
**Confidence:** HIGH

## Summary

The investigation into None values in the `ml_predictions` table fields (`yeni_kesme_hizi`, `yeni_inme_hizi`, `katsayi`) has been completed through codebase analysis. **The root cause is clear and definitive: these fields are never populated.**

The schema in `src/services/database/schemas.py` defines all three fields in the `ml_predictions` table (lines 212-216), but the only INSERT statement writing to this table (in `src/services/control/ml_controller.py`, method `_log_ml_prediction` at line 751-775) does not include these columns. The INSERT only writes 8 fields:
- timestamp, akim_input, sapma_input, kesme_hizi_input, inme_hizi_input, serit_motor_tork, kafa_yuksekligi, ml_output

The schema has 10 data columns but only 8 are populated, leaving `yeni_kesme_hizi`, `yeni_inme_hizi`, and `katsayi` as NULL for every record.

**Primary recommendation:** Modify `_log_ml_prediction()` to include the three missing fields by passing the calculated new speeds and the `self.katsayi` value to the logging method.

## Root Cause Analysis

### Finding 1: Schema vs. Code Mismatch (HIGH confidence)

**Schema definition** (`src/services/database/schemas.py` lines 198-221):
```sql
CREATE TABLE IF NOT EXISTS ml_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,

    -- Input features
    akim_input REAL,
    sapma_input REAL,
    kesme_hizi_input REAL,
    inme_hizi_input REAL,
    serit_motor_tork REAL,
    kafa_yuksekligi REAL,

    -- Output speeds (NEVER WRITTEN)
    yeni_kesme_hizi REAL,
    yeni_inme_hizi REAL,

    -- ML outputs
    katsayi REAL,       -- NEVER WRITTEN
    ml_output REAL
);
```

**Actual INSERT** (`src/services/control/ml_controller.py` lines 751-775):
```python
def _log_ml_prediction(
    self,
    input_df,
    coefficient: float,
    serit_motor_tork: float,
    kafa_yuksekligi: float
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
            ml_output
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    # MISSING: yeni_kesme_hizi, yeni_inme_hizi, katsayi
```

### Finding 2: Data Flow Analysis (HIGH confidence)

Traced the complete ML control flow:

1. **`calculate_speeds()` (line 139-298)**: Main entry point
2. **`_predict_coefficient()` (line 300-352)**: Generates ML coefficient, calls `_log_ml_prediction()` at line 337
3. **`_calculate_new_speeds()` (line 354-421)**: Computes new speed values AFTER logging
4. **Speed accumulation** (lines 232-268): Calculates `kesme_target` and `inme_target`
5. **Return command** (lines 273-291): Returns calculated speeds

**Critical observation**: The logging happens BEFORE the new speeds are calculated (line 337 vs. lines 225-268). This is why the values cannot be logged in the current implementation without restructuring.

### Finding 3: Available Values Analysis (HIGH confidence)

| Field | Current State | Value Source | Availability |
|-------|--------------|--------------|--------------|
| `yeni_kesme_hizi` | NULL | `kesme_target` from `calculate_speeds()` | Available AFTER `_calculate_new_speeds()` |
| `yeni_inme_hizi` | NULL | `inme_target` from `calculate_speeds()` | Available AFTER `_calculate_new_speeds()` |
| `katsayi` | NULL | `self.katsayi` (class attribute, line 112) | Always available |

### Finding 4: Katsayi Value (HIGH confidence)

The `katsayi` value is:
- Loaded from config at initialization: `self.katsayi = config['ml'].get('katsayi', 1.0)` (line 112)
- Default value: 1.0 (from config.yaml line 127)
- Applied to coefficient: `coefficient *= self.katsayi` (line 334)
- Already applied to `ml_output` before logging, so `ml_output` in DB already reflects `katsayi`

## Standard Stack

This phase involves debugging/fixing an existing Python application with SQLite database.

### Core (Already in use)
| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| sqlite3 | stdlib | SQLite database operations | In use |
| Python | 3.x | Application runtime | In use |

### No Additional Libraries Needed

This is a code modification task, not a new feature requiring additional dependencies.

## Architecture Patterns

### Current ML Prediction Logging Flow
```
calculate_speeds()
    |
    +-- _predict_coefficient()
    |       |
    |       +-- model.predict()
    |       +-- coefficient *= self.katsayi
    |       +-- _log_ml_prediction()  <-- LOGGING HAPPENS HERE
    |       +-- return coefficient
    |
    +-- _calculate_new_speeds()  <-- NEW SPEEDS CALCULATED HERE
    |
    +-- Accumulate in buffers
    |
    +-- Check thresholds, return command
```

### Recommended Fix Pattern: Deferred Logging

Move ML prediction logging to AFTER speed calculation:

```
calculate_speeds()
    |
    +-- _predict_coefficient()
    |       |
    |       +-- model.predict()
    |       +-- coefficient *= self.katsayi
    |       +-- return coefficient (WITH input_df for logging)
    |
    +-- _calculate_new_speeds()
    |       |
    |       +-- return speed_changes dict
    |
    +-- _log_ml_prediction()  <-- MOVE LOGGING HERE
    |       |                    (now has access to new speeds)
    |
    +-- Accumulate in buffers
    |
    +-- Check thresholds, return command
```

### Alternative Pattern: Separate Logging Call

Keep `_predict_coefficient()` unchanged, add new logging call:

```python
# After _calculate_new_speeds() returns
self._log_ml_prediction_complete(
    input_df, coefficient, raw_data,
    speed_changes['kesme_hizi'],
    speed_changes['inme_hizi']
)
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Database migration | Custom schema updater | SQLite ALTER TABLE or app handles NULL | SQLite handles NULL columns gracefully |
| Historical data backfill | Complex migration script | Leave historical as NULL | No business value in backfilling |

**Key insight:** Historical records will remain NULL for these fields. This is acceptable because:
1. The data was never captured originally
2. Cannot be reconstructed accurately
3. New records going forward will have complete data

## Common Pitfalls

### Pitfall 1: Logging at Wrong Point in Flow
**What goes wrong:** Trying to log values before they're calculated
**Why it happens:** Original developer may have added schema fields as aspirational without implementing
**How to avoid:** Ensure `_log_ml_prediction()` is called AFTER `_calculate_new_speeds()` with all required values
**Warning signs:** NULL values in database columns that have schema definitions

### Pitfall 2: Threshold-Dependent Speed Values
**What goes wrong:** Logging speeds only when thresholds are exceeded (many NULL records)
**Why it happens:** The actual "new" speed is only calculated when threshold is exceeded
**How to avoid:** Log the CALCULATED speed change, not the WRITTEN speed target
**Clarification:**
- `speed_changes['kesme_hizi']` = always calculated (what ML thinks should happen)
- `kesme_target` = only set when threshold exceeded (what actually gets written)
- Should log `speed_changes` values, not `*_target` values

### Pitfall 3: Forgetting katsayi is Already Applied
**What goes wrong:** Double-applying katsayi or misunderstanding what to log
**Why it happens:** `coefficient *= self.katsayi` is done before logging `ml_output`
**How to avoid:** Log `self.katsayi` directly as the katsayi field
**Note:** `ml_output` already has katsayi applied, so the relationship is: `ml_output = raw_coefficient * katsayi`

### Pitfall 4: Breaking Thread Safety
**What goes wrong:** Adding mutable state access outside lock
**Why it happens:** `calculate_speeds()` uses `self._lock` (RLock)
**How to avoid:** Keep all logging within the existing `with self._lock:` block

## Code Examples

### Current Implementation (Missing Fields)
```python
# src/services/control/ml_controller.py, lines 734-778
def _log_ml_prediction(
    self,
    input_df,
    coefficient: float,
    serit_motor_tork: float,
    kafa_yuksekligi: float
):
    """Log ML prediction to database for analysis."""
    try:
        sql = """
            INSERT INTO ml_predictions (
                timestamp,
                akim_input,
                sapma_input,
                kesme_hizi_input,
                inme_hizi_input,
                serit_motor_tork,
                kafa_yuksekligi,
                ml_output
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            datetime.now().isoformat(),
            float(input_df['akim_input'].iloc[0]),
            float(input_df['sapma_input'].iloc[0]),
            float(input_df['kesme_hizi'].iloc[0]),
            float(input_df['inme_hizi'].iloc[0]),
            float(serit_motor_tork),
            float(kafa_yuksekligi),
            float(coefficient)
        )

        self.db.write_async(sql, params)
```

### Required Fix: Add Missing Fields
```python
# Updated signature and implementation
def _log_ml_prediction(
    self,
    input_df,
    coefficient: float,
    serit_motor_tork: float,
    kafa_yuksekligi: float,
    yeni_kesme_hizi: float,  # NEW
    yeni_inme_hizi: float,   # NEW
    katsayi: float           # NEW (use self.katsayi)
):
    """Log ML prediction to database for analysis."""
    try:
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
                ml_output
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            datetime.now().isoformat(),
            float(input_df['akim_input'].iloc[0]),
            float(input_df['sapma_input'].iloc[0]),
            float(input_df['kesme_hizi'].iloc[0]),
            float(input_df['inme_hizi'].iloc[0]),
            float(serit_motor_tork),
            float(kafa_yuksekligi),
            float(yeni_kesme_hizi),  # NEW
            float(yeni_inme_hizi),   # NEW
            float(katsayi),          # NEW
            float(coefficient)
        )

        self.db.write_async(sql, params)
```

### Call Site Update Required
The call to `_log_ml_prediction()` needs to be moved from inside `_predict_coefficient()` to after `_calculate_new_speeds()` in `calculate_speeds()`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Schema with unused columns | Populate all columns | This phase | Complete ML prediction logging |

**Deprecated/outdated:**
- N/A - This is a bug fix, not a technology update

## Open Questions

1. **What values to log for yeni_kesme_hizi/yeni_inme_hizi?**
   - What we know: `_calculate_new_speeds()` returns `{'kesme_hizi': X, 'inme_hizi': Y, ...}`
   - What's unclear: Should we log calculated values or only threshold-exceeded values?
   - Recommendation: Log calculated values (from `speed_changes` dict) to capture all ML decisions, not just ones that exceeded write threshold

2. **Historical data handling**
   - What we know: All existing records have NULL for these fields
   - What's unclear: Is there business need to backfill?
   - Recommendation: Leave historical as NULL, document in release notes

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis of:
  - `/media/workspace/smart-saw/src/services/database/schemas.py` - Schema definition
  - `/media/workspace/smart-saw/src/services/control/ml_controller.py` - ML controller with logging
  - `/media/workspace/smart-saw/config/config.yaml` - Configuration values

### Secondary (MEDIUM confidence)
- N/A - All findings from direct code inspection

### Tertiary (LOW confidence)
- N/A - No external sources needed

## Metadata

**Confidence breakdown:**
- Root cause analysis: HIGH - Direct code inspection proves the issue
- Fix approach: HIGH - Standard Python/SQLite patterns
- Data flow: HIGH - Traced complete call chain

**Research date:** 2026-02-04
**Valid until:** N/A - Bug fix based on static code analysis

## Implementation Summary

### Required Changes

1. **Modify `_log_ml_prediction()` signature** to accept new parameters
2. **Update INSERT statement** to include all 11 columns
3. **Move logging call** from inside `_predict_coefficient()` to after `_calculate_new_speeds()` in `calculate_speeds()`
4. **Pass required values** at the new call site

### Files to Modify
- `src/services/control/ml_controller.py` - Single file contains all changes

### Verification
- Query `ml.db`: `SELECT yeni_kesme_hizi, yeni_inme_hizi, katsayi FROM ml_predictions ORDER BY id DESC LIMIT 10;`
- After fix, new records should have non-NULL values
- Historical records will remain NULL (expected)
