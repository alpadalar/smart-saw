# Testing Patterns

**Analysis Date:** 2026-01-14

## Test Framework

**Runner:**
- pytest >= 7.4.0 (configured in `pyproject.toml`)
- Config: None (no pytest.ini or pyproject.toml pytest section)

**Assertion Library:**
- pytest built-in expect (configured but not used)

**Run Commands:**
```bash
pytest                              # Run all tests (none exist)
pytest --asyncio-mode=auto          # Async test support
pytest --cov=src                    # Coverage report
```

## Test File Organization

**Location:**
- No test files found in codebase
- Expected pattern: `tests/` directory or `*.test.py` co-located

**Naming:**
- Expected: `test_*.py` or `*_test.py`
- None present

**Structure:**
```
# Expected but not implemented:
tests/
├── conftest.py
├── test_modbus.py
├── test_database.py
├── test_control.py
└── test_anomaly.py
```

## Test Structure

**Suite Organization:**
- Not implemented

**Expected Pattern:**
```python
import pytest
from src.services.modbus.client import AsyncModbusService

@pytest.fixture
def modbus_config():
    return {
        'host': '127.0.0.1',
        'port': 5020,
        'timeout': 1.0
    }

class TestAsyncModbusService:
    @pytest.mark.asyncio
    async def test_connect_success(self, modbus_config):
        service = AsyncModbusService(modbus_config)
        result = await service.connect()
        assert result is True

    @pytest.mark.asyncio
    async def test_connect_timeout(self, modbus_config):
        modbus_config['timeout'] = 0.001
        service = AsyncModbusService(modbus_config)
        with pytest.raises(ModbusConnectionError):
            await service.connect()
```

**Patterns:**
- Use `@pytest.mark.asyncio` for async tests
- Use fixtures for shared setup
- Use `pytest.raises()` for exception testing

## Mocking

**Framework:**
- unittest.mock (expected)
- pytest-mock (available)

**Patterns:**
```python
# Expected pattern for Modbus mocking:
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_read_registers(mocker):
    mock_client = AsyncMock()
    mock_client.read_holding_registers.return_value = Mock(registers=[100, 200])

    with patch('src.services.modbus.client.AsyncModbusTcpClient', return_value=mock_client):
        service = AsyncModbusService(config)
        await service.connect()
        result = await service.read_holding_registers(2000, 2)
        assert result == [100, 200]
```

**What to Mock:**
- Modbus TCP connections (pymodbus client)
- Database connections (SQLite, PostgreSQL)
- MQTT broker connections
- File system operations
- Time/datetime (for session tracking)

**What NOT to Mock:**
- Internal pure functions
- Dataclass creation
- Config parsing (use fixtures)

## Fixtures and Factories

**Test Data:**
```python
# Expected pattern for sensor data:
@pytest.fixture
def sample_sensor_data():
    return RawSensorData(
        timestamp=datetime.now(),
        serit_motor_akim_a=5.5,
        serit_kesme_hizi=65.0,
        testere_durumu=3  # Cutting state
    )

@pytest.fixture
def sample_config():
    return {
        'modbus': {'host': '127.0.0.1', 'port': 5020},
        'control': {'default_mode': 'manual'},
        'database': {'path': ':memory:'}
    }
```

**Location:**
- Expected: `tests/conftest.py` for shared fixtures
- Expected: `tests/fixtures/` for sample data files

## Coverage

**Requirements:**
- No coverage target defined
- pytest-cov >= 4.1.0 available

**Configuration:**
- Not configured

**View Coverage:**
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Test Types

**Unit Tests:**
- Not implemented
- Scope: Individual functions/classes
- Examples needed: Validators, preprocessor, anomaly detectors

**Integration Tests:**
- Not implemented
- Scope: Service layer (Modbus, database, control)
- Mock external connections

**E2E Tests:**
- Not implemented
- Would require: Modbus simulator, test database

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result == expected
```

**Error Testing:**
```python
def test_throws_on_invalid_input():
    with pytest.raises(ValidationError):
        validate_speed(-100)

@pytest.mark.asyncio
async def test_async_error():
    with pytest.raises(ModbusConnectionError):
        await service.connect()
```

**Snapshot Testing:**
- Not used in this codebase
- Would be useful for GUI testing

## Critical Testing Gaps

**HIGH PRIORITY - No tests exist for:**
1. Modbus communication - Critical for PLC control
2. ML inference - Speed calculations affect machine operation
3. Anomaly detection - Safety-critical feature
4. Control mode switching - Core business logic
5. Database operations - Data integrity

**MEDIUM PRIORITY:**
6. Config parsing and validation
7. Data processing pipeline
8. Cutting session tracking
9. MQTT telemetry

**Implications:**
- All code changes require manual verification
- No regression protection
- CI/CD cannot validate changes
- Refactoring is high-risk

## Recommended Test Setup

```bash
# Create test structure
mkdir -p tests
touch tests/__init__.py
touch tests/conftest.py

# Add to pyproject.toml:
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]

# Run tests
pytest -v
pytest --cov=src --cov-report=term-missing
```

---

*Testing analysis: 2026-01-14*
*Update when test patterns change*
