# Architecture

**Analysis Date:** 2026-01-14

## Pattern Overview

**Overall:** Layered Architecture with Async/Threading Hybrid Concurrency Model

**Key Characteristics:**
- Production-grade industrial control system
- 55+ Python modules (~13,500 lines of code)
- Async-first I/O with threading for blocking operations
- Event-driven processing at 10 Hz

## Layers

**Presentation Layer (GUI):**
- Purpose: User interface for machine operators
- Contains: PySide6 Qt6 widgets, controllers, signal/slot handlers
- Location: `src/gui/`
- Depends on: Domain layer for data models, service layer for control
- Used by: Operators on industrial PC

**Business Logic Layer:**
- Purpose: Control orchestration and data processing
- Contains: ControlManager, DataProcessingPipeline, anomaly detection
- Location: `src/services/control/`, `src/services/processing/`, `src/anomaly/`
- Depends on: Service layer for I/O, domain layer for models
- Used by: Presentation layer, background tasks

**Service Layer:**
- Purpose: External communication and data persistence
- Contains: ModbusService, SQLiteService, MQTTService, PostgresService
- Location: `src/services/modbus/`, `src/services/database/`, `src/services/iot/`
- Depends on: Infrastructure layer, domain models
- Used by: Business logic layer

**Domain Layer:**
- Purpose: Business domain models and enums
- Contains: RawSensorData, ProcessedData, ControlCommand, TesereDurumu, ControlMode
- Location: `src/domain/`
- Depends on: Nothing (pure data structures)
- Used by: All other layers

**Infrastructure Layer:**
- Purpose: Foundation utilities (config, logging, exceptions)
- Contains: ConfigManager, logging setup, custom exceptions, constants
- Location: `src/core/`
- Depends on: External libraries only
- Used by: All other layers

## Data Flow

**Main Processing Loop (10 Hz target) - DataProcessingPipeline:**

1. **Read Phase** (ModbusReader)
   - Pull 30+ sensor registers from PLC via Modbus TCP
   - Scale to engineering units (e.g., register / 10)
   - Create `RawSensorData` dataclass

2. **Process Phase**
   - Detect cutting state (testere_durumu == 3)
   - Track cutting sessions (`CuttingTracker`)
   - Run anomaly detection (`AnomalyManager` → 9 detectors)
   - Create `ProcessedData`

3. **Control Phase** (ControlManager)
   - Check initial delay (if cutting + delay enabled)
   - Delegate to active controller:
     - Manual: Return speeds from GUI input
     - ML: Run Bagging model, apply Torque Guard, return adjusted speeds

4. **Write Phase** (ModbusWriter)
   - Send `ControlCommand` to PLC (registers 2066, 2041)

5. **Storage Phase** (SQLiteService queue pattern)
   - raw.db: Store `RawSensorData`
   - total.db: Store `ProcessedData`
   - log.db: Store system logs
   - ml.db: Store ML predictions

6. **Telemetry Phase** (MQTTService batching)
   - Queue to offline storage if disconnected
   - Batch send to ThingsBoard on interval/size threshold

**State Management:**
- File-based: All state lives in SQLite databases
- No persistent in-memory state between restarts
- Each processing cycle is independent

## Key Abstractions

**Service:**
- Purpose: Encapsulate I/O and business logic for a domain
- Examples: `AsyncModbusService`, `SQLiteService`, `MQTTService`, `ControlManager`
- Pattern: Singleton-like (imported as modules, shared instances)
- Location: `src/services/*/`

**Controller:**
- Purpose: Control mode implementation (Manual or ML)
- Examples: `ManualController`, `MLController`
- Pattern: Strategy pattern via ControlManager
- Location: `src/services/control/`

**Detector:**
- Purpose: Anomaly detection for specific sensor
- Examples: `SeritSapmasiDetector`, `SeritMotorAkimDetector`, `TitresimXDetector`
- Pattern: Abstract base class with 9 concrete implementations
- Location: `src/anomaly/detectors.py`

**Tracker:**
- Purpose: Session and state tracking
- Examples: `CuttingTracker`, `AnomalyTracker`
- Pattern: Singleton for cutting, instance for anomaly
- Location: `src/services/processing/`

## Entry Points

**CLI Entry:**
- Location: `run.py`
- Triggers: `python run.py` or `smart-saw` command
- Responsibilities: Set PYTHONPATH, import main, run asyncio

**Async Main:**
- Location: `src/main.py`
- Triggers: Called by run.py
- Responsibilities: Setup signal handlers (SIGINT, SIGTERM), create ApplicationLifecycle, start/stop

**Application Orchestrator:**
- Location: `src/core/lifecycle.py` (ApplicationLifecycle)
- Triggers: Called by main.py
- Responsibilities: Initialize all services in order, manage startup/shutdown sequence

**GUI Entry:**
- Location: `src/gui/app.py` (GUIApplication.run())
- Triggers: Started by ApplicationLifecycle in separate thread
- Responsibilities: Qt event loop, window management

## Error Handling

**Strategy:** Throw exceptions, catch at boundaries, graceful degradation

**Patterns:**
- Custom exception hierarchy in `src/core/exceptions.py`
  - `SmartSawException` (base)
  - `ModbusConnectionError`, `ModbusReadError`, `ModbusWriteError`
  - `DatabaseError`, `ControllerError`, `ConfigurationError`
  - `MLModelError`, `ValidationError`
- Services throw specific exceptions
- ApplicationLifecycle catches and logs at top level
- Modbus errors allow retry before escalation
- Database queue pattern prevents blocking on write failures

## Cross-Cutting Concerns

**Logging:**
- Framework: Python `logging` module with `colorlog`
- Configuration: `config/config.yaml` (lines 312-411)
- Output: Console (colored) + rotating file handlers (10MB max)
- Files: `app.log`, `modbus.log`, `database.log`, `control.log`, `iot.log`

**Validation:**
- Input validation at Modbus read (register scaling)
- Speed limits enforced in ControlManager
- Configuration validated at startup (required sections)

**Thread Safety:**
- SQLite: Single-writer pattern with queue
- ControlManager: `threading.RLock` for mode switching
- Anomaly detectors: Thread-safe with locks
- GUI: Qt signals/slots for cross-thread communication

**Health Monitoring:**
- Background task in ApplicationLifecycle (30s interval)
- Checks: Modbus error rate, database queue size, memory/disk usage
- Thresholds configured in `config/config.yaml`

## Concurrency Model

| Type | Component | Purpose |
|------|-----------|---------|
| AsyncIO | Modbus, PostgreSQL, MQTT | Non-blocking I/O (main event loop) |
| Threading | SQLite writes, GUI, health monitor | Blocking I/O and UI handling |
| Multiprocessing | Daily backups | Heavy computation isolation |

---

*Architecture analysis: 2026-01-14*
*Update when major patterns change*
