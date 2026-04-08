"""Unit tests for HealthCalculator.

Tests cover: broken percentage calculation (normal, zero teeth, over-max),
saw health formula (perfect, mixed, zero teeth with wear), status labels,
and color codes.

All tests are pure unit tests — no mocking needed as HealthCalculator
contains only deterministic arithmetic logic.
"""

from __future__ import annotations

import pytest

from src.services.camera.health_calculator import HealthCalculator


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def calc() -> HealthCalculator:
    """Return a fresh HealthCalculator instance."""
    return HealthCalculator()


# ---------------------------------------------------------------------------
# Broken percentage tests
# ---------------------------------------------------------------------------


def test_broken_percentage_normal(calc: HealthCalculator) -> None:
    """10 teeth, 3 broken => 30.0%."""
    result = calc.calculate_broken_percentage(10, 3)
    assert result == pytest.approx(30.0)


def test_broken_percentage_zero_teeth(calc: HealthCalculator) -> None:
    """0 teeth, 5 broken => 0.0% (guard clause: no division by zero)."""
    result = calc.calculate_broken_percentage(0, 5)
    assert result == pytest.approx(0.0)


def test_broken_percentage_clamped(calc: HealthCalculator) -> None:
    """10 teeth, 15 broken => 100.0% (clamped to max at 100%)."""
    result = calc.calculate_broken_percentage(10, 15)
    assert result == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# Saw health formula tests
# ---------------------------------------------------------------------------


def test_saw_health_perfect(calc: HealthCalculator) -> None:
    """10 teeth, 0 broken, 0% wear => health = 100.0."""
    result = calc.calculate_saw_health(10, 0, 0.0)
    assert result == pytest.approx(100.0)


def test_saw_health_mixed(calc: HealthCalculator) -> None:
    """10 teeth, 3 broken, 50% wear => health = 64.0.

    broken_pct = 30.0%
    health = 100 - ((0.30 * 0.70 + 0.50 * 0.30) * 100)
           = 100 - ((0.21 + 0.15) * 100)
           = 100 - 36
           = 64.0
    """
    result = calc.calculate_saw_health(10, 3, 50.0)
    assert result == pytest.approx(64.0)


def test_saw_health_zero_teeth_with_wear(calc: HealthCalculator) -> None:
    """0 teeth, 0 broken, 80% wear => health = 76.0.

    broken_pct = 0.0% (guard clause)
    health = 100 - ((0.0 + 0.80 * 0.30) * 100)
           = 100 - 24
           = 76.0
    """
    result = calc.calculate_saw_health(0, 0, 80.0)
    assert result == pytest.approx(76.0)


# ---------------------------------------------------------------------------
# Status label tests
# ---------------------------------------------------------------------------


def test_health_status_labels(calc: HealthCalculator) -> None:
    """Status labels use correct thresholds with Turkish Unicode strings."""
    assert calc.get_health_status(85.0) == "Sağlıklı"
    assert calc.get_health_status(65.0) == "İyi"
    assert calc.get_health_status(45.0) == "Orta"
    assert calc.get_health_status(25.0) == "Kritik"
    assert calc.get_health_status(15.0) == "Tehlikeli"

    # Boundary values
    assert calc.get_health_status(80.0) == "Sağlıklı"
    assert calc.get_health_status(60.0) == "İyi"
    assert calc.get_health_status(40.0) == "Orta"
    assert calc.get_health_status(20.0) == "Kritik"
    assert calc.get_health_status(0.0) == "Tehlikeli"


# ---------------------------------------------------------------------------
# Color code tests
# ---------------------------------------------------------------------------


def test_health_color_codes(calc: HealthCalculator) -> None:
    """Color codes map to correct CSS hex values at each threshold."""
    assert calc.get_health_color(85.0) == "#00FF00"
    assert calc.get_health_color(65.0) == "#90EE90"
    assert calc.get_health_color(45.0) == "#FFFF00"
    assert calc.get_health_color(25.0) == "#FFA500"
    assert calc.get_health_color(15.0) == "#FF0000"

    # Boundary values
    assert calc.get_health_color(80.0) == "#00FF00"
    assert calc.get_health_color(60.0) == "#90EE90"
    assert calc.get_health_color(40.0) == "#FFFF00"
    assert calc.get_health_color(20.0) == "#FFA500"


# ---------------------------------------------------------------------------
# Custom weight tests
# ---------------------------------------------------------------------------


def test_custom_weights_affect_health() -> None:
    """HealthCalculator with custom weights produces different health score.

    With broken_weight=0.5, wear_weight=0.5:
    10 teeth, 3 broken (30%), 50% wear:
    health = 100 - ((0.30 * 0.5 + 0.50 * 0.5) * 100)
           = 100 - ((0.15 + 0.25) * 100)
           = 100 - 40
           = 60.0
    """
    calc = HealthCalculator(broken_weight=0.5, wear_weight=0.5)
    result = calc.calculate_saw_health(10, 3, 50.0)
    assert result == pytest.approx(60.0)


def test_custom_weights_only_broken() -> None:
    """HealthCalculator with broken_weight=1.0, wear_weight=0.0 ignores wear.

    10 teeth, 3 broken (30%), 80% wear:
    health = 100 - ((0.30 * 1.0 + 0.80 * 0.0) * 100)
           = 100 - 30
           = 70.0
    """
    calc = HealthCalculator(broken_weight=1.0, wear_weight=0.0)
    result = calc.calculate_saw_health(10, 3, 80.0)
    assert result == pytest.approx(70.0)


def test_default_constructor_unchanged() -> None:
    """HealthCalculator() without args still uses 0.7/0.3 defaults."""
    calc = HealthCalculator()
    assert calc.BROKEN_WEIGHT == pytest.approx(0.7)
    assert calc.WEAR_WEIGHT == pytest.approx(0.3)
