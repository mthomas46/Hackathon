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

# Import and expose key functions for easy access
from .utilities import (
    utc_now,
    attach_self_register,
    setup_common_middleware,
    iso_datetime,
    generate_id,
    safe_filename,
    clean_string,
    validate_sql_identifier,
    sanitize_sql_identifier,
    get_service_client
)
from .timeout_manager import (
    TimeoutManager,
    HealthCheckTimeout,
    StartupTimeout,
    ShutdownTimeout,
    with_health_timeout,
    with_startup_timeout,
    with_shutdown_timeout,
    with_http_timeout,
    with_db_timeout
)

from .middleware import ServiceMiddleware
from .error_handling import ServiceException, ValidationException
# from .observability import setup_logging, fire_and_forget  # Not implemented yet
from .resilience import CircuitBreaker, EnhancedCircuitBreaker, ResilienceManager, FailureType
from .circuit_breaker_service import get_circuit_breaker_service, execute_with_circuit_breaker
from .retry_service import get_retry_service, retry_with_policy, retry_with_custom_policy, RetryPolicy, RetryStrategy, BackoffStrategy
from .logging_service import (
    get_logging_service, get_correlation_id, set_correlation_id, with_correlation_id,
    log_performance, log_error, StructuredLogger
)
from .centralized_logging_service import (
    get_centralized_logging_service, store_log_entry, query_logs, get_correlation_logs,
    LogStorageType, LogQuery, LogRetentionPolicy
)
from .shutdown_service import (
    get_shutdown_service, graceful_shutdown, register_shutdown_hook,
    register_cleanup_function, ShutdownPhase
)
from .health_check_service import (
    get_health_check_service, check_service_health, register_health_checks,
    add_dependency_check, HealthStatus, HealthCheckType, HealthCheck,
    DatabaseHealthCheck, HTTPHealthCheck, PerformanceHealthCheck, ResourceHealthCheck
)
from .kubernetes_probes_service import (
    create_kubernetes_probes_service, create_standard_probes,
    create_fast_startup_probes, create_resilient_probes, ProbeConfig, ProbeResult
)
from .build_preflight_checks import (
    run_preflight_checks, create_preflight_dockerfile_checker,
    BuildPreflightChecker, BuildCheck, BuildCheckResult
)
from .build_cache_optimizer import (
    analyze_dockerfile_cache, generate_optimized_dockerfile,
    create_dockerignore_template, BuildCacheOptimizer
)
from .fallback_service import (
    get_fallback_service, execute_with_fallback, register_fallback,
    set_service_degradation, FallbackStrategy, FallbackPriority, FallbackResult,
    CacheFallback, ServiceFallback, DegradationStrategy
)
from .self_healing_service import (
    get_self_healing_service, trigger_healing_check, register_service_for_healing,
    HealingAction, FailurePattern, HealingRule, DataConsistencyCheck
)
from .connection_pool_service import (
    get_connection_pool_service, create_database_pool, create_http_pool,
    ConnectionType, PoolState, ConnectionConfig, PoolMetrics
)
from .process_monitor_service import (
    get_process_monitor_service, start_process_monitoring, get_resource_summary,
    force_garbage_collection, ResourceType, AlertSeverity, ProcessAlert
)
from .service_mesh_service import (
    get_service_mesh_service, route_to_service, register_mesh_service, get_mesh_status,
    LoadBalancingAlgorithm, ServiceState, ServiceInstance, ServiceEndpoint, RoutingRule, TrafficSplit
)

__all__ = [
    # Core utilities
    'utc_now',
    'attach_self_register',
    'setup_common_middleware',
    'iso_datetime',
    'generate_id',
    'safe_filename',
    'clean_string',
    'get_service_client',

    # Middleware
    'ServiceMiddleware',

    # Error handling
    'ServiceException',
    'ValidationException',

    # Observability
    # 'setup_logging',  # Not implemented yet
    # 'fire_and_forget',  # Not implemented yet

    # Resilience
    'CircuitBreaker',
    'EnhancedCircuitBreaker',
    'ResilienceManager',
    'FailureType',
    'get_circuit_breaker_service',
    'execute_with_circuit_breaker',

    # Retry Service
    'get_retry_service',
    'retry_with_policy',
    'retry_with_custom_policy',
    'RetryPolicy',
    'RetryStrategy',
    'BackoffStrategy',

    # Logging Service
    'get_logging_service',
    'get_correlation_id',
    'set_correlation_id',
    'with_correlation_id',
    'log_performance',
    'log_error',
    'StructuredLogger',

    # Centralized Logging Service
    'get_centralized_logging_service',
    'store_log_entry',
    'query_logs',
    'get_correlation_logs',
    'LogStorageType',
    'LogQuery',
    'LogRetentionPolicy',

    # Shutdown Service
    'get_shutdown_service',
    'graceful_shutdown',
    'register_shutdown_hook',
    'register_cleanup_function',
    'ShutdownPhase',

    # Health Check Service
    'get_health_check_service',
    'check_service_health',
    'register_health_checks',
    'add_dependency_check',
    'HealthStatus',
    'HealthCheckType',
    'HealthCheck',
    'DatabaseHealthCheck',
    'HTTPHealthCheck',
    'PerformanceHealthCheck',
    'ResourceHealthCheck',

    # Kubernetes Probes Service
    'create_kubernetes_probes_service',
    'create_standard_probes',
    'create_fast_startup_probes',
    'create_resilient_probes',
    'ProbeConfig',
    'ProbeResult',

    # Build Preflight Checks
    'run_preflight_checks',
    'create_preflight_dockerfile_checker',
    'BuildPreflightChecker',
    'BuildCheck',
    'BuildCheckResult',

    # Build Cache Optimizer
    'analyze_dockerfile_cache',
    'generate_optimized_dockerfile',
    'create_dockerignore_template',
    'BuildCacheOptimizer',

    # Fallback Service
    'get_fallback_service',
    'execute_with_fallback',
    'register_fallback',
    'set_service_degradation',
    'FallbackStrategy',
    'FallbackPriority',
    'FallbackResult',
    'CacheFallback',
    'ServiceFallback',
    'DegradationStrategy',

    # Self-Healing Service
    'get_self_healing_service',
    'trigger_healing_check',
    'register_service_for_healing',
    'HealingAction',
    'FailurePattern',
    'HealingRule',
    'DataConsistencyCheck',

    # Connection Pool Service
    'get_connection_pool_service',
    'create_database_pool',
    'create_http_pool',
    'ConnectionType',
    'PoolState',
    'ConnectionConfig',
    'PoolMetrics',

    # Process Monitor Service
    'get_process_monitor_service',
    'start_process_monitoring',
    'get_resource_summary',
    'force_garbage_collection',
    'ResourceType',
    'AlertSeverity',
    'ProcessAlert',

    # Service Mesh Service
    'get_service_mesh_service',
    'route_to_service',
    'register_mesh_service',
    'get_mesh_status',
    'LoadBalancingAlgorithm',
    'ServiceState',
    'ServiceInstance',
    'ServiceEndpoint',
    'RoutingRule',
    'TrafficSplit'
]