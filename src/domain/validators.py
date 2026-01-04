"""
Data validation functions.
"""

from typing import Optional
from ..core.exceptions import ValidationError


def validate_speed(value: float, min_val: float, max_val: float, name: str) -> float:
    """
    Validate speed value against limits.

    Args:
        value: Speed value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Parameter name (for error messages)

    Returns:
        Clamped value within limits

    Raises:
        ValidationError: If value is invalid (NaN, infinite)
    """
    if value != value:  # NaN check
        raise ValidationError(f"{name} is NaN")

    if abs(value) == float('inf'):
        raise ValidationError(f"{name} is infinite")

    # Clamp to limits
    return max(min_val, min(value, max_val))


def validate_register_value(value: int, max_value: int = 65535) -> int:
    """
    Validate Modbus register value.

    Args:
        value: Register value (0-65535)
        max_value: Maximum allowed value

    Returns:
        Validated value

    Raises:
        ValidationError: If value is out of range
    """
    if value < 0:
        raise ValidationError(f"Register value cannot be negative: {value}")

    if value > max_value:
        raise ValidationError(f"Register value exceeds maximum ({max_value}): {value}")

    return value


def sanitize_signed_register(value: int, bits: int = 16) -> int:
    """
    Convert unsigned register to signed integer.

    Args:
        value: Unsigned register value
        bits: Number of bits (default: 16)

    Returns:
        Signed integer value
    """
    max_val = 2 ** (bits - 1)

    if value >= max_val:
        return value - (2 ** bits)
    return value
