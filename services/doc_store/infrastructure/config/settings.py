"""Configuration settings for Doc Store infrastructure.

Provides centralized configuration management for the Doc Store service.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ServiceConfig:
    """Service configuration settings."""

    service_name: str = "doc_store"
    service_version: str = "1.0.0"
    debug_mode: bool = False
    max_connections: int = 100
    cache_ttl: int = 3600
    db_path: str = ":memory:"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> 'ServiceConfig':
        """Create configuration from environment variables."""
        return cls(
            service_name=os.getenv("DOC_STORE_SERVICE_NAME", "doc_store"),
            service_version=os.getenv("DOC_STORE_VERSION", "1.0.0"),
            debug_mode=os.getenv("DOC_STORE_DEBUG", "false").lower() == "true",
            max_connections=int(os.getenv("DOC_STORE_MAX_CONNECTIONS", "100")),
            cache_ttl=int(os.getenv("DOC_STORE_CACHE_TTL", "3600")),
            db_path=os.getenv("DOC_STORE_DB_PATH", ":memory:"),
            log_level=os.getenv("DOC_STORE_LOG_LEVEL", "INFO")
        )


def get_service_config() -> ServiceConfig:
    """Get the current service configuration.

    Returns:
        ServiceConfig instance with current settings
    """
    return ServiceConfig.from_env()


def get_database_config() -> Dict[str, Any]:
    """Get database configuration settings.

    Returns:
        Dictionary with database configuration
    """
    config = get_service_config()
    return {
        "path": config.db_path,
        "max_connections": config.max_connections,
        "timeout": 30.0
    }


def get_cache_config() -> Dict[str, Any]:
    """Get cache configuration settings.

    Returns:
        Dictionary with cache configuration
    """
    config = get_service_config()
    return {
        "ttl": config.cache_ttl,
        "max_size": 1000,
        "cleanup_interval": 300
    }
