#!/usr/bin/env python3
"""
Shared Infrastructure Service

Demonstrates the usage of shared utilities and provides a reference
implementation for other services. This service showcases the
comprehensive error handling, logging, and infrastructure patterns
that all services in the ecosystem should follow.

The shared service itself doesn't provide business functionality but
serves as a foundation and example for proper service architecture.
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logger = logging.getLogger(__name__)

# Import shared infrastructure
from services.shared.infrastructure.config import load_service_config
from services.shared.core.constants_new import EnvVars
from services.shared.infrastructure.utilities.middleware import setup_common_middleware, get_request_id
from services.shared.infrastructure.utilities.error_handling import (
    register_exception_handlers,
    ServiceException,
    ValidationException,
    NotFoundException,
    AuthenticationException,
    AuthorizationException,
)
from services.shared.infrastructure.monitoring.health import register_health_endpoints
from services.shared.presentation.api.responses import create_success_response, create_error_response

# Load configuration
config = load_service_config(service_name="shared")

# Create FastAPI application
app = FastAPI(
    title="Shared Infrastructure Service",
    description="""
    A comprehensive shared infrastructure service that provides common utilities, patterns, and reference implementations for the entire service ecosystem.

    ## Features

    * **Error Handling**: Comprehensive exception handling with custom error types and proper HTTP status codes
    * **Logging**: Structured logging with correlation IDs and performance monitoring
    * **Health Checks**: Service health monitoring and dependency validation
    * **Configuration**: Centralized configuration management with environment variable support
    * **Middleware**: CORS, authentication, and request tracking middleware
    * **Response Formatting**: Standardized API response formats across all services
    * **Domain Patterns**: Reference implementations of DDD patterns, CQRS, and repository patterns

    ## Usage

    This service serves as a reference implementation and utility provider for other services in the ecosystem. It demonstrates proper service architecture patterns that should be followed by all services.

    ## Authentication

    All endpoints support standardized authentication middleware.

    ## Monitoring

    Comprehensive logging and health check endpoints are available for monitoring service status.
    """,
    version=config.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": os.getenv(EnvVars.SHARED_CONTACT_NAME, "Shared Infrastructure Team"),
        "email": os.getenv(EnvVars.SHARED_CONTACT_EMAIL, "shared@company.com"),
        "url": os.getenv(EnvVars.SHARED_CONTACT_URL, "https://shared.company.com/support")
    },
    license_info={
        "name": os.getenv(EnvVars.SHARED_LICENSE_NAME, "Proprietary"),
        "url": os.getenv(EnvVars.SHARED_LICENSE_URL, "https://shared.company.com/license")
    },
    tags_metadata=[
        {
            "name": "health",
            "description": "Service health monitoring and status checks"
        },
        {
            "name": "utilities",
            "description": "Shared utility functions and reference implementations"
        },
        {
            "name": "patterns",
            "description": "Reference implementations of architectural patterns"
        },
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup middleware
setup_common_middleware(app, service_name="shared")

# Register exception handlers with comprehensive coverage
register_exception_handlers(app)

# Additional error handler examples for different scenarios
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with proper formatting."""
    return create_error_response(
        message=exc.detail,
        error_code="http_error",
        status_code=exc.status_code,
        request_id=getattr(request.state, 'correlation_id', None)
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Handle any unhandled exceptions with proper logging."""
    # Log the error
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return create_error_response(
        message="An unexpected error occurred",
        error_code="internal_error",
        details={"error_type": type(exc).__name__} if os.environ.get("DEBUG") else None,
        request_id=getattr(request.state, 'correlation_id', None)
    )

# Register health endpoints
register_health_endpoints(app, "shared", config.service_version)


# ============================================================================
# DEMONSTRATION ENDPOINTS
# ============================================================================

@app.get("/", tags=["health"])
async def root():
    """Root endpoint demonstrating successful response format."""
    return create_success_response(
        data={
            "service": "shared",
            "version": config.service_version,
            "description": "Shared infrastructure demonstration service",
            "capabilities": [
                "error_handling",
                "logging",
                "health_checks",
                "configuration_management",
                "domain_driven_design",
                "cqrs_patterns",
                "resilience_services"
            ]
        },
        message="Shared infrastructure service is operational"
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return create_success_response(
        data={
            "status": "healthy",
            "service": "shared",
            "version": config.service_version,
            "infrastructure_status": {
                "domain_layer": "available",
                "error_handling": "configured",
                "logging": "active",
                "monitoring": "enabled",
                "configuration": "loaded"
            }
        },
        message="All shared infrastructure components are operational"
    )


@app.get("/error-demo/{error_type}")
async def error_demo(error_type: str):
    """
    Demonstration endpoint showing different error types.

    Available error types:
    - validation: ValidationException
    - not_found: NotFoundException
    - auth: AuthenticationException
    - forbidden: AuthorizationException
    - service: ServiceException
    """
    if error_type == "validation":
        raise ValidationException(
            message="Invalid input provided",
            field_errors={"input": ["Field is required", "Must be a valid format"]}
        )
    elif error_type == "not_found":
        raise NotFoundException("resource", "demo-resource-123")
    elif error_type == "auth":
        raise AuthenticationException("Valid credentials required")
    elif error_type == "forbidden":
        raise AuthorizationException("Insufficient permissions for this operation")
    elif error_type == "service":
        raise ServiceException(
            message="Service temporarily unavailable",
            error_code="service_unavailable",
            status_code=503,
            details={"retry_after": 30}
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown error type: {error_type}")


@app.get("/domain-demo")
async def domain_demo():
    """
    Demonstration of domain-driven design patterns.

    Shows usage of:
    - Value objects
    - Domain services
    - Exception handling
    """
    from .domain.value_objects import EmailAddress, Money
    from .domain.domain_services import NotificationService
    from .domain.exceptions import create_validation_error

    try:
        # Demonstrate value objects
        email = EmailAddress("demo@example.com")
        amount = Money(99.99, "USD")

        # Demonstrate domain service
        notification_svc = NotificationService()
        priority = notification_svc.calculate_notification_priority(
            "user_registration", "normal"
        )

        return create_success_response(
            data={
                "value_objects": {
                    "email": str(email.value),
                    "amount": f"{amount.amount} {amount.currency}"
                },
                "domain_service": {
                    "notification_priority": priority
                },
                "domain_patterns": [
                    "Value Objects (EmailAddress, Money)",
                    "Domain Services (NotificationService)",
                    "Exception Hierarchy (ValidationError, BusinessRuleViolationError)",
                    "Repository Pattern (BaseRepository, SqlRepository)",
                    "CQRS Pattern (CommandHandler, QueryHandler)"
                ]
            },
            message="Domain-driven design patterns demonstrated successfully"
        )

    except Exception as e:
        raise ServiceException(
            message="Domain demonstration failed",
            error_code="domain_demo_error",
            details={"error": str(e)}
        )


@app.get("/resilience-demo")
async def resilience_demo():
    """
    Demonstration of resilience patterns.

    Shows usage of:
    - Circuit breakers
    - Retry policies
    - Fallback mechanisms
    - Connection pooling
    """
    return create_success_response(
        data={
            "resilience_patterns": [
                "Circuit Breaker (failure detection and recovery)",
                "Retry Service (exponential backoff, jitter)",
                "Fallback Service (cache-based, external API)",
                "Self-Healing Service (automatic restart, consistency checks)",
                "Connection Pooling (database, HTTP, Redis)",
                "Process Monitoring (memory leaks, CPU usage)",
                "Service Mesh (dynamic discovery, load balancing)"
            ],
            "usage_examples": {
                "circuit_breaker": "services.shared.utilities.circuit_breaker_service",
                "retry_policy": "services.shared.utilities.retry_service",
                "connection_pool": "services.shared.utilities.connection_pool_service",
                "health_monitoring": "services.shared.monitoring.health"
            }
        },
        message="Resilience patterns available in shared infrastructure"
    )


@app.get("/architecture-info")
async def architecture_info():
    """
    Information about the shared service architecture.

    Demonstrates the layered architecture used throughout the ecosystem.
    """
    return create_success_response(
        data={
            "architecture": {
                "layers": [
                    "Presentation Layer (API, responses, middleware)",
                    "Application Layer (use cases, commands, queries)",
                    "Domain Layer (entities, services, business rules)",
                    "Infrastructure Layer (external APIs, databases, frameworks)"
                ],
                "patterns": [
                    "Domain-Driven Design (DDD)",
                    "Command Query Responsibility Segregation (CQRS)",
                    "Repository Pattern",
                    "Dependency Injection",
                    "Observer Pattern (events)",
                    "Strategy Pattern (resilience)"
                ],
                "infrastructure": [
                    "FastAPI (web framework)",
                    "Pydantic (data validation)",
                    "aiosqlite (async database)",
                    "httpx (async HTTP client)",
                    "structlog (structured logging)",
                    "prometheus (metrics)"
                ]
            },
            "service_types": {
                "utility_services": ["shared", "monitoring", "caching"],
                "business_services": ["doc_store", "prompt_store", "analysis-service"],
                "interface_services": ["frontend", "cli", "orchestrator"],
                "infrastructure_services": ["discovery-agent", "service-mesh"]
            }
        },
        message="Shared service architecture information"
    )


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("🚀 Shared infrastructure service starting...")

    # Validate configuration
    if not config.service_name:
        raise ValueError("Service name not configured")

    logger.info("✅ Shared infrastructure service started successfully")
    logger.info(f"📊 Service: {config.service_name}")
    logger.info(f"🏷️  Version: {config.service_version}")
    logger.info(f"🌐 Port: {config.server.port}")
    docs_host = os.getenv(EnvVars.SHARED_DOCS_API_HOST, "localhost")
    docs_port = os.getenv(EnvVars.SHARED_DOCS_API_PORT, "8000")
    logger.info(f"📚 Documentation: http://{docs_host}:{docs_port}/docs")
    yield

    # Shutdown
    logger.info("🛑 Shared infrastructure service shutting down...")

    # Cleanup resources
    logger.info("✅ Shared infrastructure service stopped")


# Apply lifespan
app.router.lifespan_context = lifespan


if __name__ == "__main__":
    import uvicorn

    logger.info("🏗️  Starting Shared Infrastructure Service...")
    logger.info("This service demonstrates proper usage of shared ecosystem utilities.")
    docs_host = os.getenv(EnvVars.SHARED_DOCS_API_HOST, "localhost")
    docs_port = os.getenv(EnvVars.SHARED_DOCS_API_PORT, "8000")
    logger.info(f"Visit http://{docs_host}:{docs_port}/docs for interactive API documentation.")

    uvicorn.run(
        "services.shared.main:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_level="info"
    )
