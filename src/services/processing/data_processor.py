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
from .anomaly_tracker import AnomalyTracker
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

        # Anomaly tracker for persistence and reset functionality
        self.anomaly_tracker = AnomalyTracker(db_services.get('anomaly'))

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

        # Update cutting tracker (with height for session tracking)
        kesim_id = self.cutting_tracker.update(
            raw_data.testere_durumu,
            current_mode.value,
            raw_data.kafa_yuksekligi_mm
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

        # Mapping from GUI keys to data keys (for sensor value lookup)
        gui_to_data_key = {
            'SeritSapmasi': 'serit_sapmasi',
            'SeritAkim': 'serit_motor_akim_a',
            'SeritTork': 'serit_motor_tork_percentage',
            'KesmeHizi': 'serit_kesme_hizi',
            'IlerlemeHizi': 'serit_inme_hizi',
            'TitresimX': 'ivme_olcer_x_hz',
            'TitresimY': 'ivme_olcer_y_hz',
            'TitresimZ': 'ivme_olcer_z_hz',
            'SeritGerginligi': 'serit_gerginligi_bar',
        }

        # Record anomalies to tracker (for persistence and GUI display)
        for sensor_name, is_anomaly in anomaly_results.items():
            if is_anomaly:
                # Get correct data key for sensor value lookup
                data_key = gui_to_data_key.get(sensor_name)
                sensor_value = raw_data_dict.get(data_key, 0.0) if data_key else 0.0
                self.anomaly_tracker.record_anomaly(
                    sensor_name=sensor_name,
                    sensor_value=sensor_value,
                    detection_method=self.anomaly_manager.get_method_for_sensor(sensor_name),
                    kesim_id=kesim_id,
                    kafa_yuksekligi=raw_data.kafa_yuksekligi_mm
                )

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
            cutting_session_id=kesim_id,  # Now integer kesim_id
            anomalies=anomalies,
            is_cutting=is_cutting,
            controller_type=current_mode.value
        )
        # # Log every item in processed data human readably
        # logger.info(f"ProcessedData: {processed_data}")
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
        Save raw Modbus register values to raw.db (unprocessed).

        Args:
            raw_data: RawSensorData (we use modbus_reader to get raw registers)
        """
        # Get raw registers from modbus reader
        raw_registers = self.modbus_reader.get_last_raw_registers()

        if not raw_registers or len(raw_registers) < 44:
            logger.warning("No raw registers available for database save")
            return

        sql = """
            INSERT INTO raw_registers (
                timestamp,
                reg_1000_makine_id,
                reg_1001_serit_id,
                reg_1002_serit_dis_mm,
                reg_1003_serit_tip,
                reg_1004_serit_marka,
                reg_1005_serit_malz,
                reg_1006_malzeme_cinsi,
                reg_1007_malzeme_sertlik,
                reg_1008_kesit_yapisi,
                reg_1009_a_mm,
                reg_1010_b_mm,
                reg_1011_c_mm,
                reg_1012_d_mm,
                reg_1013_kafa_yuksekligi,
                reg_1014_kesilen_parca_adeti,
                reg_1015_serit_motor_akim,
                reg_1016_serit_motor_tork,
                reg_1017_inme_motor_akim,
                reg_1018_inme_motor_tork,
                reg_1019_mengene_basinc,
                reg_1020_serit_gerginligi,
                reg_1021_ivme_olcer_x,
                reg_1022_ivme_olcer_y,
                reg_1023_ivme_olcer_z,
                reg_1024_serit_sapmasi,
                reg_1025_ortam_sicakligi,
                reg_1026_ortam_nem,
                reg_1027_sogutma_sivi_sicakligi,
                reg_1028_hidrolik_yag_sicakligi,
                reg_1029_serit_sicakligi,
                reg_1030_testere_durumu,
                reg_1031_alarm_status,
                reg_1032_alarm_bilgisi,
                reg_1033_serit_kesme_hizi,
                reg_1034_serit_inme_hizi,
                reg_1035_ivme_olcer_x_hz,
                reg_1036_ivme_olcer_y_hz,
                reg_1037_ivme_olcer_z_hz,
                reg_1038_fark_hz_x,
                reg_1039_fark_hz_y,
                reg_1040_fark_hz_z,
                reg_1041_malzeme_genisligi,
                reg_1042_guc_1,
                reg_1043_guc_2
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            raw_data.timestamp.isoformat(),
            raw_registers[0],   # 1000 - makine_id
            raw_registers[1],   # 1001 - serit_id
            raw_registers[2],   # 1002 - serit_dis_mm
            raw_registers[3],   # 1003 - serit_tip
            raw_registers[4],   # 1004 - serit_marka
            raw_registers[5],   # 1005 - serit_malz
            raw_registers[6],   # 1006 - malzeme_cinsi
            raw_registers[7],   # 1007 - malzeme_sertlik
            raw_registers[8],   # 1008 - kesit_yapisi
            raw_registers[9],   # 1009 - a_mm
            raw_registers[10],  # 1010 - b_mm
            raw_registers[11],  # 1011 - c_mm
            raw_registers[12],  # 1012 - d_mm
            raw_registers[13],  # 1013 - kafa_yuksekligi
            raw_registers[14],  # 1014 - kesilen_parca_adeti
            raw_registers[15],  # 1015 - serit_motor_akim
            raw_registers[16],  # 1016 - serit_motor_tork
            raw_registers[17],  # 1017 - inme_motor_akim
            raw_registers[18],  # 1018 - inme_motor_tork
            raw_registers[19],  # 1019 - mengene_basinc
            raw_registers[20],  # 1020 - serit_gerginligi
            raw_registers[21],  # 1021 - ivme_olcer_x
            raw_registers[22],  # 1022 - ivme_olcer_y
            raw_registers[23],  # 1023 - ivme_olcer_z
            raw_registers[24],  # 1024 - serit_sapmasi
            raw_registers[25],  # 1025 - ortam_sicakligi
            raw_registers[26],  # 1026 - ortam_nem
            raw_registers[27],  # 1027 - sogutma_sivi_sicakligi
            raw_registers[28],  # 1028 - hidrolik_yag_sicakligi
            raw_registers[29],  # 1029 - serit_sicakligi
            raw_registers[30],  # 1030 - testere_durumu
            raw_registers[31],  # 1031 - alarm_status
            raw_registers[32],  # 1032 - alarm_bilgisi
            raw_registers[33],  # 1033 - serit_kesme_hizi
            raw_registers[34],  # 1034 - serit_inme_hizi
            raw_registers[35],  # 1035 - ivme_olcer_x_hz
            raw_registers[36],  # 1036 - ivme_olcer_y_hz
            raw_registers[37],  # 1037 - ivme_olcer_z_hz
            raw_registers[38],  # 1038 - fark_hz_x
            raw_registers[39],  # 1039 - fark_hz_y
            raw_registers[40],  # 1040 - fark_hz_z
            raw_registers[41],  # 1041 - malzeme_genisligi
            raw_registers[42],  # 1042 - guc_1
            raw_registers[43],  # 1043 - guc_2
        )

        self.db_services['raw'].write_async(sql, params)

    def _save_processed_data(self, processed_data, command):
        """
        Save processed sensor data to total.db.

        Args:
            processed_data: ProcessedData
            command: ControlCommand (or None)
        """
        raw = processed_data.raw_data

        sql = """
            INSERT INTO sensor_data (
                timestamp,
                kesim_id,
                serit_motor_akim_a,
                serit_motor_tork_percentage,
                inme_motor_akim_a,
                inme_motor_tork_percentage,
                serit_kesme_hizi,
                serit_inme_hizi,
                kesme_hizi_hedef,
                inme_hizi_hedef,
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
                serit_id,
                malzeme_cinsi,
                malzeme_sertlik,
                kesit_yapisi,
                malzeme_a_mm,
                malzeme_b_mm,
                malzeme_c_mm,
                malzeme_d_mm,
                malzeme_genisligi,
                serit_tip,
                serit_marka,
                serit_malz,
                serit_dis_mm,
                kesilen_parca_adeti,
                guc_kwh,
                ml_output,
                kesme_hizi_degisim,
                inme_hizi_degisim,
                torque_guard_active,
                controller_type,
                anomalies
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            processed_data.timestamp.isoformat(),
            processed_data.cutting_session_id,  # kesim_id (int or None)
            raw.serit_motor_akim_a,
            raw.serit_motor_tork_percentage,
            raw.inme_motor_akim_a,
            raw.inme_motor_tork_percentage,
            raw.serit_kesme_hizi,
            raw.serit_inme_hizi,
            raw.kesme_hizi_hedef,
            raw.inme_hizi_hedef,
            raw.kafa_yuksekligi_mm,
            raw.serit_sapmasi,
            raw.serit_gerginligi_bar,
            raw.mengene_basinc_bar,
            raw.ortam_sicakligi_c,
            raw.ortam_nem_percentage,
            raw.sogutma_sivi_sicakligi_c,
            raw.hidrolik_yag_sicakligi_c,
            raw.ivme_olcer_x,
            raw.ivme_olcer_y,
            raw.ivme_olcer_z,
            raw.ivme_olcer_x_hz,
            raw.ivme_olcer_y_hz,
            raw.ivme_olcer_z_hz,
            raw.max_titresim_hz,
            raw.testere_durumu,
            raw.alarm_status,
            raw.alarm_bilgisi,
            raw.makine_id,
            raw.serit_id,
            raw.malzeme_cinsi,
            raw.malzeme_sertlik,
            raw.kesit_yapisi,
            raw.malzeme_a_mm,
            raw.malzeme_b_mm,
            raw.malzeme_c_mm,
            raw.malzeme_d_mm,
            raw.malzeme_genisligi,
            raw.serit_tip,
            raw.serit_marka,
            raw.serit_malz,
            raw.serit_dis_mm,
            raw.kesilen_parca_adeti,
            raw.guc_kwh,
            processed_data.ml_output,
            command.kesme_hizi_target if command else None,
            command.inme_hizi_target if command else None,
            int(processed_data.torque_guard_active),
            processed_data.controller_type,
            json.dumps(processed_data.anomalies) if processed_data.anomalies else None
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

    def get_latest_data(self) -> dict:
        """
        Get latest processed data for GUI display.

        Returns:
            Dictionary with sensor data and connection status.
            Returns default values with modbus_connected=False if no data available.

        Note:
            Unlike to_dict() which returns nested structure, this method
            flattens raw_data fields for direct GUI access.
        """
        modbus_ip = self.config.get('modbus', {}).get('host', '192.168.1.100')

        # If we have recent processed data, connection is working
        # Check data freshness (within last 2 seconds)
        if self._last_processed_data is not None:
            data_age = (datetime.now() - self._last_processed_data.timestamp).total_seconds()
            # If data is fresh (less than 2 seconds old), connection is active
            modbus_connected = data_age < 2.0
        else:
            modbus_connected = False

        # If we have processed data, flatten it for GUI
        if self._last_processed_data is not None:
            pd = self._last_processed_data
            raw = pd.raw_data

            # Flatten raw_data fields directly into result dict
            data = {
                # Connection status
                'modbus_connected': modbus_connected,
                'modbus_ip': modbus_ip,

                # Timestamp
                'timestamp': pd.timestamp.isoformat(),

                # Motor measurements (from raw_data)
                'serit_motor_akim_a': raw.serit_motor_akim_a,
                'serit_motor_tork_percentage': raw.serit_motor_tork_percentage,
                'inme_motor_akim_a': raw.inme_motor_akim_a,
                'inme_motor_tork_percentage': raw.inme_motor_tork_percentage,

                # Speed values (actual - from registers 1033/1034)
                'serit_kesme_hizi': raw.serit_kesme_hizi,
                'serit_inme_hizi': raw.serit_inme_hizi,

                # Target speed values (from registers 2066/2041 - what we write to PLC)
                'kesme_hizi_hedef': raw.kesme_hizi_hedef,
                'inme_hizi_hedef': raw.inme_hizi_hedef,

                # Mechanical measurements
                'kafa_yuksekligi_mm': raw.kafa_yuksekligi_mm,
                'serit_sapmasi': raw.serit_sapmasi,
                'serit_gerginligi_bar': raw.serit_gerginligi_bar,
                'mengene_basinc_bar': raw.mengene_basinc_bar,

                # Environmental measurements
                'ortam_sicakligi_c': raw.ortam_sicakligi_c,
                'ortam_nem_percentage': raw.ortam_nem_percentage,
                'sogutma_sivi_sicakligi_c': raw.sogutma_sivi_sicakligi_c,
                'hidrolik_yag_sicakligi_c': raw.hidrolik_yag_sicakligi_c,

                # Vibration measurements
                'ivme_olcer_x': raw.ivme_olcer_x,
                'ivme_olcer_y': raw.ivme_olcer_y,
                'ivme_olcer_z': raw.ivme_olcer_z,
                'ivme_olcer_x_hz': raw.ivme_olcer_x_hz,
                'ivme_olcer_y_hz': raw.ivme_olcer_y_hz,
                'ivme_olcer_z_hz': raw.ivme_olcer_z_hz,
                'max_titresim_hz': raw.max_titresim_hz,

                # State information
                'testere_durumu': raw.testere_durumu,
                'alarm_status': raw.alarm_status,
                'alarm_bilgisi': raw.alarm_bilgisi,

                # Identification
                'makine_id': raw.makine_id,
                'serit_id': raw.serit_id,

                # Material information
                'malzeme_cinsi': raw.malzeme_cinsi,
                'malzeme_sertlik': raw.malzeme_sertlik,
                'kesit_yapisi': raw.kesit_yapisi,
                'malzeme_a_mm': raw.malzeme_a_mm,
                'malzeme_b_mm': raw.malzeme_b_mm,
                'malzeme_c_mm': raw.malzeme_c_mm,
                'malzeme_d_mm': raw.malzeme_d_mm,
                'malzeme_genisligi': raw.malzeme_genisligi,

                # Band information
                'serit_tip': raw.serit_tip,
                'serit_marka': raw.serit_marka,
                'serit_malz': raw.serit_malz,
                'serit_dis_mm': raw.serit_dis_mm,

                # Statistics
                'kesilen_parca_adeti': raw.kesilen_parca_adeti,

                # Power measurement
                'guc_kwh': raw.guc_kwh,

                # ML control outputs (from ProcessedData)
                'ml_output': pd.ml_output,
                'kesme_hizi_degisim': pd.kesme_hizi_degisim,
                'inme_hizi_degisim': pd.inme_hizi_degisim,
                'torque_guard_active': pd.torque_guard_active,

                # Anomaly detection
                'anomalies': pd.anomalies,

                # Cutting session tracking
                'is_cutting': pd.is_cutting,
                'cutting_session_id': pd.cutting_session_id,
                'controller_type': pd.controller_type,
            }
            return data

        # No data available - return defaults with connection status
        return {
            'modbus_connected': modbus_connected,
            'modbus_ip': modbus_ip,
            'testere_durumu': -1,  # Special value for "waiting for connection"
            'kafa_yuksekligi_mm': 0,
            'serit_motor_akim_a': 0,
            'inme_motor_akim_a': 0,
            'serit_motor_tork_percentage': 0,
            'inme_motor_tork_percentage': 0,
            'serit_sapmasi': 0,
            'serit_kesme_hizi': 0,
            'serit_inme_hizi': 0,
            'kesme_hizi_hedef': 0,
            'inme_hizi_hedef': 0,
            'serit_gerginligi_bar': 0,
            'mengene_basinc_bar': 0,
            'ortam_sicakligi_c': 0,
            'ortam_nem_percentage': 0,
            'ivme_olcer_x': 0,
            'ivme_olcer_y': 0,
            'ivme_olcer_z': 0,
            'ivme_olcer_x_hz': 0,
            'ivme_olcer_y_hz': 0,
            'ivme_olcer_z_hz': 0,
            'max_titresim_hz': 0,
            'guc_kwh': 0,
        }
