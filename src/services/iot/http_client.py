"""
HTTP-based ThingsBoard telemetry sender.

Based on old project's working implementation.
Uses httpx for HTTP requests with retry and exponential backoff.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import httpx
except ImportError:
    httpx = None
    logging.warning("httpx not installed - HTTP functionality disabled")

from .thingsboard import ThingsBoardFormatter

logger = logging.getLogger(__name__)

# Offline storage directory
OFFLINE_DATA_DIR = Path("data/http_offline")


class HTTPThingsBoardService:
    """
    HTTP-based ThingsBoard telemetry sender.

    Features:
    - HTTP POST to ThingsBoard REST API
    - Retry with exponential backoff
    - Offline data storage when disconnected
    - Batch sending support
    - Sends stored data on reconnection
    """

    def __init__(self, config: dict):
        """
        Initialize HTTP ThingsBoard service.

        Args:
            config: Full application configuration dictionary
        """
        if httpx is None:
            raise RuntimeError("httpx not installed - cannot use HTTP service")

        self.config = config
        iot_config = config['iot']['thingsboard']
        http_config = iot_config.get('http', {})

        # Connection settings
        self.host = http_config.get('host', '185.87.252.58')
        self.port = http_config.get('port', 8081)
        self.access_token = http_config.get('access_token') or iot_config.get('access_token', '')
        self.timeout_seconds = http_config.get('timeout_seconds', 10.0)

        # Build base URL
        self.base_url = f"http://{self.host}:{self.port}"

        # Retry settings
        self.max_retries = 3
        self.backoff_factor = 0.5

        # Batch settings (from MQTT config for compatibility)
        mqtt_config = iot_config.get('mqtt', {})
        self.batch_size = mqtt_config.get('batch_size', 100)
        self.batch_interval = mqtt_config.get('batch_interval_seconds', 1.0)

        # State
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False
        self._running = False

        # Batch queue
        self._batch_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)

        # Background tasks
        self._batch_sender_task: Optional[asyncio.Task] = None

        # Formatter
        self.formatter = ThingsBoardFormatter(config['iot'])

        # Offline storage
        self._offline_file: Optional[Path] = None
        self._offline_count = 0
        self._ensure_offline_dir()

        # Statistics
        self._stats = {
            'messages_queued': 0,
            'messages_sent': 0,
            'batches_sent': 0,
            'errors': 0,
            'offline_stored': 0,
            'offline_sent': 0,
            'last_error': None,
            'last_error_time': None
        }

        logger.info(
            f"HTTPThingsBoardService initialized: "
            f"url={self.base_url}, "
            f"token={self.access_token[:8]}..., "
            f"batch_size={self.batch_size}"
        )

    def _ensure_offline_dir(self):
        """Ensure offline data directory exists."""
        try:
            OFFLINE_DATA_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create offline directory: {e}")

    def _get_offline_file_path(self) -> Path:
        """Get current offline data file path."""
        if self._offline_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._offline_file = OFFLINE_DATA_DIR / f"http_offline_{timestamp}.jsonl"
        return self._offline_file

    def _store_offline(self, telemetry: dict):
        """
        Store telemetry data to offline file.

        Args:
            telemetry: Telemetry data dict
        """
        try:
            # Add timestamp if not present
            if 'ts' not in telemetry:
                telemetry['ts'] = int(datetime.now().timestamp() * 1000)

            file_path = self._get_offline_file_path()

            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(telemetry) + '\n')

            self._offline_count += 1
            self._stats['offline_stored'] += 1

            if self._offline_count % 100 == 0:
                logger.info(f"Offline storage: {self._offline_count} records saved to {file_path.name}")

        except Exception as e:
            logger.error(f"Failed to store offline data: {e}")

    def _build_url(self, path: str) -> str:
        """Build ThingsBoard API URL with access token."""
        return f"{self.base_url}/api/v1/{self.access_token}{path}"

    async def _post_json(self, url: str, payload: Any, operation: str = "unknown") -> bool:
        """
        POST JSON with retry and exponential backoff.

        Args:
            url: Target URL
            payload: JSON payload
            operation: Operation name for logging

        Returns:
            True if successful
        """
        if self._client is None:
            logger.error("HTTP client not initialized")
            return False

        delay = self.backoff_factor

        for attempt in range(self.max_retries):
            try:
                response = await self._client.post(url, json=payload)

                if response.status_code in (200, 204):
                    if attempt > 0:
                        logger.info(f"[TB] {operation} successful (retry {attempt+1})")
                    return True

                # 5xx: server error → retry
                if 500 <= response.status_code < 600:
                    error_msg = f"HTTP {response.status_code}"
                    if attempt < self.max_retries - 1:
                        logger.warning(f"[TB] {operation}: {error_msg}, retrying...")
                    else:
                        logger.error(f"[TB] {operation}: {error_msg}, max retries reached")
                        self._record_failure(operation, error_msg)
                        return False

                # 4xx: client error → don't retry
                elif 400 <= response.status_code < 500:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(f"[TB] {operation}: {error_msg}")
                    self._record_failure(operation, error_msg)
                    return False

                else:
                    error_msg = f"HTTP {response.status_code}"
                    logger.warning(f"[TB] {operation}: Unexpected {error_msg}")
                    self._record_failure(operation, error_msg)
                    return False

            except httpx.TimeoutException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"[TB] {operation}: Timeout (attempt {attempt+1}), retrying...")
                else:
                    logger.error(f"[TB] {operation}: Timeout, max retries reached")
                    self._record_failure(operation, f"Timeout: {e}")
                    return False

            except httpx.ConnectError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"[TB] {operation}: Connection error (attempt {attempt+1}), retrying...")
                else:
                    logger.error(f"[TB] {operation}: Connection error, max retries reached")
                    self._record_failure(operation, f"Connection: {e}")
                    self._connected = False
                    return False

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"[TB] {operation}: {type(e).__name__} (attempt {attempt+1}), retrying...")
                else:
                    logger.error(f"[TB] {operation}: {type(e).__name__}, max retries reached: {e}")
                    self._record_failure(operation, f"{type(e).__name__}: {e}")
                    return False

            # Exponential backoff
            if attempt < self.max_retries - 1 and delay > 0:
                await asyncio.sleep(delay * (2 ** attempt))

        return False

    def _record_failure(self, operation: str, error: str):
        """Record failure in statistics."""
        self._stats['errors'] += 1
        self._stats['last_error'] = error
        self._stats['last_error_time'] = datetime.now().isoformat()

    async def connect(self) -> bool:
        """
        Initialize HTTP client and test connection.

        Returns:
            True if connection test successful
        """
        if not self.access_token or self.access_token.strip() == '':
            logger.warning("ThingsBoard access token not configured - skipping connection")
            return False

        try:
            # Create async HTTP client with timeout
            timeout = httpx.Timeout(
                connect=10.0,
                read=self.timeout_seconds,
                write=10.0,
                pool=10.0
            )

            self._client = httpx.AsyncClient(
                timeout=timeout,
                http2=False
            )

            # Test connection with empty telemetry (ThingsBoard accepts this)
            test_url = self._build_url("/telemetry")

            try:
                response = await self._client.post(test_url, json={})

                if response.status_code in (200, 204):
                    self._connected = True
                    logger.info(f"HTTP ThingsBoard connected: {self.base_url}")
                    return True
                elif response.status_code == 401:
                    logger.error(f"ThingsBoard authentication failed - check access token")
                    self._connected = False
                    return False
                else:
                    logger.warning(f"ThingsBoard connection test returned HTTP {response.status_code}")
                    # Still mark as connected - server is reachable
                    self._connected = True
                    return True

            except httpx.ConnectError as e:
                logger.error(f"Cannot connect to ThingsBoard at {self.base_url}: {e}")
                self._connected = False
                return False

        except Exception as e:
            logger.error(f"HTTP connection initialization failed: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Close HTTP client."""
        if self._client:
            try:
                await self._client.aclose()
                self._connected = False
                logger.info("HTTP ThingsBoard disconnected")
            except Exception as e:
                logger.error(f"Error closing HTTP client: {e}")

    async def start(self):
        """Start HTTP service (connection + batch sender)."""
        if self._running:
            logger.warning("HTTP service already running")
            return

        self._running = True

        # Try to connect
        await self.connect()

        # Start batch sender
        self._batch_sender_task = asyncio.create_task(self._batch_sender_loop())

        logger.info("HTTP ThingsBoard service started")

    async def stop(self, timeout: float = 5.0):
        """
        Stop HTTP service.

        Args:
            timeout: Maximum time to wait for graceful shutdown
        """
        if not self._running:
            return

        self._running = False

        # Cancel batch sender
        if self._batch_sender_task:
            self._batch_sender_task.cancel()

        # Flush remaining queue
        await self._flush_queue()

        # Close client
        await self.disconnect()

        logger.info("HTTP ThingsBoard service stopped")

    async def _flush_queue(self):
        """Flush remaining queue - send if connected, store offline if not."""
        while not self._batch_queue.empty():
            if self._connected:
                await self._send_batch_internal()
            else:
                try:
                    item = self._batch_queue.get_nowait()
                    self._store_offline(item)
                except asyncio.QueueEmpty:
                    break

    async def queue_telemetry(self, processed_data, vision_data=None):
        """
        Queue telemetry data for batch sending.

        Args:
            processed_data: ProcessedData instance
            vision_data: Optional dict with camera vision fields
        """
        try:
            # Format for ThingsBoard
            telemetry = self.formatter.format_telemetry(processed_data, vision_data=vision_data)

            if telemetry:
                # Ensure timestamp
                if 'ts' not in telemetry:
                    telemetry['ts'] = int(datetime.now().timestamp() * 1000)

                if self._connected:
                    try:
                        self._batch_queue.put_nowait(telemetry)
                        self._stats['messages_queued'] += 1

                        logger.debug(
                            f"Telemetry queued: "
                            f"queue_size={self._batch_queue.qsize()}"
                        )
                    except asyncio.QueueFull:
                        self._store_offline(telemetry)
                        logger.warning("Batch queue full, storing offline")
                else:
                    self._store_offline(telemetry)

        except Exception as e:
            logger.debug(f"Error queuing telemetry: {e}")
            self._stats['errors'] += 1

    async def _batch_sender_loop(self):
        """Background task: Send batches periodically."""
        logger.info("HTTP batch sender loop started")

        while self._running:
            try:
                await asyncio.sleep(self.batch_interval)

                if self._connected and not self._batch_queue.empty():
                    await self._send_batch_internal()

            except asyncio.CancelledError:
                logger.info("HTTP batch sender loop cancelled")
                break

            except Exception as e:
                logger.debug(f"Error in HTTP batch sender loop: {e}")
                self._stats['errors'] += 1

        logger.info("HTTP batch sender loop ended")

    async def _send_batch_internal(self):
        """Send accumulated telemetry batch to ThingsBoard."""
        if not self._connected or self._batch_queue.empty():
            return

        batch = []
        try:
            # Collect batch items
            while len(batch) < self.batch_size:
                try:
                    item = self._batch_queue.get_nowait()
                    batch.append(item)
                except asyncio.QueueEmpty:
                    break

            if not batch:
                return

            # ThingsBoard accepts array of telemetry objects
            url = self._build_url("/telemetry")
            success = await self._post_json(url, batch, operation="send_telemetry")

            if success:
                self._stats['messages_sent'] += len(batch)
                self._stats['batches_sent'] += 1

                logger.info(
                    f"HTTP telemetry batch sent: "
                    f"size={len(batch)}, "
                    f"remaining={self._batch_queue.qsize()}"
                )
            else:
                # Store failed batch to offline
                for item in batch:
                    self._store_offline(item)

        except Exception as e:
            logger.error(f"Error sending HTTP batch: {e}")
            self._stats['errors'] += 1

            # Store failed batch to offline
            for item in batch:
                self._store_offline(item)

    async def _send_offline_data(self):
        """Send all stored offline data to ThingsBoard."""
        if not self._connected:
            return

        try:
            offline_files = sorted(OFFLINE_DATA_DIR.glob("http_offline_*.jsonl"))

            if not offline_files:
                return

            total_sent = 0

            for file_path in offline_files:
                try:
                    records = []

                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    records.append(json.loads(line))
                                except json.JSONDecodeError:
                                    continue

                    if not records:
                        file_path.unlink()
                        continue

                    logger.info(f"Sending {len(records)} offline records from {file_path.name}")

                    # Send in batches
                    url = self._build_url("/telemetry")

                    for i in range(0, len(records), self.batch_size):
                        batch = records[i:i + self.batch_size]

                        success = await self._post_json(url, batch, operation="send_offline")

                        if success:
                            total_sent += len(batch)
                            self._stats['offline_sent'] += len(batch)
                            await asyncio.sleep(0.1)  # Small delay between batches
                        else:
                            logger.error("Failed to send offline batch, stopping")
                            return

                    # All sent successfully, delete file
                    file_path.unlink()
                    logger.info(f"Offline file {file_path.name} sent and deleted")

                except Exception as e:
                    logger.error(f"Error processing offline file {file_path}: {e}")

            if total_sent > 0:
                logger.info(f"Total offline records sent: {total_sent}")

        except Exception as e:
            logger.error(f"Error sending offline data: {e}")

    async def try_reconnect(self) -> bool:
        """
        Manually attempt to reconnect.

        Returns:
            True if reconnected successfully
        """
        if self._connected:
            return True

        logger.info("HTTP reconnect attempt...")

        # Close existing client
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass

        connected = await self.connect()

        if connected:
            # Send any stored offline data
            await self._send_offline_data()

        return connected

    async def publish_attributes(self, attributes: dict) -> bool:
        """
        Publish device attributes to ThingsBoard.

        Args:
            attributes: Dictionary with device attributes

        Returns:
            True if published successfully
        """
        if not self._connected:
            logger.warning("Cannot publish attributes - not connected")
            return False

        url = self._build_url("/attributes")
        return await self._post_json(url, attributes, operation="publish_attributes")

    @property
    def is_connected(self) -> bool:
        """Check if HTTP is connected."""
        return self._connected

    @property
    def offline_mode(self) -> bool:
        """Check if running in offline mode."""
        return not self._connected and self._running

    def get_stats(self) -> dict:
        """Get HTTP service statistics."""
        return {
            **self._stats,
            'connected': self._connected,
            'running': self._running,
            'offline_mode': self.offline_mode,
            'queue_size': self._batch_queue.qsize(),
            'queue_max': self._batch_queue.maxsize,
            'offline_file': str(self._offline_file) if self._offline_file else None,
            'offline_count': self._offline_count,
            'protocol': 'http',
            'base_url': self.base_url
        }
