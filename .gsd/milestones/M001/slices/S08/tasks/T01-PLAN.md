# T01: 08-vibration-dbscan-to-iqr 01

**Slice:** S08 — **Milestone:** M001

## Description

Replace DBSCAN with IQR for vibration anomaly detectors (TitresimX, TitresimY, TitresimZ).

Purpose: Eliminate O(n²) DBSCAN complexity in favor of O(n) IQR method for consistent 100ms cycle time.
Output: Three vibration detectors using IQR method, aligned with config.yaml declaration.

## Files

- `src/anomaly/detectors.py`
