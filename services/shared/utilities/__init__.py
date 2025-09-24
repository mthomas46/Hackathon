"""Shared Utilities Package.

This package contains utility functions and helpers used across all services
in the LLM Documentation Ecosystem.

Modules:
- utilities: Core utility functions
- middleware: HTTP middleware components
- error_handling: Standardized error handling
- helpers: Additional helper functions
- validation: Input validation utilities
- observability: Monitoring and observability helpers
- resilience: Circuit breaker and retry logic
"""

from .build_cache_optimizer import (
    BuildCacheOptimizer,
    analyze_dockerfile_cache,
    create_dockerignore_template,
    generate_optimized_dockerfile,
)
from .build_preflight_checks import (
    BuildCheck,
    BuildCheckResult,
    BuildPreflightChecker,
    create_preflight_dockerfile_checker,
    run_preflight_checks,
)
from .centralized_logging_service import (
    LogQuery,
    LogRetentionPolicy,
    LogStorageType,
    get_centralized_logging_service,
    get_correlation_logs,
    query_logs,
    store_log_entry,
)
from .circuit_breaker_service import execute_with_circuit_breaker, get_circuit_breaker_service
from .connection_pool_service import (
    ConnectionConfig,
    ConnectionType,
    PoolMetrics,
    PoolState,
    create_database_pool,
    create_http_pool,
    get_connection_pool_service,
)
from .error_handling import ServiceException, ValidationException
from .fallback_service import (
    CacheFallback,
    DegradationStrategy,
    FallbackPriority,
    FallbackResult,
    FallbackStrategy,
    ServiceFallback,
    execute_with_fallback,
    get_fallback_service,
    register_fallback,
    set_service_degradation,
)
from .health_check_service import (
    DatabaseHealthCheck,
    HealthCheck,
    HealthCheckType,
    HealthStatus,
    HTTPHealthCheck,
    PerformanceHealthCheck,
    ResourceHealthCheck,
    add_dependency_check,
    check_service_health,
    get_health_check_service,
    register_health_checks,
)
from .kubernetes_probes_service import (
    ProbeConfig,
    ProbeResult,
    create_fast_startup_probes,
    create_kubernetes_probes_service,
    create_resilient_probes,
    create_standard_probes,
)
from .logging_service import (
    StructuredLogger,
    get_correlation_id,
    get_logging_service,
    log_error,
    log_performance,
    set_correlation_id,
    with_correlation_id,
)
from .middleware import ServiceMiddleware
from .process_monitor_service import (
    AlertSeverity,
    ProcessAlert,
    ResourceType,
    force_garbage_collection,
    get_process_monitor_service,
    get_resource_summary,
    start_process_monitoring,
)

# from .observability import setup_logging, fire_and_forget  # Not implemented yet
from .resilience import CircuitBreaker, EnhancedCircuitBreaker, FailureType, ResilienceManager
from .retry_service import (
    BackoffStrategy,
    RetryPolicy,
    RetryStrategy,
    get_retry_service,
    retry_with_custom_policy,
    retry_with_policy,
)
from .self_healing_service import (
    DataConsistencyCheck,
    FailurePattern,
    HealingAction,
    HealingRule,
    get_self_healing_service,
    register_service_for_healing,
    trigger_healing_check,
)
from .service_mesh_service import (
    LoadBalancingAlgorithm,
    RoutingRule,
    ServiceEndpoint,
    ServiceInstance,
    ServiceState,
    TrafficSplit,
    get_mesh_status,
    get_service_mesh_service,
    register_mesh_service,
    route_to_service,
)
from .shutdown_service import (
    ShutdownPhase,
    get_shutdown_service,
    graceful_shutdown,
    register_cleanup_function,
    register_shutdown_hook,
)

# Import and expose key functions for easy access
from .utilities import (
    attach_self_register,
    clean_string,
    generate_id,
    get_service_client,
    iso_datetime,
    safe_filename,
    sanitize_sql_identifier,
    setup_common_middleware,
    validate_sql_identifier,
    utc_now,
)

