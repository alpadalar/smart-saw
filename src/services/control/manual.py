"""
Manual speed control (GUI-driven).
"""

import logging
from datetime import datetime
from typing import Optional

from ...domain.models import ControlCommand
from ...domain.validators import validate_speed

logger = logging.getLogger(__name__)


class ManualController:
    """
    Manual speed controller for GUI-driven operation.

    Simple pass-through controller:
    - Validates speed inputs
    - Enforces speed limits
    - Creates ControlCommand objects
    - No ML inference or automation
    """

    def __init__(self, config: dict):
        """
        Initialize manual controller.

        Args:
            config: System configuration dictionary
        """
        self.config = config
        self.limits = config['control']['speed_limits']

        logger.info("ManualController initialized")

    async def set_speeds(
        self,
        kesme_hizi: float,
        inme_hizi: float
    ) -> Optional[ControlCommand]:
        """
        Set speeds manually from GUI.

        Args:
            kesme_hizi: Desired cutting speed (mm/min)
            inme_hizi: Desired descent speed (mm/min)

        Returns:
            ControlCommand if validation successful, None otherwise
        """
        try:
            # Validate and clamp kesme_hizi
            kesme_hizi = validate_speed(
                kesme_hizi,
                self.limits['kesme_hizi']['min'],
                self.limits['kesme_hizi']['max'],
                'kesme_hizi'
            )

            # Validate and clamp inme_hizi
            inme_hizi = validate_speed(
                inme_hizi,
                self.limits['inme_hizi']['min'],
                self.limits['inme_hizi']['max'],
                'inme_hizi'
            )

            # Create command
            command = ControlCommand(
                timestamp=datetime.now(),
                kesme_hizi_target=kesme_hizi,
                inme_hizi_target=inme_hizi,
                source="manual"
            )

            logger.info(
                f"Manual speed command: "
                f"kesme={kesme_hizi:.1f}, "
                f"inme={inme_hizi:.1f}"
            )

            return command

        except Exception as e:
            logger.error(f"Error in manual speed setting: {e}", exc_info=True)
            return None

    def get_current_limits(self) -> dict:
        """
        Get current speed limits for GUI display.

        Returns:
            Dictionary with min/max limits
        """
        return {
            'kesme_hizi': {
                'min': self.limits['kesme_hizi']['min'],
                'max': self.limits['kesme_hizi']['max']
            },
            'inme_hizi': {
                'min': self.limits['inme_hizi']['min'],
                'max': self.limits['inme_hizi']['max']
            }
        }
