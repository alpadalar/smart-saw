# T01: 05-ml-speed-restoration 01

**Slice:** S05 — **Milestone:** M001

## Description

Implement save/restore of cutting speeds around ML cuts.

Purpose: When ML mode adjusts speeds during cutting, the original operator-set speeds are lost. This feature saves speeds before ML starts and restores them after cutting completes, so the next cut starts from operator-preferred values instead of ML-modified values.

Output: MLController that automatically saves/restores kesme and inme speeds around each cutting session.

## Files

- `src/services/control/ml_controller.py`
- `config/config.yaml`
