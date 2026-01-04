"""
High-level Modbus command writing service.
"""

import logging
from ...domain.validators import validate_speed

logger = logging.getLogger(__name__)


class ModbusWriter:
    """High-level Modbus command writer."""

    def __init__(self, modbus_client, register_map: dict, speed_limits: dict):
        """
        Initialize writer.

        Args:
            modbus_client: AsyncModbusService instance
            register_map: Register address mapping
            speed_limits: Speed limit configuration
        """
        self.modbus = modbus_client
        self.regs = register_map
        self.limits = speed_limits

    async def write_speeds(self, kesme_hizi: float, inme_hizi: float) -> bool:
        """
        Write cutting and descent speeds to Modbus.

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

            # Convert to register values
            kesme_register = int(kesme_hizi * 10)
            inme_register = int(inme_hizi * 100)

            # Write cutting speed
            success1 = await self.modbus.write_register(
                self.regs['KESME_HIZI'],
                kesme_register
            )

            if not success1:
                logger.error("Failed to write cutting speed")
                return False

            # Small delay between writes
            import asyncio
            await asyncio.sleep(0.11)  # 110ms

            # Write descent speed
            success2 = await self.modbus.write_register(
                self.regs['INME_HIZI'],
                inme_register
            )

            if not success2:
                logger.error("Failed to write descent speed")
                return False

            logger.debug(f"Speeds written: kesme={kesme_hizi:.1f}, inme={inme_hizi:.1f}")
            return True

        except Exception as e:
            logger.error(f"Error writing speeds: {e}", exc_info=True)
            return False
