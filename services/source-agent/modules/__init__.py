"""Source Agent modules package.

This package contains all the modularized functionality for the Source Agent service.
Provides shared utilities and client instances for all source agent modules.
"""

from services.shared.utilities import get_service_client

# Shared service client for all source agent modules - lazy initialization
_service_client = None

def get_source_agent_client():
    """Get the shared service client for source agent modules.

    Uses lazy initialization pattern to create client only when first needed.
    This ensures efficient resource usage and proper initialization order.
    """
    global _service_client
    if _service_client is None:
        _service_client = get_service_client()
    return _service_client

# Module-level client instance for direct access (optional optimization)
source_agent_client = None

def initialize_source_agent_client():
    """Initialize the module-level source agent client."""
    global source_agent_client
    if source_agent_client is None:
        source_agent_client = get_service_client()
    return source_agent_client

# Export key module functions for easier importing
__all__ = [
    'get_source_agent_client',
    'initialize_source_agent_client',
    'source_agent_client'
]
