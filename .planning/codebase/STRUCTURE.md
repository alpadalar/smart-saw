# Codebase Structure

**Analysis Date:** 2026-01-14

## Directory Layout

```
smart-saw/
├── run.py                          # CLI entry point (launcher)
├── pyproject.toml                  # Project metadata, dependencies
├── requirements.txt                # Pip dependencies
├── environment.yml                 # Conda environment (optional)
├── config/
│   └── config.yaml                 # Main config (450+ lines)
├── data/
│   ├── databases/                  # SQLite files (raw.db, total.db, log.db, ml.db)
│   │   ├── archive/               # Backup archives
│   │   └── daily/                 # Daily backups
│   ├── models/                     # ML model (Bagging_dataset_v17.pkl)
│   └── mqtt_offline/               # Offline MQTT storage
├── logs/                           # Log files
│   ├── app.log
│   ├── modbus.log
│   ├── database.log
│   ├── control.log
│   └── iot.log
└── src/                            # Source code (55+ files, ~13,500 lines)
    ├── main.py                    # Async entry point
    ├── core/                      # Foundation layer
    ├── domain/                    # Data models
    ├── services/                  # Service layer
    ├── anomaly/                   # Anomaly detection
    ├── ml/                        # Machine learning
    ├── gui/                       # Presentation layer
    ├── infrastructure/            # Utilities
    └── tasks/                     # Background tasks
```

## Directory Purposes