__all__ = [
    # Core utilities
    "utc_now",
    "attach_self_register",
    "setup_common_middleware",
    "iso_datetime",
    "generate_id",
    "safe_filename",
    "clean_string",
    "get_service_client",
    "validate_sql_identifier",
    "sanitize_sql_identifier",
    # Middleware
    "ServiceMiddleware",
    # Error handling
    "ServiceException",
    "ValidationException",
    # Observability
    # 'setup_logging',  # Not implemented yet
    # 'fire_and_forget',  # Not implemented yet
    # Resilience
    "CircuitBreaker",
    "EnhancedCircuitBreaker",
    "ResilienceManager",
    "FailureType",
    "get_circuit_breaker_service",
    "execute_with_circuit_breaker",
    # Retry Service
    "get_retry_service",
    "retry_with_policy",
    "retry_with_custom_policy",
    "RetryPolicy",
    "RetryStrategy",
    "BackoffStrategy",
    # Logging Service
    "get_logging_service",
    "get_correlation_id",
    "set_correlation_id",
    "with_correlation_id",
    "log_performance",
    "log_error",
    "StructuredLogger",
    # Centralized Logging Service
    "get_centralized_logging_service",
    "store_log_entry",
    "query_logs",
    "get_correlation_logs",
    "LogStorageType",
    "LogQuery",
    "LogRetentionPolicy",
    # Shutdown Service
    "get_shutdown_service",
    "graceful_shutdown",
    "register_shutdown_hook",
    "register_cleanup_function",
    "ShutdownPhase",
    # Health Check Service
    "get_health_check_service",
    "check_service_health",
    "register_health_checks",
    "add_dependency_check",
    "HealthStatus",
    "HealthCheckType",
    "HealthCheck",
    "DatabaseHealthCheck",
    "HTTPHealthCheck",
    "PerformanceHealthCheck",
    "ResourceHealthCheck",
    # Kubernetes Probes Service
    "create_kubernetes_probes_service",
    "create_standard_probes",
    "create_fast_startup_probes",
    "create_resilient_probes",
    "ProbeConfig",
    "ProbeResult",
    # Build Preflight Checks
    "run_preflight_checks",
    "create_preflight_dockerfile_checker",
    "BuildPreflightChecker",
    "BuildCheck",
    "BuildCheckResult",
    # Build Cache Optimizer
    "analyze_dockerfile_cache",
    "generate_optimized_dockerfile",
    "create_dockerignore_template",
    "BuildCacheOptimizer",
    # Fallback Service
    "get_fallback_service",
    "execute_with_fallback",
    "register_fallback",
    "set_service_degradation",
    "FallbackStrategy",
    "FallbackPriority",
    "FallbackResult",
    "CacheFallback",
    "ServiceFallback",
    "DegradationStrategy",
    # Self-Healing Service
    "get_self_healing_service",
    "trigger_healing_check",
    "register_service_for_healing",
    "HealingAction",
    "FailurePattern",
    "HealingRule",
    "DataConsistencyCheck",
    # Connection Pool Service
    "get_connection_pool_service",
    "create_database_pool",
    "create_http_pool",
    "ConnectionType",
    "PoolState",
    "ConnectionConfig",
    "PoolMetrics",
    # Process Monitor Service
    "get_process_monitor_service",
    "start_process_monitoring",
    "get_resource_summary",
    "force_garbage_collection",
    "ResourceType",
    "AlertSeverity",
    "ProcessAlert",
    # Service Mesh Service
    "get_service_mesh_service",
    "route_to_service",
    "register_mesh_service",
    "get_mesh_status",
    "LoadBalancingAlgorithm",
    "ServiceState",
    "ServiceInstance",
    "ServiceEndpoint",
    "RoutingRule",
    "TrafficSplit",
]
