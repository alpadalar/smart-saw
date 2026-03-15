# T01: 07-mqtt-lock-free-queue 01

**Slice:** S07 — **Milestone:** M001

## Description

Replace `deque` + `asyncio.Lock` with lock-free `asyncio.Queue` for MQTT telemetry batching.

Purpose: Eliminate lock contention in 10 Hz data processing loop - `queue_telemetry()` currently blocks waiting for `_batch_lock`.
Output: Lock-free producer-consumer pattern where data processor never waits.

## Files

- `src/services/iot/mqtt_client.py`
