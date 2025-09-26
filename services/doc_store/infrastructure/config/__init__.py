"""Infrastructure configuration for Doc Store service.

Handles configuration management, environment variables, and service settings.
"""

from .settings import get_service_config, ServiceConfig

__all__ = [
    "get_service_config",
    "ServiceConfig",
]
