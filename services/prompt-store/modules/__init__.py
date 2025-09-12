"""Prompt Store modules package.

This package contains all the modularized functionality for the Prompt Store service.
Provides shared utilities and client instances for all prompt store modules.
"""

from services.shared.utilities import get_service_client

# Shared service client for all prompt store modules - lazy initialization
_service_client = None

def get_prompt_store_client():
    """Get the shared service client for prompt store modules.

    Uses lazy initialization pattern to create client only when first needed.
    This ensures efficient resource usage and proper initialization order.
    """
    global _service_client
    if _service_client is None:
        _service_client = get_service_client()
    return _service_client

# Module-level client instance for direct access (optional optimization)
prompt_store_client = None

def initialize_prompt_store_client():
    """Initialize the module-level prompt store client."""
    global prompt_store_client
    if prompt_store_client is None:
        prompt_store_client = get_service_client()
    return prompt_store_client

# Export key module functions for easier importing
__all__ = [
    'get_prompt_store_client',
    'initialize_prompt_store_client',
    'prompt_store_client'
]
