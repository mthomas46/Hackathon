"""CLI modules package.

This package contains all the modularized functionality for the CLI service.
Provides shared utilities and client instances for all CLI modules.
"""

from services.shared.utilities import get_service_client

# Shared service client for all CLI modules - lazy initialization
_service_client = None

def get_cli_client():
    """Get the shared service client for CLI modules.

    Uses lazy initialization pattern to create client only when first needed.
    This ensures efficient resource usage and proper initialization order.
    """
    global _service_client
    if _service_client is None:
        _service_client = get_service_client()
    return _service_client

# Module-level client instance for direct access (optional optimization)
cli_client = None

def initialize_cli_client():
    """Initialize the module-level CLI client."""
    global cli_client
    if cli_client is None:
        cli_client = get_service_client()
    return cli_client

# Export key module functions for easier importing
__all__ = [
    'get_cli_client',
    'initialize_cli_client',
    'cli_client'
]
