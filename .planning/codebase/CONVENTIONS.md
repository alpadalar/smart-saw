# Coding Conventions

**Analysis Date:** 2026-01-14

## Naming Patterns

**Files:**
- snake_case for all Python files (e.g., `data_processor.py`, `ml_controller.py`)
- `*_controller.py` for GUI controllers
- `*_service.py` for database/IO services
- `*.test.py` for tests (none present)

**Functions:**
- snake_case for all functions (e.g., `read_holding_registers`, `process_data`)
- Lifecycle methods: `start()`, `stop()`, `connect()`, `disconnect()`
- Getters: `get_*()` (e.g., `get_health()`, `get_stats()`, `get_status()`)
- Internal helpers: `_init_*()`, `_*_loop()` (e.g., `_init_modbus()`, `_health_monitor_loop()`)

**Variables:**
- snake_case for variables
- Turkish domain terms mixed with English (e.g., `serit_motor_akim_a`, `kesme_hizi`)
- Private attributes: underscore prefix (e.g., `_client`, `_connected`, `_lock`)
- Constants: UPPER_SNAKE_CASE in `src/core/constants.py`

**Types:**
- PascalCase for classes (e.g., `RawSensorData`, `AsyncModbusService`)
- Service classes: `{Domain}Service` (e.g., `SQLiteService`, `MQTTService`)
- Managers: `{Domain}Manager` (e.g., `ControlManager`, `AnomalyManager`)
- Controllers: `{Domain}Controller` (e.g., `MainController`, `MLController`)
- Base classes: `Base{Domain}` (e.g., `BaseAnomalyDetector`)

## Code Style

**Formatting:**
- Black with line-length 100 (`pyproject.toml`)
- Target versions: Python 3.10, 3.11, 3.12
- 4-space indentation (Python standard)
- Double quotes for strings

**Linting:**
- Ruff with line-length 100 (`pyproject.toml`)
- Target version: Python 3.10
- Run: `ruff check src/`

## Import Organization

**Order:**
1. Standard library imports (asyncio, logging, threading)
2. Third-party imports (PySide6, pymodbus, numpy)
3. Local imports (from ...domain.models import)

**Grouping:**
- Blank line between groups
- Alphabetical within each group

**Path Aliases:**
- Relative imports for local modules (e.g., `from ...domain.models import ProcessedData`)
- Absolute imports for external packages

## Error Handling

**Patterns:**
- Custom exception hierarchy in `src/core/exceptions.py`
- Base exception: `SmartSawException`
- Domain-specific: `ModbusConnectionError`, `DatabaseError`, `MLModelError`, etc.
- Throw exceptions, catch at service boundaries

**Error Types:**
- Throw on: Connection failures, invalid input, missing dependencies
- Log before throwing with context
- Use `exc_info=True` for stack traces

## Logging

**Framework:**
- Python `logging` module with `colorlog`
- Logger per module: `logger = logging.getLogger(__name__)`

**Patterns:**
- Structured logging with context (dict-style): `logger.info(f"Loaded model: {path}")`
- f-strings for log messages
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log at service boundaries, state transitions, errors

## Comments

**When to Comment:**
- Module docstrings required (brief description)
- Class docstrings with purpose and features (multi-line for complex classes)
- Function docstrings for public APIs (Google-style with Args, Returns, Raises)
- Inline comments for domain-specific values (register mappings, units)

**JSDoc/TSDoc:**
- Not applicable (Python project)
- Uses Google-style docstrings

**TODO Comments:**
- Format: `# TODO: description`
- No username tracking (use git blame)

## Function Design

**Size:**
- Keep functions focused (single responsibility)
- GUI controllers are exceptions (large due to Qt complexity)

**Parameters:**
- Type hints required for public functions
- Use `Optional[]` for optional parameters
- Config dict pattern for complex configuration

**Return Values:**
- Type hints on return values
- Return early for guard clauses
- Use dataclasses for complex return types

## Module Design

**Exports:**
- `__init__.py` for package exports
- Wildcard imports in `src/core/__init__.py` for exceptions and constants
- Named exports preferred elsewhere

**Barrel Files:**
- `__init__.py` re-exports from submodules
- Keep internal helpers private (not in `__init__.py`)

## Dataclass Usage

**Pattern:**
- Use `@dataclass` for data models (`src/domain/models.py`)
- Include `field()` for default factories
- Include `asdict()` for serialization
- Document units in field comments

**Example from codebase:**
```python
@dataclass
class RawSensorData:
    timestamp: datetime
    serit_motor_akim_a: float = 0.0  # Band motor current (A)
    kesme_hizi: float = 0.0          # Cutting speed (mm/min)
```

## Async Conventions

**Pattern:**
- Use `async def` for I/O operations (Modbus, database, MQTT)
- Use `await asyncio.sleep()` not `time.sleep()` in async context
- Use `asyncio.Lock()` for async thread safety
- Use `threading.RLock()` for sync thread safety

**Lifecycle:**
- `async def start()` / `async def stop()` for services
- `async def connect()` / `async def disconnect()` for connections

## GUI Conventions (PySide6)

**Pattern:**
- Controllers in `src/gui/controllers/`
- Use Qt signals/slots for cross-thread communication
- Try/except ImportError for optional PySide6 dependency
- Thread-safe updates via signal emission

---

*Convention analysis: 2026-01-14*
*Update when patterns change*
