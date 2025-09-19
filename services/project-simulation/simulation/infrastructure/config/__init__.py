"""Configuration Management System.

Provides centralized configuration management with environment-specific
overrides, validation, and dynamic loading capabilities.
"""

from .config_manager import ConfigManager, get_config
from .environment import EnvironmentConfig
from .validation import ConfigValidator

# Add is_development function
def is_development() -> bool:
    """Check if running in development environment."""
    config = get_config()
    return config.service.environment.lower() == "development"

__all__ = [
    'ConfigManager',
    'get_config',
    'is_development',
    'EnvironmentConfig',
    'ConfigValidator'
]
