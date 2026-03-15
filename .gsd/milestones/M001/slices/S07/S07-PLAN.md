# S07: Mqtt Lock Free Queue

**Goal:** Replace `deque` + `asyncio.
**Demo:** Replace `deque` + `asyncio.

## Must-Haves


## Tasks

- [x] **T01: 07-mqtt-lock-free-queue 01** `est:2min`
  - Replace `deque` + `asyncio.Lock` with lock-free `asyncio.Queue` for MQTT telemetry batching.

Purpose: Eliminate lock contention in 10 Hz data processing loop - `queue_telemetry()` currently blocks waiting for `_batch_lock`.
Output: Lock-free producer-consumer pattern where data processor never waits.

## Files Likely Touched

- `src/services/iot/mqtt_client.py`
