"""
Shared Configuration Infrastructure

This module provides centralized configuration management for all services
in the LLM Documentation Ecosystem.
"""

from .configuration_manager import (
    ConfigurationManager,
    BaseServiceConfig,
    ServerConfig,
    RedisConfig,
    LoggingConfig,
    ServiceDependencies,
    Environment,
    ConfigurationError,
    ConfigurationValidator,
    StandardConfigurationValidator,
    create_service_config_manager,
    load_service_config
)

__all__ = [
    "ConfigurationManager",
    "BaseServiceConfig",
    "ServerConfig",
    "RedisConfig",
    "LoggingConfig",
    "ServiceDependencies",
    "Environment",
    "ConfigurationError",
    "ConfigurationValidator",
    "StandardConfigurationValidator",
    "create_service_config_manager",
    "load_service_config"
]