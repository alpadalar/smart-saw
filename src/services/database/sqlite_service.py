"""
Thread-safe SQLite service using single-writer pattern.

Architecture:
- All writes go through a Queue to a dedicated writer thread
- Reads use thread-local connections (query_only=ON)
- Batch commits every 100 writes or 1 second
- WAL mode for concurrent read/write
"""

import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from typing import List, Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SQLiteService:
    """Thread-safe SQLite database service."""

    def __init__(self, db_path: Path, schema_sql: str):
        """
        Initialize SQLite service.

        Args:
            db_path: Path to database file
            schema_sql: SQL schema creation script
        """
        self.db_path = db_path
        self.schema_sql = schema_sql

        # Thread-safe queue for write operations
        self._write_queue: Queue = Queue(maxsize=10000)

        # Writer thread
        self._writer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Thread-local storage for read connections
        self._thread_local = threading.local()

        # Statistics
        self._stats_lock = threading.Lock()
        self._stats = {
            "writes_queued": 0,
            "writes_completed": 0,
            "writes_failed": 0,
            "reads_completed": 0,
            "queue_full_count": 0
        }

    def start(self):
        """Start the database service."""
        # Initialize database
        self._initialize_database()

        # Start writer thread
        self._stop_event.clear()
        self._writer_thread = threading.Thread(
            target=self._writer_loop,
            name=f"SQLiteWriter-{self.db_path.name}",
            daemon=True
        )
        self._writer_thread.start()
        logger.info(f"SQLite service started: {self.db_path}")

    def stop(self, timeout: float = 5.0):
        """
        Stop the database service.

        Args:
            timeout: Maximum time to wait for writer thread
        """
        self._stop_event.set()

        # Send poison pill
        try:
            self._write_queue.put_nowait(None)
        except:
            pass

        if self._writer_thread and self._writer_thread.is_alive():
            self._writer_thread.join(timeout=timeout)

        logger.info(f"SQLite service stopped: {self.db_path}")

    def _initialize_database(self):
        """Initialize database with schema and optimizations."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))

        try:
            # Performance optimizations
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            conn.execute("PRAGMA temp_store=MEMORY")

            # Create schema
            conn.executescript(self.schema_sql)
            conn.commit()

            logger.info(f"Database initialized: {self.db_path}")

        finally:
            conn.close()

    def _get_read_connection(self) -> sqlite3.Connection:
        """Get thread-local read connection."""
        if not hasattr(self._thread_local, 'conn'):
            self._thread_local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            # Read-only optimizations
            self._thread_local.conn.execute("PRAGMA query_only=ON")

        return self._thread_local.conn

    def _writer_loop(self):
        """Dedicated writer thread loop."""
        # Create dedicated connection for writes
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

        batch = []
        batch_size = 100
        last_commit = time.time()
        commit_interval = 1.0  # 1 second

        while not self._stop_event.is_set():
            try:
                # Get item from queue (blocking with timeout)
                item = self._write_queue.get(timeout=0.1)

                # Poison pill check
                if item is None:
                    break

                batch.append(item)

                # Batch commit conditions
                should_commit = (
                    len(batch) >= batch_size or
                    (time.time() - last_commit) >= commit_interval
                )

                if should_commit:
                    self._execute_batch(conn, batch)
                    batch.clear()
                    last_commit = time.time()

            except Empty:
                # Timeout - commit any pending batch
                if batch:
                    self._execute_batch(conn, batch)
                    batch.clear()
                    last_commit = time.time()

            except Exception as e:
                logger.error(f"Writer loop error: {e}", exc_info=True)

        # Final batch commit
        if batch:
            self._execute_batch(conn, batch)

        conn.close()

    def _execute_batch(self, conn: sqlite3.Connection, batch: List[Dict]):
        """Execute batch write operations."""
        try:
            for item in batch:
                sql = item['sql']
                params = item['params']
                conn.execute(sql, params)

            conn.commit()

            with self._stats_lock:
                self._stats['writes_completed'] += len(batch)

        except Exception as e:
            logger.error(f"Batch execution error: {e}", exc_info=True)
            conn.rollback()

            with self._stats_lock:
                self._stats['writes_failed'] += len(batch)

    # Public API

    def write_async(self, sql: str, params: Tuple = ()) -> bool:
        """
        Asynchronous write operation (queues the write).

        Args:
            sql: SQL statement
            params: Query parameters

        Returns:
            True if queued successfully, False if queue is full
        """
        try:
            self._write_queue.put_nowait({
                'sql': sql,
                'params': params
            })

            with self._stats_lock:
                self._stats['writes_queued'] += 1

            return True

        except:
            with self._stats_lock:
                self._stats['queue_full_count'] += 1

            logger.warning(f"Write queue full for {self.db_path.name}")
            return False

    def read(self, sql: str, params: Tuple = ()) -> List[Tuple]:
        """
        Thread-safe read operation.

        Args:
            sql: SQL query
            params: Query parameters

        Returns:
            Query results as list of tuples
        """
        try:
            conn = self._get_read_connection()
            cursor = conn.execute(sql, params)
            result = cursor.fetchall()

            with self._stats_lock:
                self._stats['reads_completed'] += 1

            return result

        except Exception as e:
            logger.error(f"Read error: {e}", exc_info=True)
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        with self._stats_lock:
            stats = self._stats.copy()
            stats['queue_size'] = self._write_queue.qsize()
            return stats
