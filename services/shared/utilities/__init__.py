"""Shared Utilities Package.

This package contains utility functions and helpers used across all services
in the LLM Documentation Ecosystem. Following Domain-Driven Design principles,
utilities are organized by bounded contexts and responsibilities.

Core Modules:
- core: Essential utilities used by all services
- infrastructure: Infrastructure-level utilities (databases, connections, etc.)
- presentation: HTTP and API utilities
- domain: Domain-level utilities and patterns
"""

# Core utilities - always available
from .utilities import (
    attach_self_register,
    clean_string,
    generate_id,
    get_service_client,  # Legacy - use shared.infrastructure.clients
    iso_datetime,
    safe_filename,
    sanitize_sql_identifier,
    setup_common_middleware,
    utc_now,
    validate_sql_identifier,
)

# Error handling - always available
from .error_handling import (
    ServiceException,
    ValidationException,
)

# Domain base classes - always available for service development
from ..domain.exceptions import (
    DomainError,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
    ServiceError,
    BusinessRuleViolationError,
    ValidationError as DomainValidationError,
    create_validation_error,
    create_business_rule_error,
    create_not_found_error,
    create_duplicate_error,
)

# Consolidated response handlers - always available
from ..presentation.responses import (
    create_success_response,
    create_error_response,
    create_validation_error_response,
    create_paginated_response,
    create_list_response,
    create_crud_response,
    APIResponse,
)

# Lazy imports for specialized functionality
# Import these modules only when needed to avoid circular dependencies


def __getattr__(name: str):
    """Lazy import for specialized utilities."""
    lazy_imports = {
        # Infrastructure utilities
        "get_circuit_breaker_service": (
            ".circuit_breaker_service",
            "get_circuit_breaker_service",
        ),
        "execute_with_circuit_breaker": (
            ".circuit_breaker_service",
            "execute_with_circuit_breaker",
        ),
        "get_connection_pool_service": (
            ".connection_pool_service",
            "get_connection_pool_service",
        ),
        "create_database_pool": (".connection_pool_service", "create_database_pool"),
        "create_http_pool": (".connection_pool_service", "create_http_pool"),
        # Consolidated service clients
        "ServiceClient": ("..infrastructure.clients", "ServiceClient"),
        "ServiceClientFactory": ("..infrastructure.clients", "ServiceClientFactory"),
        "initialize_service_clients": (
            "..infrastructure.clients",
            "initialize_service_clients",
        ),
        "get_service_client_new": ("..infrastructure.clients", "get_service_client"),
        # Configuration system
        "ServiceConfig": ("..infrastructure.config.service_config", "ServiceConfig"),
        "create_service_config": (
            "..infrastructure.config.service_config",
            "create_service_config",
        ),
        "load_service_config": (
            "..infrastructure.config.service_config",
            "load_service_config",
        ),
        # Response handlers (additional)
        "create_service_success_response": (
            "..presentation.responses",
            "create_service_success_response",
        ),
        "create_memory_agent_success_response": (
            "..presentation.responses",
            "create_memory_agent_success_response",
        ),
        # Resilience utilities
        "get_retry_service": (".retry_service", "RetryService"),
        "execute_with_retry": (".retry_service", "execute_with_retry"),
        "get_fallback_service": (".fallback_service", "get_fallback_service"),
        "execute_with_fallback": (".fallback_service", "execute_with_fallback"),
        # Logging utilities
        "get_logging_service": (".logging_service", "LoggingService"),
        "get_centralized_logging_service": (
            ".centralized_logging_service",
            "get_centralized_logging_service",
        ),
        # Health and monitoring
        "get_health_check_service": (
            ".health_check_service",
            "get_health_check_service",
        ),
        # Build utilities
        "BuildPreflightChecker": (".build_preflight_checks", "BuildPreflightChecker"),
        "BuildCacheOptimizer": (".build_cache_optimizer", "BuildCacheOptimizer"),
        # Process monitoring
        "get_process_monitor_service": (
            ".process_monitor_service",
            "ProcessMonitorService",
        ),
        # Service mesh
        "get_service_mesh_service": (".service_mesh_service", "ServiceMeshService"),
        # Self-healing
        "get_self_healing_service": (".self_healing_service", "SelfHealingService"),
        # Shutdown
        "get_shutdown_service": (".shutdown_service", "GracefulShutdownService"),
        # Middleware
        "ServiceMiddleware": (".middleware", "ServiceMiddleware"),
        # Base classes for service development
        "BaseRepository": ("..domain.base_repository", "BaseRepository"),
        "SqlRepository": ("..domain.base_repository", "SqlRepository"),
        "InMemoryRepository": ("..domain.base_repository", "InMemoryRepository"),
        "BaseService": ("..domain.base_service", "BaseService"),
        "CrudService": ("..domain.base_service", "CrudService"),
        "BaseEntity": ("..domain.base_repository", "BaseEntity"),
        # CQRS base classes for complex services
        "CommandHandler": ("..domain.cqrs_base", "CommandHandler"),
        "QueryHandler": ("..domain.cqrs_base", "QueryHandler"),
        "CommandBus": ("..domain.cqrs_base", "CommandBus"),
        "QueryBus": ("..domain.cqrs_base", "QueryBus"),
        "CommandResult": ("..domain.cqrs_base", "CommandResult"),
        "QueryResult": ("..domain.cqrs_base", "QueryResult"),
    }

    if name in lazy_imports:
        module_name, attr_name = lazy_imports[name]
        from importlib import import_module

        module = import_module(module_name, package=__name__)
        return getattr(module, attr_name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Core utilities
    "utc_now",
    "attach_self_register",
    "setup_common_middleware",
    "iso_datetime",
    "generate_id",
    "safe_filename",
    "clean_string",
    "get_service_client",  # Legacy
    "validate_sql_identifier",
    "sanitize_sql_identifier",
    # Error handling
    "ServiceException",
    "ValidationException",
    # Domain exceptions
    "DomainError",
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "ServiceError",
    "BusinessRuleViolationError",
    "DomainValidationError",
    "create_validation_error",
    "create_business_rule_error",
    "create_not_found_error",
    "create_duplicate_error",
    # Consolidated response handlers
    "create_success_response",
    "create_error_response",
    "create_validation_error_response",
    "create_paginated_response",
    "create_list_response",
    "create_crud_response",
    "APIResponse",
    # Base classes
    "BaseEntity",
    "BaseRepository",
    "SqlRepository",
    "InMemoryRepository",
    "BaseService",
    "CrudService",
    # CQRS base classes
    "CommandHandler",
    "QueryHandler",
    "CommandBus",
    "QueryBus",
    "CommandResult",
    "QueryResult",
]
