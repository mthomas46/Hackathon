"""Infrastructure layer for CLI service.

This layer contains adapters, repositories, and external service integrations
that provide the technical capabilities needed by the application layer.
"""

from .adapters import service_registry
from .services import config_manager

__all__ = [
    "service_registry",
    "config_manager",
]
