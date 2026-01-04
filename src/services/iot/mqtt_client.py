"""
Async MQTT client with batch sending to ThingsBoard.
"""

import asyncio
import logging
import json
from typing import Optional, List
from collections import deque

try:
    import aiomqtt
except ImportError:
    aiomqtt = None
    logging.warning("aiomqtt not installed - MQTT functionality disabled")

from .thingsboard import ThingsBoardFormatter

logger = logging.getLogger(__name__)


class MQTTService:
    """
    Async MQTT client with batch sending.

    Features:
    - Connects to ThingsBoard MQTT broker
    - Batches telemetry (configurable size/interval)
    - QoS 1 (at least once delivery)
    - Auto-reconnect with exponential backoff
    - Health monitoring
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

        # Batch queue
        self._batch_queue: deque = deque(maxlen=1000)
        self._batch_lock = asyncio.Lock()

        # Background tasks
        self._batch_sender_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        # Formatter
        self.formatter = ThingsBoardFormatter(config['iot'])

        # Statistics
        self._stats = {
            'messages_queued': 0,
            'messages_sent': 0,
            'batches_sent': 0,
            'errors': 0,
            'reconnects': 0
        }

        logger.info(
            f"MQTTService initialized: "
            f"broker={self.broker}:{self.port}, "
            f"batch_size={self.batch_size}"
        )

    async def connect(self) -> bool:
        """
        Establish MQTT connection to ThingsBoard.

        Returns:
            True if connected successfully
        """
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

            logger.info(f"MQTT connected: {self.broker}:{self.port}")
            return True

        except Exception as e:
            # Log without traceback to keep logs clean
            logger.error(f"MQTT connection failed: {e}")
            self._connected = False
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

        # Connect
        await self.connect()

        # Start batch sender
        self._batch_sender_task = asyncio.create_task(self._batch_sender_loop())

        # Start reconnect monitor
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())

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
        if self._reconnect_task:
            self._reconnect_task.cancel()

        # Send remaining batch
        await self._send_batch()

        # Disconnect
        await self.disconnect()

        logger.info("MQTT service stopped")

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
                    self._batch_queue.append(telemetry)
                    self._stats['messages_queued'] += 1

                    logger.debug(
                        f"Telemetry queued: "
                        f"queue_size={len(self._batch_queue)}"
                    )

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

                # Send batch if queue not empty
                if len(self._batch_queue) > 0:
                    await self._send_batch()

            except asyncio.CancelledError:
                logger.info("Batch sender loop cancelled")
                break

            except Exception as e:
                logger.debug(f"Error in batch sender loop: {e}")
                self._stats['errors'] += 1

        logger.info("Batch sender loop ended")

    async def _send_batch(self):
        """
        Send accumulated telemetry batch to ThingsBoard.
        """
        async with self._batch_lock:
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
                logger.debug(f"Error sending batch: {e}")
                self._stats['errors'] += 1

                # Re-queue batch on error
                for item in batch:
                    if len(self._batch_queue) < self._batch_queue.maxlen:
                        self._batch_queue.appendleft(item)

    async def _reconnect_loop(self):
        """
        Background task: Monitor connection and reconnect if needed.
        """
        logger.info("Reconnect monitor started")

        backoff = 1.0  # seconds
        max_backoff = 60.0

        while self._running:
            try:
                # Check connection
                if not self._connected:
                    logger.warning(f"MQTT disconnected - reconnecting in {backoff}s")
                    await asyncio.sleep(backoff)

                    # Attempt reconnect
                    success = await self.connect()

                    if success:
                        backoff = 1.0  # Reset backoff on success
                        self._stats['reconnects'] += 1
                    else:
                        # Exponential backoff
                        backoff = min(backoff * 2, max_backoff)

                else:
                    # Connected - check periodically
                    await asyncio.sleep(10.0)
                    backoff = 1.0  # Reset backoff

            except asyncio.CancelledError:
                logger.info("Reconnect monitor cancelled")
                break

            except Exception as e:
                logger.debug(f"Error in reconnect loop: {e}")
                await asyncio.sleep(backoff)

        logger.info("Reconnect monitor ended")

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
            'queue_size': len(self._batch_queue),
            'queue_max': self._batch_queue.maxlen
        }
