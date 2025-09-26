"""Domain-specific exceptions for Service Discovery.

This module defines exceptions specific to the service discovery domain,
following the shared exception hierarchy.
"""

try:
    from services.shared.domain.exceptions.exceptions import (
        DomainError,
        ValidationError,
        ServiceError,
        InfrastructureError,
        ExternalServiceError
    )
except ImportError:
    # Fallback for test environments or different working directories
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    while current_dir.parent != current_dir:
        shared_path = current_dir.parent / "shared" / "domain" / "exceptions" / "exceptions.py"
        if shared_path.exists():
            sys.path.insert(0, str(shared_path.parent.parent.parent.parent))
            break
        current_dir = current_dir.parent
    from services.shared.domain.exceptions.exceptions import (
        DomainError,
        ValidationError,
        ServiceError,
        InfrastructureError,
        ExternalServiceError
    )


class DiscoveryError(DomainError):
    """Base exception for discovery-related errors."""
    pass


class ServiceDiscoveryError(DiscoveryError):
    """Error during service discovery process."""
    pass


class InvalidOpenApiSpecError(ValidationError):
    """OpenAPI specification is invalid or malformed."""
    pass


class ServiceNotFoundError(DiscoveryError):
    """Service could not be found or accessed."""
    pass


class EndpointDiscoveryError(DiscoveryError):
    """Error while discovering endpoints."""
    pass


class DuplicateServiceError(ValidationError):
    """Service with same name or URL already exists."""
    pass


class NetworkTimeoutError(ExternalServiceError):
    """Network timeout while accessing service."""
    pass


class AuthenticationRequiredError(DiscoveryError):
    """Service requires authentication for discovery."""
    pass


class UnsupportedApiVersionError(ValidationError):
    """OpenAPI version is not supported."""
    pass


class MalformedUrlError(ValidationError):
    """Service URL is malformed or invalid."""
    pass


class DiscoveryConfigurationError(DiscoveryError):
    """Discovery configuration is invalid."""
    pass
