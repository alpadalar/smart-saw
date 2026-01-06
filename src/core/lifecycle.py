"""
Application lifecycle manager - orchestrates all services.
"""

import asyncio
import logging
import signal
import threading
from pathlib import Path
from typing import Optional, Dict

from .config import ConfigManager
from .logger import setup_logging
from ..services.database.sqlite_service import SQLiteService
from ..services.database.postgres_service import PostgresService
from ..services.database.schemas import SCHEMAS
from ..services.modbus.client import AsyncModbusService
from ..services.modbus.reader import ModbusReader
from ..services.modbus.writer import ModbusWriter
from ..services.control.manager import ControlManager
from ..services.processing.data_processor import DataProcessingPipeline
from ..services.iot.mqtt_client import MQTTService

# GUI imports (optional)
try:
    from ..gui.app import GUIApplication
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    logger.warning("GUI not available - PySide2 not installed")

logger = logging.getLogger(__name__)


class ApplicationLifecycle:
    """
    Master orchestrator for all services.

    Startup sequence:
    1. Load configuration
    2. Setup logging
    3. Initialize databases (4 SQLite services)
    4. Connect Modbus
    5. Start control manager
    6. Start MQTT (optional)
    7. Start data pipeline
    8. Start background tasks (health monitoring)

    Shutdown sequence (reverse order):
    1. Stop data pipeline
    2. Stop MQTT
    3. Stop control manager
    4. Disconnect Modbus
    5. Flush and stop databases (10s timeout)
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize application lifecycle.

        Args:
            config_path: Path to config.yaml (optional, uses default if None)
        """
        # Configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config

        # Setup logging
        setup_logging(self.config.get('logging', {}))

        # Service containers
        self.db_services: Dict[str, SQLiteService] = {}
        self.postgres_service: Optional[PostgresService] = None
        self.modbus_service: Optional[AsyncModbusService] = None
        self.modbus_reader: Optional[ModbusReader] = None
        self.modbus_writer: Optional[ModbusWriter] = None
        self.control_manager: Optional[ControlManager] = None
        self.data_pipeline: Optional[DataProcessingPipeline] = None
        self.mqtt_service: Optional[MQTTService] = None
        self.gui_app: Optional['GUIApplication'] = None
        self.gui_thread: Optional[threading.Thread] = None

        # Background tasks
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        # State
        self._started = False

        logger.info("ApplicationLifecycle initialized")

    async def start(self):
        """
        Start all services in correct order.
        """
        if self._started:
            logger.warning("Application already started")
            return

        try:
            logger.info("=" * 60)
            logger.info("Starting Smart Band Saw Control System")
            logger.info("=" * 60)

            # 1. Initialize databases
            await self._init_databases()

            # 2. Connect Modbus
            await self._init_modbus()

            # 3. Initialize control manager
            await self._init_control_manager()

            # 4. Initialize MQTT (optional)
            await self._init_mqtt()

            # 5. Initialize data pipeline
            await self._init_data_pipeline()

            # 6. Start GUI (optional, in separate thread)
            await self._init_gui()

            # 7. Start background tasks
            await self._start_background_tasks()

            self._started = True

            logger.info("=" * 60)
            logger.info("All services started successfully")
            logger.info("=" * 60)
            logger.info("Application running - press Ctrl+C to stop")

        except Exception as e:
            logger.error(f"Fatal error during startup: {e}", exc_info=True)
            await self.stop()
            raise

    async def stop(self, timeout: float = 10.0):
        """
        Stop all services gracefully.

        Args:
            timeout: Maximum time to wait for each service
        """
        if not self._started:
            logger.warning("Application not started")
            return

        logger.info("=" * 60)
        logger.info("Stopping Smart Band Saw Control System")
        logger.info("=" * 60)

        try:
            # 0. Wait for GUI thread to finish FIRST
            # This is critical to avoid segmentation fault on Linux.
            # Qt objects (QTimers, widgets) must be destroyed in the GUI thread.
            # If we proceed with shutdown while GUI thread is still running,
            # Python's garbage collector may try to destroy Qt objects from
            # the wrong thread, causing "Timers cannot be stopped from another
            # thread" errors and segmentation faults.
            if self.gui_thread and self.gui_thread.is_alive():
                logger.info("Waiting for GUI thread to finish...")
                self.gui_thread.join(timeout=timeout)
                if self.gui_thread.is_alive():
                    logger.warning("GUI thread did not finish in time")
                else:
                    logger.info("GUI thread finished")

            # 1. Stop data pipeline
            if self.data_pipeline:
                logger.info("Stopping data pipeline...")
                await self.data_pipeline.stop(timeout=timeout)

            # 2. Stop MQTT
            if self.mqtt_service:
                logger.info("Stopping MQTT service...")
                await self.mqtt_service.stop(timeout=timeout)

            # 3. Disconnect Modbus
            if self.modbus_service:
                logger.info("Disconnecting Modbus...")
                await self.modbus_service.disconnect()

            # 4. Stop PostgreSQL
            if self.postgres_service:
                logger.info("Disconnecting PostgreSQL...")
                await self.postgres_service.disconnect()

            # 5. Stop SQLite services (flush queues)
            for db_name, db_service in self.db_services.items():
                logger.info(f"Stopping {db_name} database...")
                db_service.stop(timeout=timeout)

            # 6. Cancel background tasks
            if self._health_monitor_task:
                self._health_monitor_task.cancel()

            self._started = False

            logger.info("=" * 60)
            logger.info("All services stopped successfully")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

    async def run_forever(self):
        """
        Run until shutdown signal received.
        """
        logger.info("Application running - press Ctrl+C to stop")

        # Wait for shutdown event
        await self._shutdown_event.wait()

    def request_shutdown(self):
        """
        Request graceful shutdown.
        """
        logger.info("Shutdown requested")
        self._shutdown_event.set()

    # Initialization methods

    async def _init_databases(self):
        """
        Initialize all database services.
        """
        logger.info("Initializing databases...")

        db_config = self.config['database']['sqlite']
        db_path = Path(db_config['path'])
        db_path.mkdir(parents=True, exist_ok=True)

        # Create SQLite services for each database
        for db_name, filename in db_config['databases'].items():
            db_file = db_path / filename
            schema_sql = SCHEMAS.get(db_name, '')

            service = SQLiteService(db_file, schema_sql)
            service.start()

            self.db_services[db_name] = service

            logger.info(f"  {db_name}.db initialized: {db_file}")

        # PostgreSQL (optional)
        if self.config['database'].get('postgresql', {}).get('enabled', False):
            pg_config = self.config['database']['postgresql']
            self.postgres_service = PostgresService(pg_config)

            try:
                await self.postgres_service.connect()
                logger.info("  PostgreSQL connected")
            except Exception as e:
                logger.warning(f"  PostgreSQL connection failed: {e}")
                logger.warning("  Continuing with SQLite only")
                self.postgres_service = None

    async def _init_modbus(self):
        """
        Initialize Modbus communication.

        Note: If connection fails, application will continue and retry in background.
        """
        logger.info("Initializing Modbus...")

        modbus_config = self.config['modbus']

        # Create Modbus client
        self.modbus_service = AsyncModbusService(
            host=modbus_config['host'],
            port=modbus_config['port'],
            config=modbus_config
        )

        # Try initial connection
        connected = await self.modbus_service.connect()

        if not connected:
            logger.warning(
                f"  Initial Modbus connection failed: {modbus_config['host']}:{modbus_config['port']}\n"
                f"  Application will continue and retry connection in background..."
            )
            # Don't raise exception - allow application to start anyway
        else:
            logger.info(f"  Modbus connected: {modbus_config['host']}:{modbus_config['port']}")

        # Create reader and writer regardless of connection status
        # They will handle disconnected state internally
        self.modbus_reader = ModbusReader(
            self.modbus_service,
            modbus_config['registers']
        )

        self.modbus_writer = ModbusWriter(
            self.modbus_service,
            modbus_config['registers'],
            self.config['control']['speed_limits']
        )

    async def _init_control_manager(self):
        """
        Initialize control manager.
        """
        logger.info("Initializing control manager...")

        self.control_manager = ControlManager(
            self.config,
            self.modbus_service,
            self.db_services.get('ml')
        )

        mode = self.control_manager.get_current_mode()
        logger.info(f"  Control manager initialized: mode={mode.value}")

    async def _init_mqtt(self):
        """
        Initialize MQTT service (optional).
        """
        if not self.config.get('iot', {}).get('thingsboard', {}).get('enabled', False):
            logger.info("MQTT disabled - skipping")
            return

        logger.info("Initializing MQTT...")

        try:
            self.mqtt_service = MQTTService(self.config)
            await self.mqtt_service.start()

            broker = self.config['iot']['thingsboard']['mqtt']['broker']
            logger.info(f"  MQTT started: {broker}")

        except Exception as e:
            logger.warning(f"  MQTT initialization failed: {e}")
            logger.warning("  Continuing without MQTT")
            self.mqtt_service = None

    async def _init_data_pipeline(self):
        """
        Initialize data processing pipeline.
        """
        logger.info("Initializing data pipeline...")

        self.data_pipeline = DataProcessingPipeline(
            self.config,
            self.modbus_reader,
            self.modbus_writer,
            self.control_manager,
            self.db_services,
            self.mqtt_service
        )

        await self.data_pipeline.start()

        logger.info("  Data pipeline started")

    async def _init_gui(self):
        """
        Initialize GUI application (runs in separate thread).
        """
        if not GUI_AVAILABLE:
            logger.info("Skipping GUI initialization - PySide2 not installed")
            return

        try:
            logger.info("Initializing GUI...")

            # Check if GUI is enabled in config
            gui_config = self.config.get('gui', {})
            if not gui_config.get('enabled', True):
                logger.info("  GUI disabled in configuration")
                return

            # Create GUI app instance
            self.gui_app = GUIApplication(
                self.control_manager,
                self.data_pipeline
            )

            # Start GUI in separate thread (non-daemon so it keeps app alive)
            self.gui_thread = threading.Thread(
                target=self._run_gui_and_shutdown,
                daemon=False,
                name="GUI-Thread"
            )
            self.gui_thread.start()

            logger.info("  GUI started in separate thread")

        except Exception as e:
            logger.warning(f"  GUI initialization failed: {e}")
            logger.warning("  Continuing without GUI")
            self.gui_app = None
            self.gui_thread = None

    def _run_gui_and_shutdown(self):
        """
        Run GUI and shutdown application when GUI closes.
        """
        try:
            # Run GUI (blocking call)
            self.gui_app.run()

            # GUI closed - trigger application shutdown
            logger.info("GUI closed - shutting down application")
            self._shutdown_event.set()

        except Exception as e:
            logger.error(f"Error in GUI thread: {e}")
            self._shutdown_event.set()

    async def _start_background_tasks(self):
        """
        Start background monitoring tasks.
        """
        logger.info("Starting background tasks...")

        # Health monitor
        self._health_monitor_task = asyncio.create_task(
            self._health_monitor_loop()
        )

        logger.info("  Background tasks started")

    async def _health_monitor_loop(self):
        """
        Periodic health monitoring.
        """
        logger.info("Health monitor started")

        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(30.0)  # Every 30 seconds

                # Check Modbus connection
                if self.modbus_service:
                    health = self.modbus_service.get_health()
                    if not health['connected']:
                        logger.warning("Modbus connection lost - attempting reconnect")
                        await self.modbus_service.connect()

                # Check database queue sizes
                for db_name, db_service in self.db_services.items():
                    stats = db_service.get_stats()
                    queue_size = stats.get('queue_size', 0)

                    if queue_size > 5000:
                        logger.warning(
                            f"{db_name}.db queue high: {queue_size} items"
                        )

                # Log statistics
                if self.data_pipeline:
                    stats = self.data_pipeline.get_stats()
                    logger.info(
                        f"Pipeline stats: "
                        f"cycles={stats['cycles']}, "
                        f"errors={stats['errors']}, "
                        f"commands={stats['speed_commands_sent']}"
                    )

            except asyncio.CancelledError:
                logger.info("Health monitor cancelled")
                break

            except Exception as e:
                logger.error(f"Error in health monitor: {e}", exc_info=True)

        logger.info("Health monitor ended")

    def get_status(self) -> dict:
        """
        Get application status.

        Returns:
            Dictionary with status information
        """
        status = {
            'started': self._started,
            'databases': {
                name: service.get_stats()
                for name, service in self.db_services.items()
            }
        }

        if self.modbus_service:
            status['modbus'] = self.modbus_service.get_health()

        if self.control_manager:
            status['control'] = self.control_manager.get_status()

        if self.data_pipeline:
            status['pipeline'] = self.data_pipeline.get_stats()

        if self.mqtt_service:
            status['mqtt'] = self.mqtt_service.get_stats()

        return status

    async def run_forever(self):
        """
        Run application until shutdown is requested.

        This method blocks until:
        - GUI is closed (if GUI is enabled)
        - Signal received (SIGINT/SIGTERM)
        - request_shutdown() is called
        """
        logger.info("Application running - waiting for shutdown signal")
        await self._shutdown_event.wait()
        logger.info("Shutdown signal received")

    def request_shutdown(self):
        """
        Request application shutdown.

        This also closes the GUI if it's running, ensuring that:
        1. Qt objects are cleaned up in the GUI thread
        2. GUI thread finishes before Python exits
        3. No segmentation fault on Linux
        """
        logger.info("Shutdown requested")

        # Close GUI first (if running) - this triggers proper Qt cleanup
        if self.gui_app and self.gui_app._app:
            try:
                # QApplication.quit() is thread-safe
                self.gui_app._app.quit()
                logger.info("GUI quit signal sent")
            except Exception as e:
                logger.warning(f"Failed to quit GUI: {e}")

        self._shutdown_event.set()
