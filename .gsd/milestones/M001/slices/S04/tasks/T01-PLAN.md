# T01: 04-modbus-timeout 01

**Slice:** S04 — **Milestone:** M001

## Description

Add connection cooldown and operation timeouts to AsyncModbusService to prevent application freezing when PLC is unreachable.

Purpose: When Modbus connection is unavailable, every read/write attempt currently triggers a reconnection that blocks for 5 seconds. At 10 Hz processing rate, this causes the application to freeze. Adding cooldown prevents repeated connection attempts, and explicit timeouts ensure operations never exceed expected bounds.

Output: Modified AsyncModbusService with graceful degradation when PLC is unreachable.

## Files

- `src/services/modbus/client.py`
- `config/config.yaml`
