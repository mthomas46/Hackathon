"""Discovery Agent modules package.

This package contains all the modularized functionality for the Discovery Agent service.
Provides shared utilities and client instances for all discovery agent modules.
"""

from services.shared.utilities import get_service_client

# Shared service client for all discovery agent modules - lazy initialization
_service_client = None

def get_discovery_agent_client():
    """Get the shared service client for discovery agent modules.

    Uses lazy initialization pattern to create client only when first needed.
    This ensures efficient resource usage and proper initialization order.
    """
    global _service_client
    if _service_client is None:
        _service_client = get_service_client()
    return _service_client

# Module-level client instance for direct access (optional optimization)
discovery_agent_client = None

def initialize_discovery_agent_client():
    """Initialize the module-level discovery agent client."""
    global discovery_agent_client
    if discovery_agent_client is None:
        discovery_agent_client = get_service_client()
    return discovery_agent_client

# Export key module functions for easier importing
__all__ = [
    'get_discovery_agent_client',
    'initialize_discovery_agent_client',
    'discovery_agent_client'
]
