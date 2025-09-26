"""Domain layer for Bedrock Proxy service.

This module provides domain-level abstractions and business logic.
Infrastructure dependencies are avoided to maintain clean architecture.
"""

# Domain entities and services
from .entities import *
from .services import *
from .repositories import *
from .value_objects import *
from .exceptions import *

# Re-export commonly used infrastructure functions for backward compatibility
# (Note: This creates a dependency, but is acceptable for transitional compatibility)
try:
    from ..infrastructure.validation_utils.validation import *
    from ..infrastructure.templates import *
except ImportError:
    # Fallback if infrastructure not available
    pass

__all__ = []  # Domain layer exports handled by submodules
