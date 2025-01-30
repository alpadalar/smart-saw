# src/control/linear/__init__.py
from .controller import (
    adjust_speeds_linear,
    LinearController,
    linear_controller
)
from .speed_matrix import speed_matrix

__all__ = [
    'adjust_speeds_linear',
    'LinearController',
    'linear_controller',
    'speed_matrix'
]