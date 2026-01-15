"""
Thread-safe SQLite service using single-writer pattern.

Architecture:
- All writes go through a Queue to a dedicated writer thread
- Reads use thread-local connections (query_only=ON)
- Batch commits every 100 writes or 1 second
- WAL mode for concurrent read/write
- Auto-detects schema mismatches and recreates database with backup
"""

import shutil
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from typing import List, Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Error patterns indicating schema mismatch
SCHEMA_MISMATCH_PATTERNS = [
    "has no column named",
    "no such column",
    "no such table",
    "table .* has no column",
]


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

        # Schema migration tracking
        self._schema_recreated = False
        self._recreate_lock = threading.Lock()

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

    def _is_schema_mismatch_error(self, error: Exception) -> bool:
        """Check if error indicates schema mismatch."""
        import re
        error_msg = str(error).lower()
        for pattern in SCHEMA_MISMATCH_PATTERNS:
            if re.search(pattern, error_msg):
                return True
        return False

    def _backup_and_recreate_database(self) -> bool:
        """
        Backup existing database and create fresh one with current schema.

        Returns:
            True if successful, False otherwise
        """
        with self._recreate_lock:
            # Prevent multiple recreations
            if self._schema_recreated:
                return False

            try:
                # Create backup filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.db_path.with_suffix(f".{timestamp}.backup")

                # Close any thread-local connections
                if hasattr(self._thread_local, 'conn'):
                    try:
                        self._thread_local.conn.close()
                    except:
                        pass
                    delattr(self._thread_local, 'conn')

                # Backup existing database
                if self.db_path.exists():
                    shutil.copy2(self.db_path, backup_path)
                    logger.warning(f"Database backed up to: {backup_path}")

                    # Also backup WAL and SHM files if they exist
                    for ext in ['-wal', '-shm']:
                        wal_path = Path(str(self.db_path) + ext)
                        if wal_path.exists():
                            shutil.copy2(wal_path, Path(str(backup_path) + ext))

                    # Remove old database files
                    self.db_path.unlink()
                    for ext in ['-wal', '-shm']:
                        wal_path = Path(str(self.db_path) + ext)
                        if wal_path.exists():
                            wal_path.unlink()

                # Recreate database with current schema
                self._initialize_database()

                self._schema_recreated = True
                logger.warning(
                    f"Database recreated with new schema: {self.db_path}. "
                    f"Old data preserved in: {backup_path}"
                )

                return True

            except Exception as e:
                logger.error(f"Failed to backup and recreate database: {e}", exc_info=True)
                return False

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
                    new_conn = self._execute_batch(conn, batch)
                    if new_conn is not None:
                        conn = new_conn  # Use new connection after db recreate
                    batch.clear()
                    last_commit = time.time()

            except Empty:
                # Timeout - commit any pending batch
                if batch:
                    new_conn = self._execute_batch(conn, batch)
                    if new_conn is not None:
                        conn = new_conn  # Use new connection after db recreate
                    batch.clear()
                    last_commit = time.time()

            except Exception as e:
                logger.error(f"Writer loop error: {e}", exc_info=True)

        # Final batch commit
        if batch:
            self._execute_batch(conn, batch)

        conn.close()

    def _execute_batch(self, conn: sqlite3.Connection, batch: List[Dict]) -> Optional[sqlite3.Connection]:
        """
        Execute batch write operations.

        Returns:
            New connection if database was recreated, None otherwise
        """
        try:
            for item in batch:
                sql = item['sql']
                params = item['params']
                conn.execute(sql, params)

            conn.commit()

            with self._stats_lock:
                self._stats['writes_completed'] += len(batch)

            return None

        except Exception as e:
            # Check if this is a schema mismatch error
            if self._is_schema_mismatch_error(e) and not self._schema_recreated:
                logger.warning(
                    f"Schema mismatch detected: {e}. "
                    f"Backing up and recreating database..."
                )

                # Close current connection before recreating
                try:
                    conn.close()
                except:
                    pass

                # Backup old database and create new one
                if self._backup_and_recreate_database():
                    # Create new connection for writer thread
                    new_conn = sqlite3.connect(str(self.db_path))
                    new_conn.execute("PRAGMA journal_mode=WAL")
                    new_conn.execute("PRAGMA synchronous=NORMAL")

                    # Retry the batch with new connection
                    try:
                        for item in batch:
                            new_conn.execute(item['sql'], item['params'])
                        new_conn.commit()

                        with self._stats_lock:
                            self._stats['writes_completed'] += len(batch)

                        return new_conn
                    except Exception as retry_error:
                        logger.error(f"Batch retry failed after recreate: {retry_error}")
                        new_conn.rollback()
                        with self._stats_lock:
                            self._stats['writes_failed'] += len(batch)
                        return new_conn

            # Regular error handling
            logger.error(f"Batch execution error: {e}", exc_info=True)
            try:
                conn.rollback()
            except:
                pass

            with self._stats_lock:
                self._stats['writes_failed'] += len(batch)

            return None

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
            stats['schema_recreated'] = self._schema_recreated
            return stats
