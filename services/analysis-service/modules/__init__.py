"""Analysis Service modules package.

This package contains all the modularized functionality for the Analysis Service.
Provides shared utilities and client instances for all analysis modules.
"""

from services.shared.utilities import get_service_client

# Shared service client for all analysis modules - lazy initialization
_service_client = None

def get_analysis_service_client():
    """Get the shared service client for analysis modules.

    Uses lazy initialization pattern to create client only when first needed.
    This ensures efficient resource usage and proper initialization order.
    """
    global _service_client
    if _service_client is None:
        _service_client = get_service_client()
    return _service_client

# Module-level client instance for direct access (optional optimization)
analysis_client = None

def initialize_analysis_client():
    """Initialize the module-level analysis client."""
    global analysis_client
    if analysis_client is None:
        analysis_client = get_service_client()
    return analysis_client

# Export key module functions for easier importing
__all__ = [
    'get_analysis_service_client',
    'initialize_analysis_client',
    'analysis_client'
]
