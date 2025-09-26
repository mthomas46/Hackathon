"""Domain Layer - Service Discovery Business Logic.

This module contains the domain layer for the service discovery agent,
implementing Domain-Driven Design principles for service endpoint discovery
and management.

Key Components:
- Service: Represents a discovered service with its endpoints
- Endpoint: Represents an individual API endpoint
- DiscoverySpec: Value object for OpenAPI specifications
- DiscoveryResult: Result of a discovery operation
- ServiceRepository: Repository interface for service persistence
- DiscoveryService: Core domain service for discovery operations
"""

# Direct imports from .py files
# Import entities
from .entities import Endpoint, Service, DiscoveryResult

# Import value objects
from .value_objects import DiscoverySpec, EndpointMetadata, ServiceMetadata
from .repositories import ServiceRepository, InMemoryServiceRepository
from .services import DiscoveryService, EndpointAnalyzer
from .exceptions import (
    DiscoveryError, ServiceDiscoveryError, InvalidOpenApiSpecError,
    ServiceNotFoundError, EndpointDiscoveryError, DuplicateServiceError,
    NetworkTimeoutError, AuthenticationRequiredError, UnsupportedApiVersionError,
    MalformedUrlError, DiscoveryConfigurationError
)


__all__ = [
    # Entities
    "Service", "Endpoint", "DiscoveryResult",

    # Value Objects
    "DiscoverySpec", "EndpointMetadata", "ServiceMetadata",

    # Repositories
    "ServiceRepository", "InMemoryServiceRepository",

    # Services
    "DiscoveryService", "EndpointAnalyzer",

    # Exceptions
    "DiscoveryError", "ServiceDiscoveryError", "InvalidOpenApiSpecError",
    "ServiceNotFoundError", "EndpointDiscoveryError", "DuplicateServiceError",
    "NetworkTimeoutError", "AuthenticationRequiredError", "UnsupportedApiVersionError",
    "MalformedUrlError", "DiscoveryConfigurationError",
]
