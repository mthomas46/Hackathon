"""
Shared Services Module

This module provides shared functionality across all services in the LLM Documentation Ecosystem.

Directory Structure:
- core/: Core functionality (config, models, responses, constants)
- enterprise/: Enterprise-grade features (error handling, service mesh, integration)
- integrations/: Service integrations and clients
- utilities/: Utility functions and helpers
- monitoring/: Health, logging, and metrics
- caching/: Intelligent caching systems
- streaming/: Event streaming and real-time features
- operational/: Operational excellence features
- auth/: Authentication and authorization
- web/: Web-related utilities (HTML, envelopes)
- prompts/: Prompt management functionality
- reporting/: Report generation and management
- testing/: Testing fixtures and mocks

All modules are designed to be imported and used consistently across
the entire ecosystem to reduce code duplication and improve maintainability.
"""

# Only import core functionality to avoid circular dependencies and missing dependencies
from .core.constants_new import *
from .core.models import *
from .core.responses import *

__version__ = "2.0.0"
__all__ = [
    # Core functionality only
    "constants_new", "models", "responses"
]
