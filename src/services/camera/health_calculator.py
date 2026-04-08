"""Saw health calculator — computes overall health from broken-tooth count and wear percentage."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class HealthCalculator:
    """
    Saw health calculator.

    Computes overall saw health from broken-tooth count and wear percentage,
    using weighted impacts (default BROKEN_WEIGHT=0.7, WEAR_WEIGHT=0.3).
    Weights are configurable via constructor parameters.
    """

    def __init__(self, broken_weight: float = 0.7, wear_weight: float = 0.3) -> None:
        """Initialise with configurable impact weights.

        Args:
            broken_weight: Weight for broken-tooth impact (default 0.7).
            wear_weight: Weight for wear impact (default 0.3).
        """
        self.BROKEN_WEIGHT = broken_weight
        self.WEAR_WEIGHT = wear_weight

    def calculate_broken_percentage(
        self, detected_teeth: int, detected_broken: int
    ) -> float:
        """Return broken-tooth percentage (0-100). Returns 0.0 if teeth <= 0."""
        try:
            if detected_teeth <= 0:
                return 0.0
            broken_percentage = (detected_broken / detected_teeth) * 100.0
            return max(0.0, min(broken_percentage, 100.0))
        except Exception as e:
            logger.error("Broken percentage calculation error: %s", e)
            return 0.0

    def calculate_saw_health(
        self,
        detected_teeth: int,
        detected_broken: int,
        wear_percentage: float,
    ) -> float:
        """
        Calculate overall saw health (0-100).

        Formula:
            broken_pct = broken / teeth * 100
            health = 100 - ((broken_pct/100 * BROKEN_WEIGHT
                           + clamp(wear,0,100)/100 * WEAR_WEIGHT) * 100)

        Returns 100.0 on exception (assume healthy).
        """
        try:
            broken_pct = self.calculate_broken_percentage(
                detected_teeth, detected_broken
            )
            normalized_wear = max(0.0, min(wear_percentage, 100.0))

            broken_impact = (broken_pct / 100.0) * self.BROKEN_WEIGHT
            wear_impact = (normalized_wear / 100.0) * self.WEAR_WEIGHT
            total_impact = broken_impact + wear_impact

            saw_health = max(0.0, min(100.0, 100.0 - (total_impact * 100.0)))

            logger.debug(
                "Saw health: broken=%.2f%%, wear=%.2f%%, health=%.2f%%",
                broken_pct,
                normalized_wear,
                saw_health,
            )
            return saw_health
        except Exception as e:
            logger.error("Saw health calculation error: %s", e)
            return 100.0

    def get_health_status(self, saw_health: float) -> str:
        """Return Turkish health status label for the given health score."""
        if saw_health >= 80.0:
            return "Sağlıklı"
        elif saw_health >= 60.0:
            return "İyi"
        elif saw_health >= 40.0:
            return "Orta"
        elif saw_health >= 20.0:
            return "Kritik"
        else:
            return "Tehlikeli"

    def get_health_color(self, saw_health: float) -> str:
        """Return CSS hex color for the given health score."""
        if saw_health >= 80.0:
            return "#00FF00"
        elif saw_health >= 60.0:
            return "#90EE90"
        elif saw_health >= 40.0:
            return "#FFFF00"
        elif saw_health >= 20.0:
            return "#FFA500"
        else:
            return "#FF0000"
