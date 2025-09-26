"""Infrastructure adapters for Doc Store service.

Adapters provide interfaces to external systems and services.
"""

from .database_adapter import DatabaseAdapter

__all__ = [
    "DatabaseAdapter",
]
