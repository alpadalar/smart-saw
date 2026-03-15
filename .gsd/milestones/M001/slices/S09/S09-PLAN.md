# S09: Anomaly Manager Lock Consolidation

**Goal:** Consolidate 9 separate lock acquisitions into single lock acquisition in AnomalyManager.
**Demo:** Consolidate 9 separate lock acquisitions into single lock acquisition in AnomalyManager.

## Must-Haves


## Tasks

- [x] **T01: 09-anomaly-manager-lock-consolidation 01** `est:2min`
  - Consolidate 9 separate lock acquisitions into single lock acquisition in AnomalyManager.process_data().

Purpose: Reduce lock contention overhead in 10 Hz processing loop - currently acquiring manager lock 9 times per cycle for anomaly_states updates.
Output: Single lock acquisition per process_data() call, ~8 fewer lock operations per cycle.

## Files Likely Touched

- `src/anomaly/manager.py`
