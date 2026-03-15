# S08: Vibration Dbscan To Iqr

**Goal:** Replace DBSCAN with IQR for vibration anomaly detectors (TitresimX, TitresimY, TitresimZ).
**Demo:** Replace DBSCAN with IQR for vibration anomaly detectors (TitresimX, TitresimY, TitresimZ).

## Must-Haves


## Tasks

- [x] **T01: 08-vibration-dbscan-to-iqr 01** `est:1min`
  - Replace DBSCAN with IQR for vibration anomaly detectors (TitresimX, TitresimY, TitresimZ).

Purpose: Eliminate O(n²) DBSCAN complexity in favor of O(n) IQR method for consistent 100ms cycle time.
Output: Three vibration detectors using IQR method, aligned with config.yaml declaration.

## Files Likely Touched

- `src/anomaly/detectors.py`
