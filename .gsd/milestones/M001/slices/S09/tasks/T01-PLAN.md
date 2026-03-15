# T01: 09-anomaly-manager-lock-consolidation 01

**Slice:** S09 — **Milestone:** M001

## Description

Consolidate 9 separate lock acquisitions into single lock acquisition in AnomalyManager.process_data().

Purpose: Reduce lock contention overhead in 10 Hz processing loop - currently acquiring manager lock 9 times per cycle for anomaly_states updates.
Output: Single lock acquisition per process_data() call, ~8 fewer lock operations per cycle.

## Files

- `src/anomaly/manager.py`
