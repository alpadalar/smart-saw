"""
Centralized logging system with colored console output and file rotation.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, Any

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Setup logging system based on configuration.

    Args:
        config: Logging configuration dictionary

    Returns:
        Root logger instance
    """
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Get logging config
    log_config = config.get('logging', {})
    log_level = config.get('application', {}).get('log_level', 'INFO')

    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with color (if available)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)

    if HAS_COLORLOG:
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white'
            }
        )
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.handlers.RotatingFileHandler(
        filename=logs_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    # Create specialized loggers
    _create_module_logger('smartsaw.services.modbus', logs_dir / "modbus.log", detailed_formatter)
    _create_module_logger('smartsaw.services.database', logs_dir / "database.log", detailed_formatter)
    _create_module_logger('smartsaw.services.control', logs_dir / "control.log", detailed_formatter)
    _create_module_logger('smartsaw.services.iot', logs_dir / "iot.log", detailed_formatter)

    root_logger.info("Logging system initialized")
    return root_logger


def _create_module_logger(name: str, log_file: Path, formatter: logging.Formatter):
    """Create a specialized logger for a module."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
