"""
High-level Modbus data reading service.
Reads all registers and converts to engineering units.

Register mapping based on old project:
- Start address: 1000
- Read count: 44 registers

Register order (from old project modbus/client.py):
  1000: makine_id
  1001: serit_id
  1002: serit_dis_mm
  1003: serit_tip
  1004: serit_marka
  1005: serit_malz
  1006: malzeme_cinsi
  1007: malzeme_sertlik
  1008: kesit_yapisi
  1009: a_mm
  1010: b_mm
  1011: c_mm
  1012: d_mm
  1013: kafa_yuksekligi_mm (raw, /10)
  1014: kesilen_parca_adeti
  1015: serit_motor_akim_a (raw, /10)
  1016: serit_motor_tork_percentage (raw, /10)
  1017: inme_motor_akim_a (raw, /100)
  1018: inme_motor_tork_percentage
  1019: mengene_basinc_bar (raw, /10)
  1020: serit_gerginligi_bar (raw, /10)
  1021: ivme_olcer_x
  1022: ivme_olcer_y
  1023: ivme_olcer_z
  1024: serit_sapmasi (raw, /100, signed)
  1025: ortam_sicakligi_c (raw, /10)
  1026: ortam_nem_percentage (raw, /10)
  1027: sogutma_sivi_sicakligi_c (raw, /10)
  1028: hidrolik_yag_sicakligi_c (raw, /10)
  1029: serit_sicakligi_c
  1030: testere_durumu
  1031: alarm_status
  1032: alarm_bilgisi
  1033: serit_kesme_hizi (raw, /10)
  1034: serit_inme_hizi (special handling)
  1035: ivme_olcer_x_hz
  1036: ivme_olcer_y_hz
  1037: ivme_olcer_z_hz
  1038: fark_hz_x (raw, /100)
  1039: fark_hz_y (raw, /100)
  1040: fark_hz_z (raw, /100)
  1041: malzeme_genisligi (raw, /10)
  1042: guc
  1043: guc2
"""

import logging
import struct
from datetime import datetime
from typing import Optional
from ...domain.models import RawSensorData
from ...domain.validators import sanitize_signed_register

logger = logging.getLogger(__name__)


