"""Base Configuration Classes.

This module provides the foundation for all service configurations
in the LLM Documentation Ecosystem.
"""

import os
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import ValidationError


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


class BaseConfig(ABC):
    """Abstract base class for all service configurations."""

    def __init__(self, **data):
        """Initialize configuration with validation."""
        try:
            self._validate_config(data)
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}") from e

    @abstractmethod
    def _validate_config(self, data: Dict[str, Any]) -> None:
        """Validate configuration data."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        pass

    @classmethod
    def from_env(cls, prefix: str = "") -> "BaseConfig":
        """Create configuration from environment variables."""
        env_data = {}
        for key, value in os.environ.items():
            if prefix and key.startswith(prefix):
                config_key = key[len(prefix) :].lower()
                env_data[config_key] = cls._parse_env_value(value)
        return cls(**env_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseConfig":
        """Create configuration from dictionary."""
        return cls(**data)

    @staticmethod
    def _parse_env_value(value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Simple type coercion for common cases
        if value.lower() in ("true", "false"):
            return value.lower() == "true"
        if value.isdigit():
            return int(value)
        if "." in value and all(part.isdigit() for part in value.split(".")):
            try:
                return float(value)
            except ValueError:
                pass
        return value


class EnvironmentConfig(BaseConfig):
    """Configuration loaded from environment variables."""

    def __init__(self, prefix: str = "", **overrides):
        """Initialize from environment with optional overrides.

        Args:
            prefix: Environment variable prefix to filter by
            **overrides: Configuration overrides
        """
        env_data = self._load_from_env(prefix)
        env_data.update(overrides)
        super().__init__(**env_data)

    def _load_from_env(self, prefix: str) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        for key, value in os.environ.items():
            if not prefix or key.startswith(prefix):
                config_key = key[len(prefix) :].lower() if prefix else key.lower()
                config[config_key] = self._parse_env_value(value)
        return config

    def _validate_config(self, data: Dict[str, Any]) -> None:
        """Validate environment configuration."""
        # Basic validation - can be overridden by subclasses
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.__dict__.copy()


class FileConfig(BaseConfig):
    """Configuration loaded from files (YAML, JSON, etc.)."""

    def __init__(self, file_path: str, **overrides):
        """Initialize from configuration file with optional overrides.

        Args:
            file_path: Path to configuration file
            **overrides: Configuration overrides
        """
        file_data = self._load_from_file(file_path)
        file_data.update(overrides)
        super().__init__(**file_data)

    def _load_from_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        import yaml

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.endswith((".yaml", ".yml")):
                return yaml.safe_load(f) or {}
            elif file_path.endswith(".json"):
                import json

                return json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {file_path}")

    def _validate_config(self, data: Dict[str, Any]) -> None:
        """Validate file configuration."""
        # Basic validation - can be overridden by subclasses
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.__dict__.copy()


class ConfigLoader:
    """Configuration loader supporting multiple sources."""

    def __init__(self):
        """Initialize configuration loader."""
        self._sources: list = []

    def add_environment_source(self, prefix: str = "") -> "ConfigLoader":
        """Add environment variables as configuration source."""
        self._sources.append(("env", prefix))
        return self

    def add_file_source(self, file_path: str) -> "ConfigLoader":
        """Add configuration file as source."""
        self._sources.append(("file", file_path))
        return self

    def load(self, config_class: type, **overrides) -> BaseConfig:
        """Load configuration from all sources.

        Args:
            config_class: Configuration class to instantiate
            **overrides: Final overrides for configuration

        Returns:
            Configuration instance
        """
        merged_config = {}

        for source_type, source_param in self._sources:
            try:
                if source_type == "env":
                    source_config = EnvironmentConfig(source_param)
                elif source_type == "file":
                    source_config = FileConfig(source_param)
                else:
                    continue

                merged_config.update(source_config.to_dict())
            except Exception as e:
                # Log warning but continue with other sources
                print(f"Warning: Failed to load config from {source_type} source: {e}")

        # Apply overrides
        merged_config.update(overrides)

        return config_class(**merged_config)
