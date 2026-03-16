# S04: Modbus Timeout

**Goal:** Add connection cooldown and operation timeouts to AsyncModbusService to prevent application freezing when PLC is unreachable.
**Demo:** Add connection cooldown and operation timeouts to AsyncModbusService to prevent application freezing when PLC is unreachable.

## Must-Haves


## Tasks

- [x] **T01: 04-modbus-timeout 01** `est:2min`
  - Add connection cooldown and operation timeouts to AsyncModbusService to prevent application freezing when PLC is unreachable.

Purpose: When Modbus connection is unavailable, every read/write attempt currently triggers a reconnection that blocks for 5 seconds. At 10 Hz processing rate, this causes the application to freeze. Adding cooldown prevents repeated connection attempts, and explicit timeouts ensure operations never exceed expected bounds.

Output: Modified AsyncModbusService with graceful degradation when PLC is unreachable.

## Files Likely Touched

- `src/services/modbus/client.py`
- `config/config.yaml`
