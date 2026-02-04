"""
High-level Modbus command writing service.

Writing format (from old project utils/helpers.py):
- Cutting speed (2066): Direct integer value, no scaling
- Descent speed (2041): Multiply by 100 (e.g., 20 mm/min -> 2000)

IMPORTANT: Each speed is written INDEPENDENTLY (matching old project).
If a speed is None, it is NOT written. This prevents oscillation caused by
writing stale values when only one speed's threshold was exceeded.
"""

import asyncio
import logging
from typing import Optional
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

    async def write_speeds(
        self,
        kesme_hizi: Optional[float],
        inme_hizi: Optional[float]
    ) -> bool:
        """
        Write cutting and/or descent speeds to Modbus.

        IMPORTANT: Each speed is written INDEPENDENTLY (matching old project).
        If a speed is None, it is NOT written to Modbus.

        Based on old project (utils/helpers.py reverse_calculate_value):
        - Cutting speed (2066): Direct integer value, no scaling
        - Descent speed (2041): Multiply by 100

        Args:
            kesme_hizi: Cutting speed (mm/min), or None to skip
            inme_hizi: Descent speed (mm/min), or None to skip

        Returns:
            True if all attempted writes successful
        """
        try:
            success = True

            # Write cutting speed if provided
            if kesme_hizi is not None:
                kesme_hizi = validate_speed(
                    kesme_hizi,
                    self.limits['kesme_hizi']['min'],
                    self.limits['kesme_hizi']['max'],
                    'kesme_hizi'
                )
                kesme_register = int(kesme_hizi)

                if not await self.modbus.write_register(
                    self.KESME_HIZI_TARGET_ADDRESS,
                    kesme_register
                ):
                    logger.error("Failed to write cutting speed")
                    success = False
                else:
                    logger.debug(f"Kesme written: {kesme_hizi:.1f} (reg={kesme_register})")

            # Small delay between writes if both are being written
            if kesme_hizi is not None and inme_hizi is not None:
                await asyncio.sleep(0.11)

            # Write descent speed if provided
            if inme_hizi is not None:
                inme_hizi = validate_speed(
                    inme_hizi,
                    self.limits['inme_hizi']['min'],
                    self.limits['inme_hizi']['max'],
                    'inme_hizi'
                )
                inme_register = int(inme_hizi * 100)

                if not await self.modbus.write_register(
                    self.INME_HIZI_TARGET_ADDRESS,
                    inme_register
                ):
                    logger.error("Failed to write descent speed")
                    success = False
                else:
                    logger.debug(f"Inme written: {inme_hizi:.1f} (reg={inme_register})")

            return success

        except Exception as e:
            logger.error(f"Error writing speeds: {e}", exc_info=True)
            return False
