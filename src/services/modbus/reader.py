"""
High-level Modbus data reading service.
Reads all registers and converts to engineering units.
"""

import logging
from datetime import datetime
from typing import Optional
from ...domain.models import RawSensorData
from ...domain.validators import sanitize_signed_register

logger = logging.getLogger(__name__)


class ModbusReader:
    """High-level Modbus sensor data reader."""

    def __init__(self, modbus_client, register_map: dict):
        """
        Initialize reader.

        Args:
            modbus_client: AsyncModbusService instance
            register_map: Register address mapping from config
        """
        self.modbus = modbus_client
        self.regs = register_map

    async def read_all_sensors(self) -> Optional[RawSensorData]:
        """
        Read all sensor data from Modbus.

        Returns:
            RawSensorData instance or None on error
        """
        try:
            # Read register groups in batches for efficiency
            # Group 1: 2000-2099 (Motor, mechanical, environment)
            batch1 = await self.modbus.read_holding_registers(2000, 100)
            if not batch1:
                logger.warning("Failed to read register batch 2000-2099")
                return None

            # Group 2: 2100-2109 (Vibration sensors)
            batch2 = await self.modbus.read_holding_registers(2100, 10)
            if not batch2:
                logger.warning("Failed to read register batch 2100-2109")
                batch2 = [0] * 10  # Use zeros as fallback

            # Combine batches
            registers = {}
            for i, val in enumerate(batch1):
                registers[2000 + i] = val
            for i, val in enumerate(batch2):
                registers[2100 + i] = val

            # Convert to engineering units
            return RawSensorData(
                timestamp=datetime.now(),

                # Motor measurements (scaled by 10)
                serit_motor_akim_a=registers.get(self.regs['SERIT_MOTOR_AKIM'], 0) / 10.0,
                serit_motor_tork_percentage=registers.get(self.regs['SERIT_MOTOR_TORK'], 0) / 10.0,
                inme_motor_akim_a=registers.get(self.regs.get('INME_MOTOR_AKIM', 2012), 0) / 10.0,
                inme_motor_tork_percentage=registers.get(self.regs.get('INME_MOTOR_TORK', 2013), 0) / 10.0,

                # Speed values
                serit_kesme_hizi=registers.get(self.regs['KESME_HIZI'], 0) / 10.0,
                serit_inme_hizi=self._decode_inme_hizi(
                    registers.get(self.regs['INME_HIZI'], 0)
                ),

                # Mechanical measurements
                kafa_yuksekligi_mm=registers.get(self.regs['KAFA_YUKSEKLIK'], 0) / 10.0,
                serit_sapmasi=sanitize_signed_register(
                    registers.get(self.regs['SERIT_SAPMASI'], 0)
                ) / 100.0,  # Signed, scaled by 100
                serit_gerginligi_bar=registers.get(self.regs['SERIT_GERGINLIGI'], 0) / 10.0,
                mengene_basinc_bar=registers.get(self.regs.get('MENGENE_BASINC', 2022), 0) / 10.0,

                # Environmental measurements
                ortam_sicakligi_c=registers.get(self.regs.get('ORTAM_SICAKLIK', 2040), 0) / 10.0,
                ortam_nem_percentage=registers.get(self.regs.get('ORTAM_NEM', 2042), 0) / 10.0,
                sogutma_sivi_sicakligi_c=registers.get(self.regs.get('SOGUTMA_SIVI_SICAKLIK', 2050), 0) / 10.0,
                hidrolik_yag_sicakligi_c=registers.get(self.regs.get('HIDROLIK_YAG_SICAKLIK', 2051), 0) / 10.0,

                # Vibration measurements
                ivme_olcer_x=registers.get(self.regs.get('IVME_X', 2100), 0) / 10.0,
                ivme_olcer_y=registers.get(self.regs.get('IVME_Y', 2101), 0) / 10.0,
                ivme_olcer_z=registers.get(self.regs.get('IVME_Z', 2102), 0) / 10.0,
                ivme_olcer_x_hz=registers.get(self.regs.get('IVME_X_HZ', 2103), 0) / 10.0,
                ivme_olcer_y_hz=registers.get(self.regs.get('IVME_Y_HZ', 2104), 0) / 10.0,
                ivme_olcer_z_hz=registers.get(self.regs.get('IVME_Z_HZ', 2105), 0) / 10.0,
                max_titresim_hz=registers.get(self.regs.get('MAX_TITRESIM_HZ', 2106), 0) / 10.0,

                # State information
                testere_durumu=registers.get(self.regs['TESTERE_DURUMU'], 0),
                alarm_status=registers.get(self.regs.get('ALARM_STATUS', 2031), 0),
                alarm_bilgisi=f"0x{registers.get(self.regs.get('ALARM_BILGISI', 2032), 0):04X}",

                # Identification
                makine_id=registers.get(self.regs.get('MAKINE_ID', 2251), 1),
                serit_id=registers.get(self.regs.get('SERIT_ID', 2230), 1),

                # Statistics
                kesilen_parca_adeti=registers.get(self.regs.get('KESILEN_PARCA_ADETI', 2250), 0)
            )

        except Exception as e:
            # Log without traceback to keep logs clean
            logger.debug(f"Error reading sensors: {e}")
            return None

    def _decode_inme_hizi(self, raw_value: int) -> float:
        """
        Decode descent speed (signed, scaled by 100).

        Args:
            raw_value: Raw register value

        Returns:
            Descent speed in mm/min
        """
        signed_value = sanitize_signed_register(raw_value)
        return signed_value / 100.0
