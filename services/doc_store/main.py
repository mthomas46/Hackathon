"""Doc Store Service - Refactored Domain-Driven Architecture

A comprehensive document storage and analysis service with advanced features
for document management, search, analytics, and lifecycle operations.
"""

from fastapi import FastAPI

# ============================================================================
# STANDARDIZED SHARED INFRASTRUCTURE - Using consolidated utilities
# ============================================================================
from services.shared.infrastructure.config import DocStoreConfig, load_service_config
from services.shared.utilities import ServiceException, ValidationException
from services.shared.utilities import setup_common_middleware
from services.shared.presentation.responses import create_success_response
from services.shared.utilities import create_validation_error

from .api.routes import router as api_router

# ============================================================================
# NEW DOMAIN-DRIVEN ARCHITECTURE - Clean separation of concerns
# ============================================================================
from .db.schema import init_database
from .infrastructure.cache import docstore_cache

# ============================================================================
# CONFIGURATION - Using standardized config system
# ============================================================================

# Load configuration using standardized system
config = load_service_config(
    service_type="doc-store",
    config_file="./config.yaml",  # Optional config file override
)

# ============================================================================
# FASTAPI APPLICATION - Clean and minimal with standardized features
# ============================================================================
app = FastAPI(
    title="Doc Store Service",
    description="Document storage and analysis service with advanced features",
    version=config.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup standardized middleware and utilities
setup_common_middleware(app, service_name=config.service_name)


# Add standardized error handling
@app.exception_handler(ServiceException)
async def service_exception_handler(request, exc: ServiceException):
    from services.shared.presentation.responses import create_error_response

    return create_error_response(
        message=str(exc),
        error_code=exc.__class__.__name__,
        request_id=getattr(exc, "request_id", None),
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(request, exc: ValidationException):
    from services.shared.presentation.responses import create_error_response

    return create_error_response(
        message=str(exc),
        error_code="ValidationError",
        request_id=getattr(exc, "request_id", None),
    )


# Database initialization on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup."""
    try:
        # Initialize database schema
        from .db.schema import init_database

        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


# Health endpoint using standardized response system
@app.get("/health")
async def health_check():
    """Health check endpoint with standardized response."""
    try:
        # Test database connectivity
        from .db.connection import get_doc_store_connection

        conn = get_doc_store_connection()
        if conn:
            db_status = "healthy"
        else:
            db_status = "unhealthy"
    except Exception:
        db_status = "error"

    return create_success_response(
        data={
            "status": "healthy",
            "service": config.service_name,
            "version": config.service_version,
            "database_status": db_status,
            "features": {
                "document_storage": True,
                "search": True,
                "analytics": True,
                "versioning": True,
                "tagging": True,
            },
        },
        message="Service is healthy",
    )


# Skip custom health endpoint registration - using simple one above
# from services.shared.monitoring.health import create_health_endpoint, create_system_health_endpoint, create_dependency_health_endpoint
# app.get("/health")(create_health_endpoint(health_manager))
# Skip all shared health endpoints
# app.get("/health/system")(create_system_health_endpoint(health_manager))
# app.get("/health/dependency/{service_name}")(create_dependency_health_endpoint(health_manager))


# ============================================================================
# LIFECYCLE MANAGEMENT - Startup and shutdown
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    init_database()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await docstore_cache.close()


# ============================================================================
# API ROUTES - Include consolidated domain-driven routes
# ============================================================================
app.include_router(api_router)

# Monkey patch the shared health system's healthy_response function
from services.shared.monitoring.health import healthy_response

original_healthy_response = healthy_response


def custom_healthy_response(service_name: str, version: str = "1.0.0", **kwargs):
    """Custom healthy response that includes database_connected for doc_store."""
    if service_name == ServiceNames.DOC_STORE:
        kwargs["database_connected"] = check_database_connection()
    return original_healthy_response(service_name, version, **kwargs)


# Apply monkey patch
import services.shared.monitoring.health

services.shared.monitoring.health.healthy_response = custom_healthy_response

# ============================================================================
# MAIN ENTRY POINT - Clean service startup
# ============================================================================
if __name__ == "__main__":
    """Run the Doc Store service directly."""
    import uvicorn

    # Load port from configuration
    port = get_config_value("port", 5000, section="server", env_key="DOCSTORE_PORT")

    uvicorn.run(app, host="127.0.0.1", port=int(port), log_level="info")
