"""
Template Management Services

Provides template loading, validation, rendering, and tracking capabilities
for adaptive documentation generation.
"""

from .template_manager import (
    TemplateManager,
    get_template_manager,
    TemplateValidationError
)
from .template_validator import TemplateValidator, get_template_validator
from .retry_handler import (
    RetryHandler,
    GracefulDegradationHandler,
    get_retry_handler,
    get_degradation_handler,
    CircuitState
)

__all__ = [
    "TemplateManager",
    "get_template_manager",
    "TemplateValidationError",
    "TemplateValidator",
    "get_template_validator",
    "RetryHandler",
    "GracefulDegradationHandler",
    "get_retry_handler",
    "get_degradation_handler",
    "CircuitState",
]

