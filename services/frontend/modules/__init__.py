"""Frontend modules package.

This package contains all the modularized functionality for the Frontend service.
Provides shared utilities and client instances for all frontend modules.
"""

from services.shared.utilities import get_service_client

# Shared service client for all frontend modules - lazy initialization
_service_client = None

def get_frontend_client():
    """Get the shared service client for frontend modules.

    Uses lazy initialization pattern to create client only when first needed.
    This ensures efficient resource usage and proper initialization order.
    """
    global _service_client
    if _service_client is None:
        _service_client = get_service_client()
    return _service_client

# Module-level client instance for direct access (optional optimization)
frontend_client = None

def initialize_frontend_client():
    """Initialize the module-level frontend client."""
    global frontend_client
    if frontend_client is None:
        frontend_client = get_service_client()
    return frontend_client

# Export key module functions for easier importing
__all__ = [
    'get_frontend_client',
    'initialize_frontend_client',
    'frontend_client'
]
