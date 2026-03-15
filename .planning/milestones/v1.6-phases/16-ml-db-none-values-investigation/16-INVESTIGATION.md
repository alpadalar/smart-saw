# Phase 16: ML DB None Values Investigation Report

**Investigation Date:** 2026-02-04
**Status:** RESOLVED

## Root Cause Summary

The `ml_predictions` table had three columns (`yeni_kesme_hizi`, `yeni_inme_hizi`, `katsayi`) that were defined in the schema but never populated by the INSERT statement. This was a schema-code mismatch where:

1. **Schema defined 11 data columns** (in `src/services/database/schemas.py`)
2. **INSERT statement only wrote 8 columns** (in `src/services/control/ml_controller.py`)
3. **Result:** Three columns always contained NULL values

## Technical Details

### Schema Definition (Complete)

```sql
CREATE TABLE IF NOT EXISTS ml_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    akim_input REAL,
    sapma_input REAL,
    kesme_hizi_input REAL,
    inme_hizi_input REAL,
    serit_motor_tork REAL,
    kafa_yuksekligi REAL,
    yeni_kesme_hizi REAL,   -- WAS NOT POPULATED
    yeni_inme_hizi REAL,    -- WAS NOT POPULATED
    katsayi REAL,           -- WAS NOT POPULATED
    ml_output REAL
);
```

### Original INSERT Statement (Incomplete)

```python
# Only 8 columns were populated
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
```

### Timing Issue

The logging method `_log_ml_prediction()` was called inside `_predict_coefficient()` BEFORE `_calculate_new_speeds()` computed the new speed values. Even if the INSERT included all columns, the values would not have been available at that point in the code flow.

**Original flow:**
```
_predict_coefficient()
    +-- model.predict()
    +-- _log_ml_prediction()  <-- LOGGING HERE (too early)
    +-- return coefficient

_calculate_new_speeds()  <-- SPEEDS CALCULATED HERE (after logging)
```

## Fix Applied

### 1. Updated `_log_ml_prediction()` Signature

Added three new parameters:
- `yeni_kesme_hizi: float` - Calculated new cutting speed
- `yeni_inme_hizi: float` - Calculated new descent speed
- `katsayi: float` - Global coefficient multiplier from config

### 2. Updated INSERT Statement

Changed from 8 columns to 11 columns:
```python
INSERT INTO ml_predictions (
    timestamp,
    akim_input,
    sapma_input,
    kesme_hizi_input,
    inme_hizi_input,
    serit_motor_tork,
    kafa_yuksekligi,
    yeni_kesme_hizi,   -- NEW
    yeni_inme_hizi,    -- NEW
    katsayi,           -- NEW
    ml_output
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

### 3. Moved Logging Call

Relocated `_log_ml_prediction()` call from `_predict_coefficient()` to `calculate_speeds()`, after `_calculate_new_speeds()` returns.

**Fixed flow:**
```
_predict_coefficient()
    +-- model.predict()
    +-- return (coefficient, input_df)

_calculate_new_speeds()
    +-- return speed_changes

_log_ml_prediction()  <-- LOGGING NOW HERE (after speeds calculated)
```

### 4. Modified Return Type

Changed `_predict_coefficient()` to return a tuple `(coefficient, input_df)` instead of just `coefficient`, so the input DataFrame is available at the logging call site.

## Verification Method

### For Historical Records

Historical records will retain NULL values for the three fields. This is expected and acceptable because:
- The data was never captured originally
- Cannot be reconstructed accurately
- No business value in backfilling estimated values

### For New Records

After the fix, run this query:
```sql
SELECT
    id,
    timestamp,
    yeni_kesme_hizi,
    yeni_inme_hizi,
    katsayi
FROM ml_predictions
ORDER BY id DESC
LIMIT 10;
```

**Expected result:**
- All three columns populated with numeric values for new records
- `yeni_kesme_hizi`: Calculated cutting speed (mm/min)
- `yeni_inme_hizi`: Calculated descent speed (mm/min)
- `katsayi`: Should be 1.0 (default config value)

## Data Interpretation

| Column | Meaning | Typical Range |
|--------|---------|---------------|
| `yeni_kesme_hizi` | Calculated new cutting speed | 10-80 mm/min |
| `yeni_inme_hizi` | Calculated new descent speed | 10-80 mm/min |
| `katsayi` | Global coefficient multiplier | 1.0 (default) |
| `ml_output` | ML coefficient with katsayi applied | -1.0 to 1.0 |

**Important distinctions:**
- `yeni_*_hizi` are CALCULATED values, not necessarily WRITTEN values
- Values are logged even if threshold was not exceeded (captures all ML decisions)
- `ml_output` already has `katsayi` applied: `ml_output = raw_coefficient * katsayi`

## Files Modified

| File | Change |
|------|--------|
| `src/services/control/ml_controller.py` | Updated `_log_ml_prediction()`, moved logging call, modified `_predict_coefficient()` return type |

## Commit

- Hash: `7d3bd29`
- Message: `fix(16-01): populate yeni_kesme_hizi, yeni_inme_hizi, katsayi in ML predictions`