**config/**
- Purpose: Application configuration files
- Contains: YAML config with all system settings
- Key files: `config.yaml` - Modbus registers, control params, logging, ML settings
- Subdirectories: None

**data/**
- Purpose: Runtime data storage
- Contains: SQLite databases, ML models, offline MQTT messages
- Key files: `raw.db`, `total.db`, `log.db`, `ml.db`, `Bagging_dataset_v17_20250509.pkl`
- Subdirectories: `databases/`, `models/`, `mqtt_offline/`

**logs/**
- Purpose: Application log files
- Contains: Rotating log files (10MB max each)
- Key files: `app.log`, `modbus.log`, `database.log`, `control.log`, `iot.log`
- Subdirectories: None

**src/core/**
- Purpose: Foundation utilities
- Contains: Config loading, logging setup, exceptions, constants, lifecycle
- Key files:
  - `lifecycle.py` - ApplicationLifecycle (main orchestrator)
  - `config.py` - ConfigManager (YAML + env vars)
  - `logger.py` - Logging setup
  - `exceptions.py` - Custom exception hierarchy
  - `constants.py` - Application constants

**src/domain/**
- Purpose: Business domain models
- Contains: Dataclasses, enums, validators
- Key files:
  - `models.py` - RawSensorData, ProcessedData, ControlCommand, CuttingSession
  - `enums.py` - TesereDurumu (saw states), ControlMode (manual/ml)
  - `validators.py` - Data validation functions

**src/services/modbus/**
- Purpose: Modbus TCP communication with PLC
- Contains: Async client, register reader, register writer
- Key files:
  - `client.py` - AsyncModbusService (rate-limited TCP client)
  - `reader.py` - ModbusReader (reads 30+ registers)
  - `writer.py` - ModbusWriter (sends speed commands)

**src/services/database/**
- Purpose: Data persistence
- Contains: SQLite service, PostgreSQL service, schemas, backup
- Key files:
  - `sqlite_service.py` - SQLiteService (single-writer queue pattern)
  - `postgres_service.py` - PostgresService (optional, async)
  - `schemas.py` - SQL schema definitions
  - `backup_service.py` - Daily backups

**src/services/control/**
- Purpose: Machine control logic
- Contains: Control manager, manual/ML controllers
- Key files:
  - `manager.py` - ControlManager (orchestrates mode switching)
  - `manual.py` - ManualController (GUI-driven speeds)
  - `ml_controller.py` - MLController (Bagging model + Torque Guard)
  - `machine_control.py` - Machine-specific control logic

**src/services/processing/**
- Purpose: Data processing pipeline
- Contains: Main processing loop, trackers
- Key files:
  - `data_processor.py` - DataProcessingPipeline (10 Hz main loop)
  - `cutting_tracker.py` - CuttingTracker (session tracking)
  - `anomaly_tracker.py` - AnomalyTracker (persistence)
  - `anomaly_detector.py` - Legacy anomaly detection

**src/services/iot/**
- Purpose: IoT telemetry
- Contains: MQTT client, ThingsBoard integration
- Key files:
  - `mqtt_client.py` - MQTTService (async, batch sending)
  - `thingsboard.py` - ThingsBoardFormatter (telemetry formatting)

**src/anomaly/**
- Purpose: Anomaly detection framework
- Contains: Base class, manager, concrete detectors
- Key files:
  - `base.py` - BaseAnomalyDetector (abstract)
  - `manager.py` - AnomalyManager (9 detectors)
  - `detectors.py` - Concrete detectors (IQR, Z-score, DBSCAN)

**src/ml/**
- Purpose: Machine learning
- Contains: Model loading, preprocessing
- Key files:
  - `model_loader.py` - MLModelLoader (thread-safe)
  - `preprocessor.py` - Feature preprocessing

**src/gui/**
- Purpose: Desktop user interface
- Contains: PySide6 application, controllers, widgets
- Key files:
  - `app.py` - GUIApplication (Qt lifecycle wrapper)
  - `numpad.py` - Touch-friendly numpad widget
- Subdirectories:
  - `controllers/` - Page controllers (main, control_panel, positioning, sensor, monitoring)
  - `ui_files/` - UI definitions
  - `images/` - GUI assets

**src/tasks/**
- Purpose: Background tasks
- Contains: Backup task
- Key files: `backup.py` - Multiprocessing daily backups

## Key File Locations

**Entry Points:**
- `run.py` - CLI launcher
- `src/main.py` - Async main with signal handling
- `src/core/lifecycle.py` - ApplicationLifecycle orchestrator

**Configuration:**
- `config/config.yaml` - Main configuration (450+ lines)
- `pyproject.toml` - Project metadata and dependencies
- `.env` / `.env.example` - Environment variables

**Core Logic:**
- `src/services/processing/data_processor.py` - Main 10 Hz processing loop
- `src/services/control/manager.py` - Control mode orchestration
- `src/services/modbus/client.py` - PLC communication

**Testing:**
- No test files found (tests/ directory not present)

**Documentation:**
- `README.md` - User documentation
- `CLAUDE.md` - AI assistant context (if present)

## Naming Conventions

**Files:**
- snake_case for all Python files (e.g., `data_processor.py`, `ml_controller.py`)
- Single word or compound names (e.g., `lifecycle.py`, `backup_service.py`)
- `*_controller.py` for GUI controllers
- `*_service.py` for service classes

**Directories:**
- lowercase for all directories (e.g., `services`, `modbus`, `control`)
- Plural for collections (e.g., `services`, `tasks`)
- Domain-based grouping (e.g., `modbus`, `database`, `iot`)

**Special Patterns:**
- `__init__.py` for package initialization
- `*_test.py` for tests (none present)
- Config files: `config.yaml`, `environment.yml`

## Where to Add New Code

**New Service:**
- Primary code: `src/services/{domain}/`
- If related to existing domain, add to that directory
- Create new directory if truly new domain

**New Anomaly Detector:**
- Implementation: `src/anomaly/detectors.py` (add class)
- Registration: `src/anomaly/manager.py` (add to detectors dict)

**New Control Mode:**
- Implementation: `src/services/control/{mode}.py`
- Registration: `src/services/control/manager.py`

**New GUI Page:**
- Controller: `src/gui/controllers/{page}_controller.py`
- Registration: `src/gui/controllers/main_controller.py`

**Utilities:**
- Shared helpers: `src/infrastructure/utils/`
- Type definitions: `src/domain/`
- Constants: `src/core/constants.py`

**Background Tasks:**
- Implementation: `src/tasks/{task}.py`
- Scheduling: `src/core/lifecycle.py`

## Special Directories

**data/**
- Purpose: Runtime data (databases, models, offline storage)
- Source: Created at runtime
- Committed: No (in .gitignore except models)

**logs/**
- Purpose: Application logs
- Source: Generated by logging system
- Committed: No (in .gitignore)

**__pycache__/**
- Purpose: Python bytecode cache
- Source: Python interpreter
- Committed: No (in .gitignore)

---

*Structure analysis: 2026-01-14*
*Update when directory structure changes*
