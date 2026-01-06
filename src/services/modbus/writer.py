"""
High-level Modbus command writing service.

Writing format (from old project utils/helpers.py):
- Cutting speed (2066): Direct integer value, no scaling
- Descent speed (2041): Multiply by 100 (e.g., 20 mm/min -> 2000)
"""

import asyncio
import logging
from ...domain.validators import validate_speed

logger = logging.getLogger(__name__)


class ModbusWriter:
    """High-level Modbus command writer."""

    # Target speed register addresses (same as in ModbusReader)
    KESME_HIZI_TARGET_ADDRESS = 2066
    INME_HIZI_TARGET_ADDRESS = 2041

    def __init__(self, modbus_client, register_map: dict, speed_limits: dict):
        """
        Initialize writer.

        Args:
            modbus_client: AsyncModbusService instance
            register_map: Register address mapping (not used, kept for compatibility)
            speed_limits: Speed limit configuration
        """
        self.modbus = modbus_client
        self.regs = register_map
        self.limits = speed_limits

    async def write_speeds(self, kesme_hizi: float, inme_hizi: float) -> bool:
        """
        Write cutting and descent speeds to Modbus.

        Based on old project (utils/helpers.py reverse_calculate_value):
        - Cutting speed (2066): Direct integer value, no scaling
        - Descent speed (2041): Multiply by 100

        Args:
            kesme_hizi: Cutting speed (mm/min)
            inme_hizi: Descent speed (mm/min)

        Returns:
            True if both writes successful
        """
        try:
            # Validate and clamp speeds
            kesme_hizi = validate_speed(
                kesme_hizi,
                self.limits['kesme_hizi']['min'],
                self.limits['kesme_hizi']['max'],
                'kesme_hizi'
            )

            inme_hizi = validate_speed(
                inme_hizi,
                self.limits['inme_hizi']['min'],
                self.limits['inme_hizi']['max'],
                'inme_hizi'
            )

            # Convert to register values (from old project helpers.py)
            # Cutting speed: direct int value (no scaling)
            kesme_register = int(kesme_hizi)
            # Descent speed: multiply by 100 (e.g., 20 -> 2000)
            inme_register = int(inme_hizi * 100)

            # Write cutting speed to register 2066
            success1 = await self.modbus.write_register(
                self.KESME_HIZI_TARGET_ADDRESS,
                kesme_register
            )

            if not success1:
                logger.error("Failed to write cutting speed")
                return False

            # Small delay between writes (110ms as in old project)
            await asyncio.sleep(0.11)

            # Write descent speed to register 2041
            success2 = await self.modbus.write_register(
                self.INME_HIZI_TARGET_ADDRESS,
                inme_register
            )

            if not success2:
                logger.error("Failed to write descent speed")
                return False

            logger.debug(
                f"Speeds written: kesme={kesme_hizi:.1f} (reg={kesme_register}), "
                f"inme={inme_hizi:.1f} (reg={inme_register})"
            )
            return True

        except Exception as e:
            logger.error(f"Error writing speeds: {e}", exc_info=True)
            return False
