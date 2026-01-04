"""
Configuration management system.
Loads and validates YAML configuration files with environment variable support.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict
import yaml
from dotenv import load_dotenv

from .exceptions import ConfigurationError


class ConfigManager:
    """Manages application configuration from YAML files."""

    def __init__(self, config_path: Path = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to main configuration file (config.yaml).
                        Defaults to config/config.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'config.yaml'

        self.config_path = config_path
        self.config: Dict[str, Any] = {}

        # Load environment variables
        load_dotenv()

        # Auto-load configuration
        self.load()

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If configuration file is invalid
        """
        if not self.config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            # Substitute environment variables
            self.config = self._substitute_env_vars(self.config)

            # Validate configuration
            self._validate()

            return self.config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML syntax: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        Recursively substitute environment variables in configuration.

        Supports format: ${VAR_NAME} or ${VAR_NAME:default_value}

        Args:
            obj: Configuration object (dict, list, str, etc.)

        Returns:
            Object with substituted values
        """
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # Match ${VAR_NAME} or ${VAR_NAME:default}
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

            def replacer(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ''
                return os.getenv(var_name, default_value)

            return re.sub(pattern, replacer, obj)
        else:
            return obj

    def _validate(self):
        """
        Validate required configuration fields.

        Raises:
            ConfigurationError: If required fields are missing
        """
        required_sections = ['application', 'modbus', 'control', 'database']

        for section in required_sections:
            if section not in self.config:
                raise ConfigurationError(f"Missing required section: {section}")

        # Validate modbus config
        modbus = self.config.get('modbus', {})
        if 'host' not in modbus or 'port' not in modbus:
            raise ConfigurationError("Modbus configuration must include 'host' and 'port'")

        # Validate register addresses
        if 'registers' not in modbus:
            raise ConfigurationError("Modbus configuration missing 'registers' section")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'modbus.host')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def save(self, path: Path = None):
        """
        Save current configuration to YAML file.

        Args:
            path: Output path (defaults to original config_path)
        """
        output_path = path or self.config_path

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
