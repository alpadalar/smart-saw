"""
Main data processing pipeline - orchestrates entire data flow.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Optional

from ...domain.models import ProcessedData
from .cutting_tracker import CuttingTracker
from ...anomaly.manager import AnomalyManager

logger = logging.getLogger(__name__)


class DataProcessingPipeline:
    """
    Main data orchestration loop.

    Flow:
    1. Read from Modbus (ModbusReader)
    2. Create RawSensorData
    3. Process into ProcessedData (anomaly detection, session tracking)
    4. Pass to ControlManager
    5. Write speeds to Modbus (if command returned)
    6. Save to databases (raw, total, ml)
    7. Queue for MQTT (batching)

    Features:
    - Async processing loop (10 Hz target)
    - Error recovery (continues on errors)
    - Health monitoring
    - Statistics tracking
    """

    def __init__(
        self,
        config: dict,
        modbus_reader,
        modbus_writer,
        control_manager,
        db_services: dict,
        mqtt_service=None
    ):
        """
        Initialize data processing pipeline.

        Args:
            config: System configuration
            modbus_reader: ModbusReader instance
            modbus_writer: ModbusWriter instance
            control_manager: ControlManager instance
            db_services: Dictionary of SQLiteService instances
                {'raw': raw_db, 'total': total_db, 'log': log_db}
            mqtt_service: MQTTService instance (optional)
        """
        self.config = config
        self.modbus_reader = modbus_reader
        self.modbus_writer = modbus_writer
        self.control_manager = control_manager
        self.db_services = db_services
        self.mqtt_service = mqtt_service

        # Processing components
        self.cutting_tracker = CuttingTracker(db_services.get('total'))

        # Advanced anomaly detection with multiple methods
        anomaly_config = config.get('anomaly_detection', {})
        self.anomaly_manager = AnomalyManager(
            buffer_size=anomaly_config.get('window', 100),
            min_samples=anomaly_config.get('min_samples', 10)
        )

        # Processing loop control
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Target processing rate
        self.target_interval = 1.0 / config.get('processing', {}).get('rate_hz', 10)

        # Statistics
        self._stats = {
            'cycles': 0,
            'errors': 0,
            'speed_commands_sent': 0,
            'db_writes': 0,
            'mqtt_queued': 0
        }

        # Latest data for GUI
        self._last_processed_data = None

        # Store last processed data for GUI access
        self._last_processed_data: Optional[ProcessedData] = None

        logger.info(
            f"DataProcessingPipeline initialized: "
            f"target_rate={1.0/self.target_interval:.1f}Hz"
        )

    async def start(self):
        """
        Start the processing pipeline.
        """
        if self._running:
            logger.warning("Pipeline already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._processing_loop())

        logger.info("Data processing pipeline started")

    async def stop(self, timeout: float = 5.0):
        """
        Stop the processing pipeline.

        Args:
            timeout: Maximum time to wait for graceful shutdown
        """
        if not self._running:
            return

        self._running = False

        # Wait for task to complete
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("Pipeline stop timeout - cancelling task")
                self._task.cancel()

        logger.info("Data processing pipeline stopped")

    async def _processing_loop(self):
        """
        Main processing loop.

        Runs continuously at target rate (default 10 Hz).
        """
        logger.info("Processing loop started")

        while self._running:
            cycle_start = asyncio.get_event_loop().time()

            try:
                # 1. Read from Modbus
                raw_data = await self.modbus_reader.read_all_sensors()
                if raw_data is None:
                    # Modbus read failed (PLC disconnected or error)
                    self._stats['errors'] += 1

                    # Log only every 10 errors to avoid spam
                    if self._stats['errors'] % 10 == 1:
                        logger.warning(
                            f"Modbus read failed (total errors: {self._stats['errors']}). "
                            "Waiting for PLC connection..."
                        )

                    await asyncio.sleep(self.target_interval)
                    continue

                # 2. Process raw data
                processed_data = self._process_raw_data(raw_data)

                # Store for GUI access
                self._last_processed_data = processed_data

                # 3. Control logic (ML or Manual)
                command = await self.control_manager.process_data(processed_data)

                # 4. Write speeds to Modbus
                if command:
                    success = await self.modbus_writer.write_speeds(
                        command.kesme_hizi_target,
                        command.inme_hizi_target
                    )

                    if success:
                        self._stats['speed_commands_sent'] += 1
                        logger.debug(
                            f"Speeds written: "
                            f"kesme={command.kesme_hizi_target:.1f}, "
                            f"inme={command.inme_hizi_target:.1f}"
                        )
                    else:
                        logger.error("Failed to write speeds to Modbus")

                # 5. Save to databases
                self._save_to_databases(raw_data, processed_data, command)

                # 6. Queue for MQTT
                if self.mqtt_service:
                    await self.mqtt_service.queue_telemetry(processed_data)
                    self._stats['mqtt_queued'] += 1

                # Update statistics
                self._stats['cycles'] += 1

                # Rate limiting
                cycle_duration = asyncio.get_event_loop().time() - cycle_start
                sleep_time = max(0, self.target_interval - cycle_duration)

                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    logger.warning(
                        f"Processing cycle exceeded target interval: "
                        f"{cycle_duration*1000:.1f}ms > {self.target_interval*1000:.1f}ms"
                    )

            except asyncio.CancelledError:
                logger.info("Processing loop cancelled")
                break

            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                self._stats['errors'] += 1
                await asyncio.sleep(self.target_interval)

        logger.info("Processing loop ended")

    def _process_raw_data(self, raw_data) -> ProcessedData:
        """
        Process raw sensor data into ProcessedData.

        Args:
            raw_data: RawSensorData from Modbus

        Returns:
            ProcessedData with anomalies and session info
        """
        # Get current control mode
        current_mode = self.control_manager.get_current_mode()

        # Update cutting tracker
        session_id = self.cutting_tracker.update(
            raw_data.testere_durumu,
            current_mode.value
        )

        is_cutting = (raw_data.testere_durumu == 3)

        # Detect anomalies using advanced manager
        # Convert raw_data to dict for manager
        raw_data_dict = {
            'serit_sapmasi': raw_data.serit_sapmasi,
            'serit_motor_akim_a': raw_data.serit_motor_akim_a,
            'serit_motor_tork_percentage': raw_data.serit_motor_tork_percentage,
            'serit_kesme_hizi': raw_data.serit_kesme_hizi,
            'serit_inme_hizi': raw_data.serit_inme_hizi,
            'ivme_olcer_x_hz': raw_data.ivme_olcer_x_hz,
            'ivme_olcer_y_hz': raw_data.ivme_olcer_y_hz,
            'ivme_olcer_z_hz': raw_data.ivme_olcer_z_hz,
            'serit_gerginligi_bar': raw_data.serit_gerginligi_bar,
        }
        anomaly_results = self.anomaly_manager.process_data(raw_data_dict, is_cutting)

        # Convert anomaly results to list format for ProcessedData
        anomalies = [
            {'sensor': key, 'type': 'anomaly_detected'}
            for key, is_anomaly in anomaly_results.items()
            if is_anomaly
        ]

        # Create ProcessedData
        processed_data = ProcessedData(
            timestamp=datetime.now(),
            raw_data=raw_data,
            ml_output=None,  # Will be filled by ML controller if used
            kesme_hizi_degisim=None,
            inme_hizi_degisim=None,
            torque_guard_active=False,
            cutting_session_id=session_id,
            anomalies=anomalies,
            is_cutting=is_cutting,
            controller_type=current_mode.value
        )

        return processed_data

    def _save_to_databases(self, raw_data, processed_data, command):
        """
        Save data to SQLite databases (non-blocking).

        Args:
            raw_data: RawSensorData
            processed_data: ProcessedData
            command: ControlCommand (or None)
        """
        try:
            # Save to raw.db
            if 'raw' in self.db_services:
                self._save_raw_data(raw_data)

            # Save to total.db
            if 'total' in self.db_services:
                self._save_processed_data(processed_data, command)

            self._stats['db_writes'] += 1

        except Exception as e:
            logger.error(f"Error saving to databases: {e}", exc_info=True)

    def _save_raw_data(self, raw_data):
        """
        Save raw sensor data to raw.db.

        Args:
            raw_data: RawSensorData
        """
        sql = """
            INSERT INTO sensor_data (
                timestamp,
                serit_motor_akim_a,
                serit_motor_tork_percentage,
                inme_motor_akim_a,
                inme_motor_tork_percentage,
                serit_kesme_hizi,
                serit_inme_hizi,
                kafa_yuksekligi_mm,
                serit_sapmasi,
                serit_gerginligi_bar,
                mengene_basinc_bar,
                ortam_sicakligi_c,
                ortam_nem_percentage,
                sogutma_sivi_sicakligi_c,
                hidrolik_yag_sicakligi_c,
                ivme_olcer_x,
                ivme_olcer_y,
                ivme_olcer_z,
                ivme_olcer_x_hz,
                ivme_olcer_y_hz,
                ivme_olcer_z_hz,
                max_titresim_hz,
                testere_durumu,
                alarm_status,
                alarm_bilgisi,
                makine_id,
                serit_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            raw_data.timestamp.isoformat(),
            raw_data.serit_motor_akim_a,
            raw_data.serit_motor_tork_percentage,
            raw_data.inme_motor_akim_a,
            raw_data.inme_motor_tork_percentage,
            raw_data.serit_kesme_hizi,
            raw_data.serit_inme_hizi,
            raw_data.kafa_yuksekligi_mm,
            raw_data.serit_sapmasi,
            raw_data.serit_gerginligi_bar,
            raw_data.mengene_basinc_bar,
            raw_data.ortam_sicakligi_c,
            raw_data.ortam_nem_percentage,
            raw_data.sogutma_sivi_sicakligi_c,
            raw_data.hidrolik_yag_sicakligi_c,
            raw_data.ivme_olcer_x,
            raw_data.ivme_olcer_y,
            raw_data.ivme_olcer_z,
            raw_data.ivme_olcer_x_hz,
            raw_data.ivme_olcer_y_hz,
            raw_data.ivme_olcer_z_hz,
            raw_data.max_titresim_hz,
            raw_data.testere_durumu,
            raw_data.alarm_status,
            raw_data.alarm_bilgisi,
            raw_data.makine_id,
            raw_data.serit_id
        )

        self.db_services['raw'].write_async(sql, params)

    def _save_processed_data(self, processed_data, command):
        """
        Save processed data to total.db.

        Args:
            processed_data: ProcessedData
            command: ControlCommand (or None)
        """
        sql = """
            INSERT INTO processed_data (
                timestamp,
                ml_output,
                kesme_hizi_degisim,
                inme_hizi_degisim,
                torque_guard_active,
                cutting_session_id,
                anomalies,
                controller_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            processed_data.timestamp.isoformat(),
            processed_data.ml_output,
            command.kesme_hizi_target if command else None,
            command.inme_hizi_target if command else None,
            int(processed_data.torque_guard_active),
            processed_data.cutting_session_id,
            json.dumps(processed_data.anomalies) if processed_data.anomalies else None,
            processed_data.controller_type
        )

        self.db_services['total'].write_async(sql, params)

    def get_stats(self) -> dict:
        """
        Get pipeline statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            **self._stats,
            'is_running': self._running,
            'cutting_tracker': self.cutting_tracker.get_stats(),
            'anomaly_manager': self.anomaly_manager.get_stats(),
            'control_manager': self.control_manager.get_status()
        }
