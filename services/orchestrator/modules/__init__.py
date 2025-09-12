"""Orchestrator modules package.

This package contains all the modularized functionality for the Orchestrator service.
Provides shared utilities and client instances for all orchestrator modules.
"""

from services.shared.utilities import get_service_client

# Shared service client for all orchestrator modules - lazy initialization
_service_client = None

def get_orchestrator_client():
    """Get the shared service client for orchestrator modules.

    Uses lazy initialization pattern to create client only when first needed.
    This ensures efficient resource usage and proper initialization order.
    """
    global _service_client
    if _service_client is None:
        _service_client = get_service_client()
    return _service_client

# Module-level client instance for direct access (optional optimization)
orchestrator_client = None

def initialize_orchestrator_client():
    """Initialize the module-level orchestrator client."""
    global orchestrator_client
    if orchestrator_client is None:
        orchestrator_client = get_service_client()
    return orchestrator_client

# Export key module functions for easier importing
__all__ = [
    'get_orchestrator_client',
    'initialize_orchestrator_client',
    'orchestrator_client'
]
