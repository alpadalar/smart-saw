# Technology Stack

**Analysis Date:** 2026-01-14

## Languages

**Primary:**
- Python 3.10+ - All application code (`pyproject.toml`, `environment.yml`)
- Supports Python 3.10, 3.11, 3.12 per project metadata

**Secondary:**
- YAML - Configuration files (`config/config.yaml`)

## Runtime

**Environment:**
- Python 3.10+ required
- Async-first architecture using `asyncio`
- Can run headless or with GUI (PySide6)

**Package Manager:**
- pip - Primary package manager (`requirements.txt`)
- Conda optional - `environment.yml`
- No lockfile (pip-based, uses version constraints only)

## Frameworks

**Core:**
- asyncio - Built-in async framework for I/O operations
- PySide6 >= 6.6.0 - Qt6-based desktop GUI (`src/gui/app.py`)

**Testing:**
- pytest >= 7.4.0 - Test framework (configured but no tests implemented)
- pytest-asyncio >= 0.21.0 - Async test support
- pytest-cov >= 4.1.0 - Coverage reporting

**Build/Dev:**
- Black >= 23.0.0 - Code formatting (line-length: 100)
- Ruff >= 0.1.0 - Linting

## Key Dependencies

**Critical:**
- pymodbus[asyncio] >= 3.5.0 - Modbus TCP client for PLC communication (`src/services/modbus/client.py`)
- scikit-learn >= 1.3.0 - ML algorithms for speed optimization (`src/ml/preprocessor.py`)
- joblib >= 1.3.0 - ML model serialization (`src/ml/model_loader.py`)
- pandas >= 2.0.0 - Data processing
- numpy >= 1.24.0, < 2.0 - Numerical computing

**Infrastructure:**
- aiosqlite >= 0.19.0 - Async SQLite driver (`src/services/database/sqlite_service.py`)
- asyncpg >= 0.29.0 - Async PostgreSQL driver (`src/services/database/postgres_service.py`)
- aiomqtt >= 1.2.0 - Async MQTT client for ThingsBoard (`src/services/iot/mqtt_client.py`)
- aiofiles >= 23.0.0 - Async file I/O

**Configuration:**
- pyyaml >= 6.0 - YAML config parsing (`config/config.yaml`)
- python-dotenv >= 1.0.0 - Environment variable management (`src/core/config.py`)
- colorlog >= 6.7.0 - Colored console logging

## Configuration

**Environment:**
- `.env` files for sensitive configuration
- Key vars: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- ThingsBoard: `TB_ACCESS_TOKEN`, `TB_MQTT_BROKER`
- Application: `DEBUG`, `LOG_LEVEL`

**Build:**
- `pyproject.toml` - Project metadata, dependencies, tool configuration
- `config/config.yaml` - 450+ lines covering:
  - Application metadata (v2.0.0)
  - GUI settings (1200x800 window, dark theme)
  - Modbus TCP configuration (registers, rates, timeouts)
  - Control system settings (manual/ML modes, speed limits)
  - ML model settings (Bagging model, torque guard, coefficients)
  - Database configuration (SQLite WAL mode, PostgreSQL pooling)
  - MQTT/ThingsBoard telemetry
  - Anomaly detection (Z-score, IQR, DBSCAN methods)
  - Logging configuration (rotating file handlers)

## Platform Requirements

**Development:**
- Linux/Windows/macOS (any platform with Python 3.10+)
- No Docker required for basic development
- Optional: PostgreSQL for remote database
- PySide6 requires Qt6 runtime

**Production:**
- Industrial PC with network access to PLC (192.168.2.147:502)
- Linux recommended for production deployment
- Runs as standalone Python application
- Entry points: `smart-saw` (main), `smart-saw-backup` (backup utility)

---

*Stack analysis: 2026-01-14*
*Update after major dependency changes*
