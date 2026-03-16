# S16: ML DB None Values Investigation

**Goal:** Fix ML prediction logging to populate yeni_kesme_hizi, yeni_inme_hizi, katsayi fields that were stored as NULL due to schema-code mismatch.
**Demo:** ML predictions table has non-NULL values for all 11 columns after a cutting operation.

## Must-Haves


## Tasks


## Files Likely Touched

- `src/services/control/ml_controller.py`
