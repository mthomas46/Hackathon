"""Domain services for discovery-agent.

Exports the main domain services used by tests and application layer.
"""

# Import only working services (others have broken dependencies)
from .service_discovery import (
    discover_service,
    discover_multiple_services,
    fetch_openapi_spec,
    parse_openapi_spec,
)

__all__ = [
    "discover_service",
    "discover_multiple_services",
    "fetch_openapi_spec",
    "parse_openapi_spec",
]

