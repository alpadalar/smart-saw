# Codebase Concerns

**Analysis Date:** 2026-01-14

## Tech Debt

**Bare except clauses masking errors:**
- Issue: Multiple locations use `except:` without specifying exception types
- Files:
  - `src/services/database/sqlite_service.py` (lines 84-85, 220): Catches everything in queue operations
  - `src/anomaly/base.py` (line 290): Bare except in fallback detection
- Why: Quick error suppression during development
- Impact: Real errors are silently ignored, making debugging difficult
- Fix approach: Change to specific exceptions (`except queue.Full:`, `except ValueError:`)

**GUI controllers are monolithic:**
- Issue: Single controller files exceeding 2000 lines
- Files:
  - `src/gui/controllers/control_panel_controller.py` (2,260 lines)
  - `src/gui/controllers/sensor_controller.py` (1,448 lines)
  - `src/gui/controllers/monitoring_controller.py` (850 lines)
- Why: GUI complexity grew without refactoring
- Impact: Hard to maintain, test, or modify individual features
- Fix approach: Extract reusable widgets, separate graph logic, create smaller focused controllers

**Wildcard imports pollute namespace:**
- Issue: `from .exceptions import *` style imports
- File: `src/core/__init__.py`
- Why: Convenience during initial development
- Impact: Unclear what symbols are available, IDE support degraded
- Fix approach: Use explicit imports: `from .exceptions import SmartSawException, ModbusError`

## Known Bugs

**Potential race condition in sensor buffer:**
- Symptoms: Possible IndexError when rebuilding graph from empty buffer
- Trigger: Fast UI updates during cutting start/stop transitions
- File: `src/gui/controllers/sensor_controller.py` (lines 1359-1374)
- Workaround: Error is caught but graph may not update
- Root cause: Buffer copy made without proper empty check before index access
- Fix: Add bounds checking before accessing `buffer_copy[0]`

## Security Considerations

**Sensitive data in .env file:**
- Risk: ThingsBoard access token and Modbus IP exposed in `.env`
- File: `.env` (lines 9-14 contain real credentials)
- Current mitigation: `.env` in `.gitignore` (but may be in git history)
- Recommendations:
  - Audit git history for committed credentials
  - Rotate ThingsBoard token
  - Use secrets manager for production

**No input validation on config values:**
- Risk: Invalid config values cause runtime errors
- File: `src/core/config.py` (lines 98-118)
- Current mitigation: Only checks required sections exist
- Recommendations: Add validation for IP addresses, port numbers, threshold values

## Performance Bottlenecks

**Anomaly summary called every tick:**
- Problem: `anomaly_tracker.get_anomaly_summary()` called at 5 Hz without caching
- File: `src/gui/controllers/sensor_controller.py` (lines 1167-1169)
- Measurement: Not profiled, but potential DB query per call
- Cause: No result caching in tracker
- Improvement path: Add TTL-based cache (1-2 second expiry)

## Fragile Areas

**Database queue overflow:**
- File: `src/services/database/sqlite_service.py`
- Why fragile: Queue max size is 10,000 - if processing speed < write speed, writes silently drop
- Common failures: Data loss during high-frequency periods without warning to user
- Safe modification: Queue size change requires understanding of throughput rates
- Test coverage: None - queue overflow behavior not tested

**Anomaly detection fallback chain:**
- File: `src/anomaly/base.py` (lines 278-291)
- Why fragile: DBSCAN → Z-score fallback, both with bare except
- Common failures: Both methods can fail silently, returning `False`
- Safe modification: Add specific exception handling, logging on fallback
- Test coverage: None

**SQLite thread safety bypass:**
- File: `src/services/database/sqlite_service.py` (line 119)
- Why fragile: Uses `check_same_thread=False` with thread-local storage
- Common failures: If non-read-only query executed on read connection, silent failure
- Safe modification: Ensure all reads use thread-local connection
- Test coverage: None

## Scaling Limits

**SQLite write queue:**
- Current capacity: 10,000 items max queue
- Limit: If write rate exceeds processing rate, data drops
- Symptoms at limit: Warning logged, writes discarded
- Scaling path: Increase queue size, add backpressure mechanism

**Single PLC connection:**
- Current capacity: 1 Modbus TCP connection
- Limit: Cannot scale to multiple machines
- Symptoms at limit: Architecture change required
- Scaling path: Connection pool, machine ID routing

## Dependencies at Risk

**numpy version constraint:**
- Risk: `numpy<2.0,>=1.24.0` - numpy 2.0 excluded without documented reason
- Impact: May need testing when numpy 2.0 becomes unavoidable
- Migration plan: Test with numpy 2.0, update constraint or document incompatibility

**PySide6 no upper bound:**
- Risk: `PySide6>=6.4.0` - PySide7 could break compatibility
- Impact: Future Qt version may have breaking changes
- Migration plan: Add upper bound `PySide6>=6.4.0,<7.0.0`

## Missing Critical Features

**No automated tests:**
- Problem: 0 test files for 55+ Python modules
- Current workaround: Manual testing
- Blocks: CI/CD, safe refactoring, regression detection
- Implementation complexity: Medium - add pytest structure and critical path tests

**No config validation:**
- Problem: Invalid config values only caught at runtime
- Current workaround: User must ensure config is valid
- Blocks: Graceful startup failures, clear error messages
- Implementation complexity: Low - add validation in ConfigManager

## Test Coverage Gaps

**Modbus communication (Critical):**
- What's not tested: Connection, read/write, error handling
- Risk: PLC communication failures undetected until production
- Priority: High
- Difficulty to test: Medium - needs mock Modbus server or simulator

**ML inference (Critical):**
- What's not tested: Model loading, preprocessing, coefficient calculation
- Risk: Wrong speed calculations affect machine operation
- Priority: High
- Difficulty to test: Low - can test with sample data

**Anomaly detection (High):**
- What's not tested: All 9 detectors, fallback logic
- Risk: Safety-critical feature may miss anomalies
- Priority: High
- Difficulty to test: Low - pure functions with sample data

**Control mode switching (High):**
- What's not tested: Manual/ML transitions, speed limits
- Risk: Mode switch could cause unexpected behavior
- Priority: High
- Difficulty to test: Medium - needs state management testing

**Database operations (Medium):**
- What's not tested: Queue pattern, concurrent writes, recovery
- Risk: Data integrity issues
- Priority: Medium
- Difficulty to test: Medium - needs async test fixtures

---

*Concerns audit: 2026-01-14*
*Update as issues are fixed or new ones discovered*
