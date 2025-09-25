"""Common Configuration Utilities

Reduces code duplication by providing standardized configuration patterns
used throughout the shared service and ecosystem.

This module provides:
- Service configuration management
- Environment variable handling
- Configuration validation
- Service initialization patterns
- Configuration loading utilities
"""

import os
from typing import Any, Dict, Optional, List, Union, Callable
from pathlib import Path
from functools import lru_cache

from .validation_utils import validate_service_config, validate_port_number, ServiceException


# ============================================================================
# SERVICE CONFIGURATION MANAGEMENT (REDUCING DUPLICATION)
# ============================================================================

class ServiceConfig:
    """Base configuration class for services.

    Provides common configuration patterns used across all services,
    reducing duplication in service initialization.

    This class handles:
    - Environment variable loading with defaults
    - Configuration validation
    - Service metadata management
    - Common service settings
    """

    def __init__(self, service_name: str, version: str = "1.0.0",
                 config_prefix: str = "", validate_on_init: bool = True):
        """Initialize service configuration.

        Args:
            service_name: Name of the service
            version: Service version
            config_prefix: Prefix for environment variables (e.g., "MY_SERVICE_")
            validate_on_init: Whether to validate configuration on initialization
        """
        self.service_name = service_name
        self.version = version
        self.config_prefix = config_prefix.upper()
        self.environment = self._get_env_var("ENVIRONMENT", "development")
        self.debug = self._get_env_var("DEBUG", "false").lower() == "true"
        self.log_level = self._get_env_var("LOG_LEVEL", "INFO")

        # Service networking
        self.host = self._get_env_var("HOST", "0.0.0.0")
        self.port = validate_port_number(self._get_env_var("PORT", "8000"))

        # Database configuration
        self.database_url = self._get_env_var("DATABASE_URL")
        self.redis_url = self._get_env_var("REDIS_URL")

        # External service URLs
        self.api_base_url = self._get_env_var("API_BASE_URL", f"http://localhost:{self.port}")

        # Performance settings
        self.max_workers = int(self._get_env_var("MAX_WORKERS", "4"))
        self.request_timeout = float(self._get_env_var("REQUEST_TIMEOUT", "30.0"))

        # Security settings
        self.secret_key = self._get_env_var("SECRET_KEY")
        self.allowed_origins = self._parse_comma_separated_list(
            self._get_env_var("ALLOWED_ORIGINS", "*")
        )

        if validate_on_init:
            self.validate()

    def _get_env_var(self, name: str, default: str = None) -> Optional[str]:
        """Get environment variable with optional prefix."""
        env_name = f"{self.config_prefix}{name}" if self.config_prefix else name
        return os.getenv(env_name, default)

    def _parse_comma_separated_list(self, value: str) -> List[str]:
        """Parse comma-separated string into list."""
        if not value or value == "*":
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]

    def validate(self) -> None:
        """Validate configuration."""
        config_dict = {
            "service_name": self.service_name,
            "version": self.version,
            "environment": self.environment
        }
        validate_service_config(config_dict, self.service_name)

        # Validate critical configuration
        if not self.secret_key and self.environment == "production":
            raise ServiceException(
                f"SECRET_KEY is required in production environment for {self.service_name}",
                "configuration_error",
                500
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "service_name": self.service_name,
            "version": self.version,
            "environment": self.environment,
            "debug": self.debug,
            "log_level": self.log_level,
            "host": self.host,
            "port": self.port,
            "database_url": self.database_url,
            "redis_url": self.redis_url,
            "api_base_url": self.api_base_url,
            "max_workers": self.max_workers,
            "request_timeout": self.request_timeout,
            "allowed_origins": self.allowed_origins
        }


# ============================================================================
# ENVIRONMENT VARIABLE HANDLING (REDUCING DUPLICATION)
# ============================================================================

def get_required_env_var(name: str, description: str = "") -> str:
    """Get required environment variable.

    Common pattern for required environment variables across services.

    Args:
        name: Environment variable name
        description: Description for error message

    Returns:
        Environment variable value

    Raises:
        ServiceException: If environment variable is not set
    """
    value = os.getenv(name)
    if value is None:
        desc = f" ({description})" if description else ""
        raise ServiceException(
            f"Required environment variable {name} is not set{desc}",
            "configuration_error",
            500,
            {"missing_variable": name}
        )
    return value

def get_env_var_with_default(name: str, default: Any,
                           converter: Callable[[str], Any] = None) -> Any:
    """Get environment variable with default value and optional conversion.

    Common pattern for optional environment variables with type conversion.

    Args:
        name: Environment variable name
        default: Default value if not set
        converter: Function to convert string value (e.g., int, float, bool)

    Returns:
        Environment variable value or default
    """
    value = os.getenv(name)
    if value is None:
        return default

    if converter is not None:
        try:
            return converter(value)
        except (ValueError, TypeError) as e:
            raise ServiceException(
                f"Invalid value for environment variable {name}: {value}",
                "configuration_error",
                500,
                {"variable": name, "value": value, "error": str(e)}
            )

    return value

