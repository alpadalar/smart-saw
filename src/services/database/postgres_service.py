"""
Async PostgreSQL service with connection pooling.
"""

import asyncpg
import logging
from typing import Optional, List, Any

logger = logging.getLogger(__name__)


class PostgresService:
    """Async PostgreSQL database service."""

    def __init__(self, config: dict):
        """
        Initialize PostgreSQL service.

        Args:
            config: PostgreSQL configuration dictionary
        """
        self.config = config
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Establish connection pool."""
        try:
            self._pool = await asyncpg.create_pool(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['username'],
                password=self.config['password'],
                min_size=self.config.get('min_connections', 2),
                max_size=self.config.get('max_connections', 10),
                command_timeout=self.config.get('command_timeout', 30.0)
            )

            logger.info(f"PostgreSQL connected: {self.config['host']}:{self.config['port']}")

        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}", exc_info=True)
            raise

    async def disconnect(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("PostgreSQL disconnected")

    async def execute(self, sql: str, *params) -> str:
        """
        Execute SQL statement.

        Args:
            sql: SQL statement
            *params: Query parameters

        Returns:
            Execution status
        """
        async with self._pool.acquire() as conn:
            return await conn.execute(sql, *params)

    async def fetch(self, sql: str, *params) -> List[asyncpg.Record]:
        """
        Fetch query results.

        Args:
            sql: SQL query
            *params: Query parameters

        Returns:
            List of records
        """
        async with self._pool.acquire() as conn:
            return await conn.fetch(sql, *params)

    async def fetchrow(self, sql: str, *params) -> Optional[asyncpg.Record]:
        """
        Fetch single row.

        Args:
            sql: SQL query
            *params: Query parameters

        Returns:
            Single record or None
        """
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(sql, *params)
