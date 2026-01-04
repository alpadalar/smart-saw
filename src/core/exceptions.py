"""
Custom exception classes for Smart Saw Control System.
"""


class SmartSawException(Exception):
    """Base exception for all Smart Saw errors."""
    pass


class ModbusConnectionError(SmartSawException):
    """Raised when Modbus TCP connection fails."""
    pass


class ModbusReadError(SmartSawException):
    """Raised when reading Modbus registers fails."""
    pass


class ModbusWriteError(SmartSawException):
    """Raised when writing to Modbus registers fails."""
    pass


class DatabaseError(SmartSawException):
    """Raised for database operation errors."""
    pass


class ControllerError(SmartSawException):
    """Raised for control system errors."""
    pass


class ConfigurationError(SmartSawException):
    """Raised for configuration file errors."""
    pass


class MLModelError(SmartSawException):
    """Raised for ML model loading or inference errors."""
    pass


class ValidationError(SmartSawException):
    """Raised for data validation errors."""
    pass
