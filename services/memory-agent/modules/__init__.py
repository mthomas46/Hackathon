"""Memory Agent modules package.

This package contains all the modularized functionality for the Memory Agent service.
Provides shared utilities and client instances for all memory agent modules.
"""

from services.shared.utilities import get_service_client

# Shared service client for all memory agent modules - lazy initialization
_service_client = None

def get_memory_agent_client():
    """Get the shared service client for memory agent modules.

    Uses lazy initialization pattern to create client only when first needed.
    This ensures efficient resource usage and proper initialization order.
    """
    global _service_client
    if _service_client is None:
        _service_client = get_service_client()
    return _service_client

# Module-level client instance for direct access (optional optimization)
memory_agent_client = None

def initialize_memory_agent_client():
    """Initialize the module-level memory agent client."""
    global memory_agent_client
    if memory_agent_client is None:
        memory_agent_client = get_service_client()
    return memory_agent_client

# Export key module functions for easier importing
__all__ = [
    'get_memory_agent_client',
    'initialize_memory_agent_client',
    'memory_agent_client'
]
