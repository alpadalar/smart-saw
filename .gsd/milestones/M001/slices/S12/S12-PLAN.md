# S12: Ml Prediction Parity

**Goal:** Fix ML prediction parity by aligning speed calculation logic with old codebase.
**Demo:** Fix ML prediction parity by aligning speed calculation logic with old codebase.

## Must-Haves


## Tasks

- [x] **T01: 12-ml-prediction-parity 01** `est:1min`
  - Fix ML prediction parity by aligning speed calculation logic with old codebase.

Purpose: The new code uses raw current speed values for percentage calculations, while the old code uses averaged speeds from buffers. This causes different speed adjustments even with identical ML predictions.

Output: Modified ml_controller.py and preprocessor.py that match old code behavior exactly.

## Files Likely Touched

- `src/ml/preprocessor.py`
- `src/services/control/ml_controller.py`
