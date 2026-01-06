"""
Async MQTT client with batch sending to ThingsBoard.

Features:
- Offline data storage when disconnected
- Automatic send of stored data on reconnection
- No aggressive reconnect attempts
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Optional, List
from collections import deque
from pathlib import Path

try:
    import aiomqtt
except ImportError:
    aiomqtt = None
    logging.warning("aiomqtt not installed - MQTT functionality disabled")

from .thingsboard import ThingsBoardFormatter

logger = logging.getLogger(__name__)

# Offline storage directory
OFFLINE_DATA_DIR = Path("data/mqtt_offline")


class MQTTService:
    """
    Async MQTT client with batch sending and offline storage.

    Features:
    - Connects to ThingsBoard MQTT broker
    - Batches telemetry (configurable size/interval)
    - QoS 1 (at least once delivery)
    - Offline data storage when disconnected
    - Sends stored data on reconnection
    - No aggressive reconnect (manual reconnect only)
    """

    def __init__(self, config: dict):
        """
        Initialize MQTT service.

        Args:
            config: IoT configuration dictionary
        """
        if aiomqtt is None:
            raise RuntimeError("aiomqtt not installed - cannot use MQTT service")

        self.config = config
        mqtt_config = config['iot']['thingsboard']['mqtt']

        # Connection settings
        self.broker = mqtt_config['broker']
        self.port = mqtt_config['port']
        self.username = mqtt_config.get('username', '')
        self.password = mqtt_config.get('password', '')
        self.keepalive = mqtt_config.get('keepalive', 60)
        self.qos = mqtt_config.get('qos', 1)

        # Batch settings
        self.batch_size = mqtt_config.get('batch_size', 10)
        self.batch_interval = mqtt_config.get('batch_interval_seconds', 5.0)

        # ThingsBoard topics
        self.telemetry_topic = f"v1/devices/me/telemetry"
        self.attributes_topic = f"v1/devices/me/attributes"

        # State
        self._client: Optional[aiomqtt.Client] = None
        self._connected = False
        self._running = False
        self._initial_connection_failed = False

        # Batch queue
        self._batch_queue: deque = deque(maxlen=1000)
        self._batch_lock = asyncio.Lock()

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
            'offline_sent': 0
        }

        logger.info(
            f"MQTTService initialized: "
            f"broker={self.broker}:{self.port}, "
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
            self._offline_file = OFFLINE_DATA_DIR / f"mqtt_offline_{timestamp}.jsonl"
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

    async def _send_offline_data(self):
        """Send all stored offline data to MQTT broker."""
        if not self._connected:
            return

        try:
            # Find all offline files
            offline_files = sorted(OFFLINE_DATA_DIR.glob("mqtt_offline_*.jsonl"))

            if not offline_files:
                logger.debug("No offline data files to send")
                return

            total_sent = 0

            for file_path in offline_files:
                try:
                    records = []

                    # Read all records from file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    records.append(json.loads(line))
                                except json.JSONDecodeError:
                                    continue

                    if not records:
                        # Empty file, delete it
                        file_path.unlink()
                        continue

                    logger.info(f"Sending {len(records)} offline records from {file_path.name}")

                    # Send in batches
                    for i in range(0, len(records), self.batch_size):
                        batch = records[i:i + self.batch_size]

                        try:
                            payload = json.dumps(batch)
                            await self._client.publish(
                                self.telemetry_topic,
                                payload=payload,
                                qos=self.qos
                            )
                            total_sent += len(batch)
                            self._stats['offline_sent'] += len(batch)

                            # Small delay between batches
                            await asyncio.sleep(0.1)

                        except Exception as e:
                            logger.error(f"Failed to send offline batch: {e}")
                            # Stop sending, keep remaining data
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

    async def connect(self) -> bool:
        """
        Establish MQTT connection to ThingsBoard.

        Returns:
            True if connected successfully
        """
        # Don't connect if broker is empty
        if not self.broker or self.broker.strip() == '':
            logger.warning("MQTT broker not configured - skipping connection")
            self._initial_connection_failed = True
            return False

        try:
            self._client = aiomqtt.Client(
                hostname=self.broker,
                port=self.port,
                username=self.username,
                password=self.password,
                keepalive=self.keepalive,
                clean_session=True
            )

            await self._client.__aenter__()
            self._connected = True
            self._initial_connection_failed = False

            logger.info(f"MQTT connected: {self.broker}:{self.port}")

            # Send any stored offline data
            await self._send_offline_data()

            return True

        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            self._connected = False
            self._initial_connection_failed = True
            return False

    async def disconnect(self):
        """
        Disconnect from MQTT broker.
        """
        if self._client:
            try:
                await self._client.__aexit__(None, None, None)
                self._connected = False
                logger.info("MQTT disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting MQTT: {e}")

    async def start(self):
        """
        Start MQTT service (connection + batch sender).
        """
        if self._running:
            logger.warning("MQTT service already running")
            return

        self._running = True

        # Try to connect (but don't fail if it doesn't work)
        await self.connect()

        # Start batch sender
        self._batch_sender_task = asyncio.create_task(self._batch_sender_loop())

        logger.info("MQTT service started")

    async def stop(self, timeout: float = 5.0):
        """
        Stop MQTT service.

        Args:
            timeout: Maximum time to wait for graceful shutdown
        """
        if not self._running:
            return

        self._running = False

        # Cancel tasks
        if self._batch_sender_task:
            self._batch_sender_task.cancel()

        # Send remaining batch or store offline
        await self._flush_queue()

        # Disconnect
        await self.disconnect()

        logger.info("MQTT service stopped")

    async def _flush_queue(self):
        """Flush remaining queue - send if connected, store offline if not."""
        async with self._batch_lock:
            while len(self._batch_queue) > 0:
                if self._connected:
                    await self._send_batch_internal()
                else:
                    # Store all remaining to offline
                    item = self._batch_queue.popleft()
                    self._store_offline(item)

    async def queue_telemetry(self, processed_data):
        """
        Queue telemetry data for batch sending.

        Args:
            processed_data: ProcessedData instance
        """
        async with self._batch_lock:
            try:
                # Format for ThingsBoard
                telemetry = self.formatter.format_telemetry(processed_data)

                if telemetry:
                    # Add timestamp
                    telemetry['ts'] = int(datetime.now().timestamp() * 1000)

                    if self._connected:
                        self._batch_queue.append(telemetry)
                        self._stats['messages_queued'] += 1

                        logger.debug(
                            f"Telemetry queued: "
                            f"queue_size={len(self._batch_queue)}"
                        )
                    else:
                        # Store offline
                        self._store_offline(telemetry)

            except Exception as e:
                logger.debug(f"Error queuing telemetry: {e}")
                self._stats['errors'] += 1

    async def _batch_sender_loop(self):
        """
        Background task: Send batches periodically.
        """
        logger.info("Batch sender loop started")

        while self._running:
            try:
                # Wait for batch interval
                await asyncio.sleep(self.batch_interval)

                # Send batch if connected and queue not empty
                if self._connected and len(self._batch_queue) > 0:
                    await self._send_batch()

            except asyncio.CancelledError:
                logger.info("Batch sender loop cancelled")
                break

            except Exception as e:
                logger.debug(f"Error in batch sender loop: {e}")
                self._stats['errors'] += 1

        logger.info("Batch sender loop ended")

    async def _send_batch(self):
        """Send accumulated telemetry batch to ThingsBoard."""
        async with self._batch_lock:
            await self._send_batch_internal()

    async def _send_batch_internal(self):
        """Internal batch send (must be called with lock held)."""
        if not self._connected or len(self._batch_queue) == 0:
            return

        try:
            # Get batch
            batch_size = min(len(self._batch_queue), self.batch_size)
            batch = [self._batch_queue.popleft() for _ in range(batch_size)]

            # ThingsBoard accepts array of telemetry objects
            payload = json.dumps(batch)

            # Publish
            await self._client.publish(
                self.telemetry_topic,
                payload=payload,
                qos=self.qos
            )

            self._stats['messages_sent'] += batch_size
            self._stats['batches_sent'] += 1

            logger.info(
                f"Telemetry batch sent: "
                f"size={batch_size}, "
                f"remaining={len(self._batch_queue)}"
            )

        except Exception as e:
            logger.error(f"Error sending batch: {e}")
            self._stats['errors'] += 1
            self._connected = False

            # Store failed batch to offline
            for item in batch:
                self._store_offline(item)

    async def try_reconnect(self) -> bool:
        """
        Manually attempt to reconnect to MQTT broker.

        Call this method when you want to retry connection
        (e.g., from a GUI button or scheduled task).

        Returns:
            True if reconnected successfully
        """
        if self._connected:
            return True

        logger.info("Manual reconnect attempt...")

        # Disconnect first if client exists
        if self._client:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception:
                pass

        return await self.connect()

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

        try:
            payload = json.dumps(attributes)

            await self._client.publish(
                self.attributes_topic,
                payload=payload,
                qos=self.qos
            )

            logger.info(f"Attributes published: {list(attributes.keys())}")
            return True

        except Exception as e:
            logger.debug(f"Error publishing attributes: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        """Check if MQTT is connected."""
        return self._connected

    @property
    def offline_mode(self) -> bool:
        """Check if running in offline mode (storing to file)."""
        return not self._connected and self._running

    def get_stats(self) -> dict:
        """
        Get MQTT service statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            **self._stats,
            'connected': self._connected,
            'running': self._running,
            'offline_mode': self.offline_mode,
            'queue_size': len(self._batch_queue),
            'queue_max': self._batch_queue.maxlen,
            'offline_file': str(self._offline_file) if self._offline_file else None,
            'offline_count': self._offline_count
        }
