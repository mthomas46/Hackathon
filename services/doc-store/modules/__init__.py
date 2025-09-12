"""Doc Store modules package.

This package contains all the modularized functionality for the Doc Store service.
Provides shared utilities and client instances for all doc store modules.
"""

from services.shared.utilities import get_service_client

# Shared service client for all doc store modules - lazy initialization
_service_client = None

def get_doc_store_client():
    """Get the shared service client for doc store modules.

    Uses lazy initialization pattern to create client only when first needed.
    This ensures efficient resource usage and proper initialization order.
    """
    global _service_client
    if _service_client is None:
        _service_client = get_service_client()
    return _service_client

# Module-level client instance for direct access (optional optimization)
doc_store_client = None

def initialize_doc_store_client():
    """Initialize the module-level doc store client."""
    global doc_store_client
    if doc_store_client is None:
        doc_store_client = get_service_client()
    return doc_store_client

# Export key module functions for easier importing
__all__ = [
    'get_doc_store_client',
    'initialize_doc_store_client',
    'doc_store_client'
]
