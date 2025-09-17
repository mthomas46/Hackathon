"""DEPRECATED: Shared utilities have been moved to DDD architecture layers.

This module is kept temporarily for backward compatibility during migration.
All functions have been moved to appropriate DDD layers:

- Infrastructure utilities → infrastructure/utils.py
- Domain validation utilities → shared/domain/utils.py
- Presentation utilities → presentation/utils.py

TODO: Remove this file after completing DDD migration.
"""

# Re-export functions from new locations for backward compatibility
from ..infrastructure.utils import get_service_url, prepare_correlation_headers
from ..shared.domain.utils import validate_request_data, sanitize_string_input
from ..presentation.utils import handle_service_error, create_service_success_response, build_operation_context as build_orchestrator_context

# Keep the old function that depends on local imports
def get_orchestrator_service_client():
    """Get orchestrator service client with standardized error handling."""
    from . import get_orchestrator_client
    try:
        return get_orchestrator_client()
    except Exception as e:
        from services.shared.logging import fire_and_forget
        from services.shared.constants_new import ServiceNames
        fire_and_forget("error", f"Failed to get orchestrator service client: {e}", ServiceNames.ORCHESTRATOR)
        raise


__all__ = [
    'get_orchestrator_service_client',
    'get_service_url',
    'prepare_correlation_headers',
    'handle_service_error',
    'create_service_success_response',
    'validate_request_data',
    'sanitize_string_input',
    'build_orchestrator_context'
]