def get_bool_env_var(name: str, default: bool = False) -> bool:
    """Get boolean environment variable.

    Common pattern for boolean environment variables.

    Args:
        name: Environment variable name
        default: Default value

    Returns:
        Boolean value
    """
    value = os.getenv(name, str(default)).lower()
    return value in ("true", "1", "yes", "on")

def get_list_env_var(name: str, default: List[str] = None,
                    separator: str = ",") -> List[str]:
    """Get list environment variable.

    Common pattern for comma-separated list environment variables.

    Args:
        name: Environment variable name
        default: Default list value
        separator: List separator

    Returns:
        List of values
    """
    value = os.getenv(name)
    if value is None:
        return default or []

    return [item.strip() for item in value.split(separator) if item.strip()]


# ============================================================================
# CONFIGURATION LOADING UTILITIES (REDUCING DUPLICATION)
# ============================================================================

@lru_cache(maxsize=1)
def load_service_config_from_file(config_path: Union[str, Path],
                                service_name: str) -> Dict[str, Any]:
    """Load service configuration from YAML file.

    Common pattern for loading service configuration from files.

    Args:
        config_path: Path to configuration file
        service_name: Name of the service for error messages

    Returns:
        Configuration dictionary

    Raises:
        ServiceException: If configuration file cannot be loaded
    """
    try:
        import yaml
    except ImportError:
        raise ServiceException(
            "PyYAML is required for configuration file loading",
            "configuration_error",
            500
        )

    config_file = Path(config_path)
    if not config_file.exists():
        raise ServiceException(
            f"Configuration file not found: {config_path}",
            "configuration_error",
            500,
            {"config_path": str(config_path)}
        )

    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            raise ServiceException(
                f"Invalid configuration file format: {config_path}",
                "configuration_error",
                500,
                {"config_path": str(config_path)}
            )

        return config

    except yaml.YAMLError as e:
        raise ServiceException(
            f"Error parsing configuration file {config_path}: {e}",
            "configuration_error",
            500,
            {"config_path": str(config_path), "error": str(e)}
        )
    except Exception as e:
        raise ServiceException(
            f"Error reading configuration file {config_path}: {e}",
            "configuration_error",
            500,
            {"config_path": str(config_path), "error": str(e)}
        )

def merge_configs(base_config: Dict[str, Any],
                 override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries.

    Common pattern for configuration merging (e.g., base config + environment overrides).

    Args:
        base_config: Base configuration
        override_config: Override configuration

    Returns:
        Merged configuration
    """
    merged = base_config.copy()

    for key, value in override_config.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            # Recursively merge nested dictionaries
            merged[key] = merge_configs(merged[key], value)
        else:
            # Override with new value
            merged[key] = value

    return merged


# ============================================================================
# SERVICE INITIALIZATION PATTERNS (REDUCING DUPLICATION)
# ============================================================================

def create_service_logger(service_name: str, config: ServiceConfig) -> Any:
    """Create standardized logger for service.

    Common pattern for service logger initialization.

    Args:
        service_name: Name of the service
        config: Service configuration

    Returns:
        Configured logger instance
    """
    try:
        from ..logging.logger import get_service_logger
        return get_service_logger(service_name, config.log_level)
    except ImportError:
        # Fallback to basic logging
        import logging
        logger = logging.getLogger(service_name)
        logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {service_name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

def initialize_service_monitoring(service_name: str, config: ServiceConfig,
                                health_check_endpoint: str = "/health") -> Dict[str, Any]:
    """Initialize service monitoring and health checks.

    Common pattern for service monitoring setup.

    Args:
        service_name: Name of the service
        config: Service configuration
        health_check_endpoint: Health check endpoint path

    Returns:
        Monitoring configuration dictionary
    """
    monitoring_config = {
        "service_name": service_name,
        "version": config.version,
        "environment": config.environment,
        "health_endpoint": health_check_endpoint,
        "metrics_enabled": True,
        "tracing_enabled": config.environment in ["staging", "production"]
    }

    # Initialize health monitor if available
    try:
        from ..monitoring.health import HealthMonitor
        monitoring_config["health_monitor"] = HealthMonitor(
            service_name=service_name,
            version=config.version
        )
    except ImportError:
        monitoring_config["health_monitor"] = None

    return monitoring_config

def setup_service_database(config: ServiceConfig) -> Optional[Any]:
    """Setup service database connection.

    Common pattern for database initialization.

    Args:
        config: Service configuration

    Returns:
        Database connection or None if not configured
    """
    if not config.database_url:
        return None

    try:
        # This would be service-specific, but we provide the pattern
        from ..database.connection import create_database_connection
        return create_database_connection(config.database_url)
    except ImportError:
        # Database support not available
        return None

def setup_service_cache(config: ServiceConfig) -> Optional[Any]:
    """Setup service caching layer.

    Common pattern for cache initialization.

    Args:
        config: Service configuration

    Returns:
        Cache instance or None if not configured
    """
    if not config.redis_url:
        return None

    try:
        from ..performance.cache.redis_cache import RedisCache
        return RedisCache(config.redis_url)
    except ImportError:
        # Cache support not available
        return None