class ModbusReader:
    """High-level Modbus sensor data reader."""

    # Register start address and count (from old project)
    START_ADDRESS = 1000
    REGISTER_COUNT = 44

    # Target speed register addresses (these are what we write to PLC)
    # Also need to read them back to show in GUI
    KESME_HIZI_TARGET_ADDRESS = 2066
    INME_HIZI_TARGET_ADDRESS = 2041

    def __init__(self, modbus_client, register_map: dict):
        """
        Initialize reader.

        Args:
            modbus_client: AsyncModbusService instance
            register_map: Register address mapping from config (not used anymore, kept for compatibility)
        """
        self.modbus = modbus_client
        self.client = modbus_client  # Alias for GUI connection checking
        self.regs = register_map

        # Store last raw registers for database saving
        self._last_raw_registers: list = []

    async def read_all_sensors(self) -> Optional[RawSensorData]:
        """
        Read all sensor data from Modbus.

        Based on old project: reads 44 registers starting from address 1000.
        Also reads target speed registers (2066, 2041) separately.

        Returns:
            RawSensorData instance or None on error
        """
        try:
            # Read all 44 registers in a single batch (like old project)
            registers = await self.modbus.read_holding_registers(
                self.START_ADDRESS,
                self.REGISTER_COUNT
            )

            if not registers:
                logger.warning("Failed to read Modbus registers")
                return None

            # Store raw registers for database saving
            self._last_raw_registers = list(registers)

            # Read target speed registers separately (2066 and 2041)
            # These are the speeds we write to PLC, shown as "hedef" (target) in GUI
            kesme_hizi_hedef = 0.0
            inme_hizi_hedef = 0.0

            try:
                # Read cutting speed target (2066) - no scaling needed per speed_reader.py
                kesme_target_regs = await self.modbus.read_holding_registers(
                    self.KESME_HIZI_TARGET_ADDRESS, 1
                )
                if kesme_target_regs:
                    kesme_hizi_hedef = float(kesme_target_regs[0])

                # Read descent speed target (2041) - scale by /100 per speed_reader.py
                inme_target_regs = await self.modbus.read_holding_registers(
                    self.INME_HIZI_TARGET_ADDRESS, 1
                )
                if inme_target_regs:
                    inme_hizi_hedef = float(inme_target_regs[0]) / 100.0
            except Exception as e:
                logger.debug(f"Failed to read target speed registers: {e}")

            # Map register indices to values (0-indexed, register 1000 = index 0)
            # Apply scaling factors from old project's data/processor.py

            # Raw values (no scaling needed for these)
            makine_id = registers[0]          # 1000
            serit_id = registers[1]           # 1001
            serit_dis_mm = registers[2]       # 1002
            serit_tip = str(registers[3])     # 1003
            serit_marka = str(registers[4])   # 1004
            serit_malz = str(registers[5])    # 1005
            malzeme_cinsi = str(registers[6])  # 1006
            malzeme_sertlik = str(registers[7])  # 1007
            kesit_yapisi = str(registers[8])  # 1008
            # Material dimensions: /10 scaling (PLC stores mm * 10)
            a_mm = registers[9] / 10.0        # 1009
            b_mm = registers[10] / 10.0       # 1010
            c_mm = registers[11] / 10.0       # 1011
            d_mm = registers[12] / 10.0       # 1012
            kesilen_parca_adeti = registers[14]  # 1014
            testere_durumu = registers[30]    # 1030
            alarm_status = registers[31]      # 1031
            alarm_bilgisi_raw = registers[32]  # 1032

            # 1/10 scaled values
            kafa_yuksekligi_mm = registers[13] / 10.0      # 1013
            serit_motor_akim_a = registers[15] / 10.0      # 1015
            serit_motor_tork = registers[16] / 10.0        # 1016
            mengene_basinc_bar = registers[19] / 10.0      # 1019
            serit_gerginligi_bar = registers[20] / 10.0    # 1020
            ortam_sicakligi_c = registers[25] / 10.0       # 1025
            ortam_nem_percentage = registers[26] / 10.0    # 1026
            sogutma_sivi_sicakligi_c = registers[27] / 10.0  # 1027
            hidrolik_yag_sicakligi_c = registers[28] / 10.0  # 1028
            serit_kesme_hizi = registers[33] / 10.0        # 1033
            malzeme_genisligi = registers[41] / 10.0       # 1041

            # 1/100 scaled values
            inme_motor_akim_raw = registers[17] / 100.0    # 1017
            serit_sapmasi_raw = registers[24] / 100.0      # 1024

            # Special handling for inme_motor_akim (from old processor.py)
            # if value > 15, it's a negative value: 655.35 - value
            if inme_motor_akim_raw > 15:
                inme_motor_akim_a = 655.35 - inme_motor_akim_raw
            else:
                inme_motor_akim_a = inme_motor_akim_raw

            # Special handling for serit_sapmasi (signed 16-bit conversion)
            # if value > 1.5, it's negative: value - 655.35
            if serit_sapmasi_raw > 1.5:
                serit_sapmasi = serit_sapmasi_raw - 655.35
            else:
                serit_sapmasi = serit_sapmasi_raw

            # Descent speed special handling (from old processor.py)
            inme_hizi_raw = registers[34]  # 1034
            if inme_hizi_raw == 0:
                serit_inme_hizi = 0.0
            elif inme_hizi_raw > 500:
                serit_inme_hizi = float(inme_hizi_raw - 65536)
            else:
                serit_inme_hizi = float(inme_hizi_raw)

            # Vibration values (no scaling in old processor)
            ivme_olcer_x = float(registers[21])   # 1021
            ivme_olcer_y = float(registers[22])   # 1022
            ivme_olcer_z = float(registers[23])   # 1023
            ivme_olcer_x_hz = float(registers[35])  # 1035
            ivme_olcer_y_hz = float(registers[36])  # 1036
            ivme_olcer_z_hz = float(registers[37])  # 1037

            # Torque percentage (no additional scaling, raw /10 already applied in PLC)
            inme_motor_tork = float(registers[18])  # 1018

            # Alarm bilgisi as hex string
            alarm_bilgisi = f"0x{alarm_bilgisi_raw:04x}"

            # Maximum vibration frequency
            max_titresim_hz = max(ivme_olcer_x_hz, ivme_olcer_y_hz, ivme_olcer_z_hz)

            # Power (kWh) - IEEE754 float from two 16-bit registers (1042, 1043)
            guc_kwh = self._decode_ieee754(registers[42], registers[43])

            return RawSensorData(
                timestamp=datetime.now(),

                # Motor measurements
                serit_motor_akim_a=serit_motor_akim_a,
                serit_motor_tork_percentage=serit_motor_tork,
                inme_motor_akim_a=inme_motor_akim_a,
                inme_motor_tork_percentage=inme_motor_tork,

                # Speed values (actual - from registers 1033/1034)
                serit_kesme_hizi=serit_kesme_hizi,
                serit_inme_hizi=serit_inme_hizi,

                # Target speed values (from registers 2066/2041)
                kesme_hizi_hedef=kesme_hizi_hedef,
                inme_hizi_hedef=inme_hizi_hedef,

                # Mechanical measurements
                kafa_yuksekligi_mm=kafa_yuksekligi_mm,
                serit_sapmasi=serit_sapmasi,
                serit_gerginligi_bar=serit_gerginligi_bar,
                mengene_basinc_bar=mengene_basinc_bar,

                # Environmental measurements
                ortam_sicakligi_c=ortam_sicakligi_c,
                ortam_nem_percentage=ortam_nem_percentage,
                sogutma_sivi_sicakligi_c=sogutma_sivi_sicakligi_c,
                hidrolik_yag_sicakligi_c=hidrolik_yag_sicakligi_c,

                # Vibration measurements
                ivme_olcer_x=ivme_olcer_x,
                ivme_olcer_y=ivme_olcer_y,
                ivme_olcer_z=ivme_olcer_z,
                ivme_olcer_x_hz=ivme_olcer_x_hz,
                ivme_olcer_y_hz=ivme_olcer_y_hz,
                ivme_olcer_z_hz=ivme_olcer_z_hz,
                max_titresim_hz=max_titresim_hz,

                # State information
                testere_durumu=testere_durumu,
                alarm_status=alarm_status,
                alarm_bilgisi=alarm_bilgisi,

                # Identification
                makine_id=makine_id,
                serit_id=serit_id,

                # Material information
                malzeme_cinsi=malzeme_cinsi,
                malzeme_sertlik=malzeme_sertlik,
                kesit_yapisi=kesit_yapisi,
                malzeme_a_mm=a_mm,
                malzeme_b_mm=b_mm,
                malzeme_c_mm=c_mm,
                malzeme_d_mm=d_mm,
                malzeme_genisligi=malzeme_genisligi,

                # Band information
                serit_tip=serit_tip,
                serit_marka=serit_marka,
                serit_malz=serit_malz,
                serit_dis_mm=serit_dis_mm,

                # Statistics
                kesilen_parca_adeti=kesilen_parca_adeti,

                # Power measurement
                guc_kwh=guc_kwh
            )

        except Exception as e:
            logger.debug(f"Error reading sensors: {e}")
            return None

    def _decode_inme_hizi(self, raw_value: int) -> float:
        """
        Decode descent speed (special handling from old project).

        Args:
            raw_value: Raw register value

        Returns:
            Descent speed in mm/min
        """
        if raw_value == 0:
            return 0.0
        elif raw_value > 500:
            return float(raw_value - 65536)
        else:
            return float(raw_value)

    def _decode_ieee754(self, low_word: int, high_word: int) -> float:
        """
        Decode IEEE754 32-bit float from two 16-bit Modbus registers.

        Args:
            low_word: Low 16-bit register value (1042)
            high_word: High 16-bit register value (1043)

        Returns:
            Decoded float value
        """
        try:
            # Combine two 16-bit registers into 32-bit value
            # Big-endian word order: high_word first, then low_word
            combined = (high_word << 16) | low_word
            # Pack as unsigned 32-bit integer, unpack as float
            packed = struct.pack('>I', combined)
            value = struct.unpack('>f', packed)[0]
            return value
        except Exception as e:
            logger.debug(f"IEEE754 decode error: {e}")
            return 0.0

    def get_last_raw_registers(self) -> list:
        """
        Get the last raw register values (unprocessed).

        Returns:
            List of 44 raw 16-bit register values, or empty list if no data
        """
        return self._last_raw_registers.copy() if self._last_raw_registers else []
