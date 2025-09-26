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

# Import entities
from . import entities as entities_module
from . import value_objects as value_objects_module
from . import repositories as repositories_module
from . import services as services_module
from . import exceptions as exceptions_module

# Re-export for convenience
Service = entities_module.Service
Endpoint = entities_module.Endpoint
DiscoveryResult = entities_module.DiscoveryResult

DiscoverySpec = value_objects_module.DiscoverySpec
EndpointMetadata = value_objects_module.EndpointMetadata
ServiceMetadata = value_objects_module.ServiceMetadata

ServiceRepository = repositories_module.ServiceRepository
InMemoryServiceRepository = repositories_module.InMemoryServiceRepository

DiscoveryService = services_module.DiscoveryService
EndpointAnalyzer = services_module.EndpointAnalyzer

DiscoveryError = exceptions_module.DiscoveryError
ServiceDiscoveryError = exceptions_module.ServiceDiscoveryError
InvalidOpenApiSpecError = exceptions_module.InvalidOpenApiSpecError
ServiceNotFoundError = exceptions_module.ServiceNotFoundError
EndpointDiscoveryError = exceptions_module.EndpointDiscoveryError
DuplicateServiceError = exceptions_module.DuplicateServiceError
NetworkTimeoutError = exceptions_module.NetworkTimeoutError
AuthenticationRequiredError = exceptions_module.AuthenticationRequiredError
UnsupportedApiVersionError = exceptions_module.UnsupportedApiVersionError
MalformedUrlError = exceptions_module.MalformedUrlError
DiscoveryConfigurationError = exceptions_module.DiscoveryConfigurationError

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
