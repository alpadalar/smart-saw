"""
Async Modbus TCP client with rate limiting and health monitoring.
"""

import asyncio
import logging
import time
from typing import Optional, List, Dict, Any
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

logger = logging.getLogger(__name__)


class AsyncModbusService:
    """Asyncio-based Modbus TCP client."""

    def __init__(self, host: str, port: int, config: dict):
        """Initialize Modbus service."""
        self.host = host
        self.port = port
        self.config = config

        self._client: Optional[AsyncModbusTcpClient] = None
        self._connected = False
        self._lock = asyncio.Lock()

        # Rate limiting
        self._read_semaphore = asyncio.Semaphore(config.get('read_rate', 10))
        self._write_semaphore = asyncio.Semaphore(config.get('write_rate', 5))

        # Connection cooldown (prevents repeated connection attempts when PLC is unreachable)
        self._last_connect_attempt: float = 0
        self._connect_cooldown: float = config.get('connect_cooldown', 1.0)

        # Health monitoring
        self._last_read_time: Optional[float] = None
        self._last_write_time: Optional[float] = None
        self._read_count = 0
        self._write_count = 0
        self._error_count = 0

    def _should_attempt_connect(self) -> bool:
        """Check if enough time has passed since last connection attempt."""
        elapsed = time.monotonic() - self._last_connect_attempt
        if elapsed >= self._connect_cooldown:
            return True
        logger.debug(
            f"Skipping connection attempt: cooldown active ({elapsed:.1f}s / {self._connect_cooldown:.1f}s)"
        )
        return False

    async def connect(self) -> bool:
        """Establish Modbus connection."""
        async with self._lock:
            # Record attempt time BEFORE connecting
            self._last_connect_attempt = time.monotonic()

            try:
                self._client = AsyncModbusTcpClient(
                    host=self.host,
                    port=self.port,
                    timeout=self.config.get('timeout', 5.0)
                )

                # Wrap connection with explicit timeout
                connect_timeout = self.config.get('timeout', 5.0)
                self._connected = await asyncio.wait_for(
                    self._client.connect(),
                    timeout=connect_timeout
                )

                if self._connected:
                    logger.info(f"Modbus connected: {self.host}:{self.port}")
                else:
                    logger.error(f"Modbus connection failed: {self.host}:{self.port}")

                return self._connected

            except asyncio.TimeoutError:
                logger.warning(
                    f"Modbus connection timeout after {self.config.get('timeout', 5.0)}s: {self.host}:{self.port}"
                )
                self._connected = False
                return False

            except Exception as e:
                logger.error(f"Modbus connection error: {e}", exc_info=True)
                self._connected = False
                return False

    async def disconnect(self):
        """Close Modbus connection."""
        async with self._lock:
            if self._client:
                self._client.close()
                self._connected = False
                logger.info("Modbus disconnected")

    async def read_holding_registers(
        self,
        address: int,
        count: int,
        unit: int = 1
    ) -> Optional[List[int]]:
        """
        Read holding registers (rate-limited).

        Args:
            address: Starting register address
            count: Number of registers to read
            unit: Modbus slave unit ID

        Returns:
            List of register values or None on error
        """
        async with self._read_semaphore:
            try:
                if not self._connected:
                    # Check cooldown before attempting reconnection
                    if not self._should_attempt_connect():
                        return None  # Skip operation during cooldown
                    await self.connect()
                    if not self._connected:
                        return None  # Connection failed

                # Wrap read operation with explicit timeout
                read_timeout = self.config.get('timeout', 5.0)
                result = await asyncio.wait_for(
                    self._client.read_holding_registers(
                        address=address,
                        count=count
                    ),
                    timeout=read_timeout
                )

                if result.isError():
                    logger.error(f"Modbus read error at {address}: {result}")
                    self._error_count += 1
                    return None

                self._read_count += 1
                self._last_read_time = asyncio.get_event_loop().time()

                return result.registers

            except asyncio.TimeoutError:
                logger.debug(f"Modbus read timeout at {address}")
                self._error_count += 1
                self._connected = False
                return None
            except ModbusException as e:
                # Log without traceback to keep logs clean
                logger.debug(f"Modbus read exception: {e}")
                self._error_count += 1
                self._connected = False
                return None
            except Exception as e:
                # Catch any other exceptions
                logger.debug(f"Unexpected error in Modbus read: {e}")
                self._error_count += 1
                self._connected = False
                return None

    async def write_register(
        self,
        address: int,
        value: int,
        unit: int = 1
    ) -> bool:
        """
        Write single register (rate-limited).

        Args:
            address: Register address
            value: Value to write (0-65535)
            unit: Modbus slave unit ID

        Returns:
            True if successful, False otherwise
        """
        async with self._write_semaphore:
            try:
                if not self._connected:
                    # Check cooldown before attempting reconnection
                    if not self._should_attempt_connect():
                        return False  # Skip operation during cooldown
                    await self.connect()
                    if not self._connected:
                        return False  # Connection failed

                # Wrap write operation with explicit timeout
                write_timeout = self.config.get('timeout', 5.0)
                result = await asyncio.wait_for(
                    self._client.write_register(
                        address=address,
                        value=value
                    ),
                    timeout=write_timeout
                )

                if result.isError():
                    logger.error(f"Modbus write error at {address}: {result}")
                    self._error_count += 1
                    return False

                self._write_count += 1
                self._last_write_time = asyncio.get_event_loop().time()

                return True

            except asyncio.TimeoutError:
                logger.debug(f"Modbus write timeout at {address}")
                self._error_count += 1
                self._connected = False
                return False
            except ModbusException as e:
                # Log without traceback to keep logs clean
                logger.debug(f"Modbus write exception: {e}")
                self._error_count += 1
                self._connected = False
                return False
            except Exception as e:
                # Catch any other exceptions
                logger.debug(f"Unexpected error in Modbus write: {e}")
                self._error_count += 1
                self._connected = False
                return False

    def get_health(self) -> Dict[str, Any]:
        """Get health status information."""
        now = asyncio.get_event_loop().time()

        return {
            'connected': self._connected,
            'read_count': self._read_count,
            'write_count': self._write_count,
            'error_count': self._error_count,
            'last_read_elapsed': now - self._last_read_time if self._last_read_time else None,
            'last_write_elapsed': now - self._last_write_time if self._last_write_time else None
        }
