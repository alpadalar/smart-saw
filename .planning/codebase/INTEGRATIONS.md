# External Integrations

**Analysis Date:** 2026-01-14

## APIs & External Services

**Payment Processing:**
- Not applicable (industrial control system)

**Email/SMS:**
- Not applicable

**External APIs:**
- None (self-contained industrial system)

## Data Storage

**Databases:**
- SQLite (Primary Local Database) - 4 separate databases
  - Connection: Local files in `data/databases/`
  - Client: aiosqlite >= 0.19.0 (`src/services/database/sqlite_service.py`)
  - Features:
    - Single-writer pattern (dedicated writer thread)
    - WAL (Write-Ahead Logging) mode for concurrent access
    - Databases: `raw.db`, `total.db`, `log.db`, `ml.db`, `anomaly.db`

- PostgreSQL (Optional Remote Database) - `src/services/database/postgres_service.py`
  - Connection: via `DATABASE_URL` or individual `POSTGRES_*` env vars
  - Client: asyncpg >= 0.29.0
  - Status: Disabled by default (enabled via `.env`)
  - Features:
    - Connection pooling (2-10 connections)
    - Async query execution
    - 30-second command timeout

**File Storage:**
- Local filesystem - `data/` directory
  - `data/databases/` - SQLite database files
  - `data/models/` - ML model file (`Bagging_dataset_v17_20250509.pkl`)
  - `data/mqtt_offline/` - Offline MQTT message storage
  - `data/databases/archive/` - Backup archives
  - `data/databases/daily/` - Daily backups

**Caching:**
- None (all data from Modbus and SQLite)

## Authentication & Identity

**Auth Provider:**
- Not applicable (local industrial system)
- No user authentication required

**OAuth Integrations:**
- None

## Monitoring & Observability

**Error Tracking:**
- None (local logging only)

**Analytics:**
- None

**Logs:**
- Local file-based logging - `logs/` directory
  - `logs/app.log` - Application events
  - `logs/modbus.log` - Modbus communication
  - `logs/database.log` - Database operations
  - `logs/control.log` - Control system events
  - `logs/iot.log` - MQTT/ThingsBoard operations
- Configuration: Rotating handlers (10MB max) in `config/config.yaml`

## CI/CD & Deployment

**Hosting:**
- Self-hosted on industrial PC
- No cloud deployment

**CI Pipeline:**
- Not configured (no test files found)

## Environment Configuration

**Development:**
- Required env vars: None strictly required (defaults in config.yaml)
- Optional env vars: `POSTGRES_*`, `TB_ACCESS_TOKEN`, `TB_MQTT_BROKER`
- Secrets location: `.env` (gitignored), `.env.example` provided

**Staging:**
- Not applicable (single deployment model)

**Production:**
- Same configuration as development
- Environment variables override YAML config
- Modbus PLC at `192.168.2.147:502`

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Industrial Control Integration

**Modbus TCP Protocol (PLC Communication)**
- Driver: pymodbus[asyncio] >= 3.5.0
- Implementation: `src/services/modbus/client.py`, `src/services/modbus/reader.py`, `src/services/modbus/writer.py`
- Configuration: `config/config.yaml` (lines 18-89)
- Target: Band saw PLC at `192.168.2.147:502`
- Features:
  - Async TCP client with rate limiting
  - 10 Hz read/write rates (configurable)
  - Retry logic: 3 retries with 1-second delay
  - Register address mapping (100+ registers)
  - Health monitoring (error rates, connection status)

**Register Groups:**
- Motor & Mechanical (2000-2039): Head height, motor current/torque, band tension
- Environment Sensors (2040-2069): Temperature, humidity, speeds
- Vibration Sensors (2100-2109): X/Y/Z acceleration and frequency
- Material Information (2200-2229): Material type, dimensions
- Band Information (2230-2249): Band ID, type, brand
- Statistics (2250-2269): Cut piece count, machine ID

## IoT/Telemetry Integration

**ThingsBoard IoT Platform**
- Integration: `src/services/iot/thingsboard.py`, `src/services/iot/mqtt_client.py`
- Protocol: MQTT (primary)
- Features:
  - Telemetry data formatting and transmission
  - Device attributes publishing
  - Batch sending (10 messages per batch, 5-second interval)
  - Offline storage with automatic sync on reconnect
  - 17+ telemetry fields configured
- Configuration: `config/config.yaml` (lines 233-272)
  - MQTT broker: `mqtt.thingsboard.cloud` (configurable via `TB_MQTT_BROKER`)
  - Authentication: Device token via `TB_ACCESS_TOKEN`
  - QoS: Level 1 (at-least-once delivery)

## Machine Learning Integration

**Scikit-learn ML Models**
- Libraries: scikit-learn >= 1.3.0, joblib >= 1.3.0, pandas >= 2.0.0, numpy >= 1.24.0
- Model: Bagging classifier - `data/models/Bagging_dataset_v17_20250509.pkl`
- Implementation: `src/ml/model_loader.py`, `src/ml/preprocessor.py`, `src/services/control/ml_controller.py`
- Features:
  - Thread-safe model loading via `joblib.load()`
  - ML control mode for adaptive speed adjustment
  - Torque guard protection (detects overload conditions)
  - Polynomial torque-to-current conversion (coefficients in config)
  - Update rate: 5 Hz (0.2-second intervals)

## External Service Summary

| Service | Type | Status | Required |
|---------|------|--------|----------|
| Modbus PLC | Industrial Protocol | Required | Yes |
| SQLite | Local Database | Required | Yes |
| ThingsBoard MQTT | IoT Platform | Optional | No |
| PostgreSQL | Remote Database | Optional | No |
| Scikit-learn Models | ML Framework | Optional | No |

---

*Integration audit: 2026-01-14*
*Update when adding/removing external services*
