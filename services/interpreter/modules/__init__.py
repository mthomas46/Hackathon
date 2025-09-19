"""Interpreter modules package.

This package contains all the modularized functionality for the Interpreter service.
Provides shared utilities and client instances for all interpreter modules.
"""

# Optional import - will use fallback if not available
try:
    from services.shared.utilities import get_service_client
except ImportError:
    def get_service_client(*args, **kwargs):
        # Fallback function
        pass

# Shared service client for all interpreter modules - lazy initialization
_service_client = None

def get_interpreter_client():
    """Get the shared service client for interpreter modules.

    Uses lazy initialization pattern to create client only when first needed.
    This ensures efficient resource usage and proper initialization order.
    """
    global _service_client
    if _service_client is None:
        _service_client = get_service_client()
    return _service_client

# Module-level client instance for direct access (optional optimization)
interpreter_client = None

def initialize_interpreter_client():
    """Initialize the module-level interpreter client."""
    global interpreter_client
    if interpreter_client is None:
        interpreter_client = get_service_client()
    return interpreter_client

# Export key module functions for easier importing
__all__ = [
    'get_interpreter_client',
    'initialize_interpreter_client',
    'interpreter_client'
]
