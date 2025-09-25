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
from services.shared.presentation.responses import create_success_response, create_error_response
from services.shared.utilities import create_validation_error

from .api.routes import router as api_router

# ============================================================================
# DOMAIN EXCEPTIONS - Doc Store specific exceptions
# ============================================================================
from .domain.exceptions import (
    DocStoreException,
    DocumentException,
    DocumentNotFoundException,
    DocumentValidationException,
    DocumentSizeExceededException,
    DocumentContentTypeException,
    VersioningException,
    VersionNotFoundException,
    VersionConflictException,
    TaggingException,
    TagNotFoundException,
    InvalidTagException,
    RelationshipsException,
    RelationshipNotFoundException,
    CircularReferenceException,
    BulkOperationException,
    BulkOperationTimeoutException,
    AnalyticsException,
    InvalidAnalyticsQueryException,
    LifecycleException,
    InvalidLifecycleTransitionException,
    NotificationsException,
    NotificationDeliveryException,
)

# ============================================================================
# NEW DOMAIN-DRIVEN ARCHITECTURE - Clean separation of concerns
# ============================================================================
from .db.schema import init_database
from .infrastructure.cache import docstore_cache
from .infrastructure.di.container import container

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
    description="""
    A comprehensive document storage and analysis service built with Domain-Driven Design principles.

    ## Features

    * **Document Management**: Store, retrieve, and manage documents with full lifecycle support
    * **Advanced Search**: Full-text search with semantic similarity and relevance scoring
    * **Version Control**: Complete document versioning with diff tracking and rollback
    * **Analytics**: Document quality analysis, trends, and predictive maintenance
    * **Tagging System**: Flexible hierarchical tagging with validation and auto-completion
    * **Relationships**: Complex document relationships and dependency management
    * **Bulk Operations**: High-performance batch operations with progress tracking
    * **Lifecycle Management**: Automated document lifecycle transitions and cleanup
    * **Real-time Notifications**: Event-driven notifications for document changes
    * **RESTful API**: Complete REST API with OpenAPI/Swagger documentation

    ## Authentication

    All endpoints require authentication via JWT tokens or API keys.

    ## Rate Limiting

    API endpoints are rate-limited to ensure fair usage and system stability.
    """,
    version=config.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Doc Store Team",
        "email": "docstore@company.com",
        "url": "https://docstore.company.com/support"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://docstore.company.com/license"
    },
    tags_metadata=[
        {
            "name": "documents",
            "description": "Core document operations: create, read, update, delete"
        },
        {
            "name": "search",
            "description": "Advanced search and discovery operations"
        },
        {
            "name": "analytics",
            "description": "Document analytics and quality assessment"
        },
        {
            "name": "versioning",
            "description": "Document version control and history"
        },
        {
            "name": "tagging",
            "description": "Document tagging and categorization"
        },
        {
            "name": "relationships",
            "description": "Document relationships and dependencies"
        },
        {
            "name": "bulk",
            "description": "Bulk operations for multiple documents"
        },
        {
            "name": "lifecycle",
            "description": "Document lifecycle management"
        },
        {
            "name": "notifications",
            "description": "Event notifications and webhooks"
        },
        {
            "name": "health",
            "description": "Service health and monitoring"
        }
    ]
)

# Setup standardized middleware and utilities
setup_common_middleware(app, service_name=config.service_name)


# ============================================================================
# COMPREHENSIVE ERROR HANDLING - Domain-specific exception handlers
# ============================================================================

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


@app.exception_handler(DocStoreException)
async def docstore_exception_handler(request: Request, exc: DocStoreException):
    """Handle Doc Store domain exceptions."""
    return JSONResponse(
        status_code=400,
        content=create_error_response(
            message=f"Doc Store error: {exc.message}",
            error_code="DOC_STORE_ERROR",
            details=exc.details
        )
    )


@app.exception_handler(DocumentNotFoundException)
async def document_not_found_handler(request: Request, exc: DocumentNotFoundException):
    """Handle document not found exceptions."""
    return JSONResponse(
        status_code=404,
        content=create_error_response(
            message=f"Document not found: {exc.message}",
            error_code="DOCUMENT_NOT_FOUND",
            details=exc.details
        )
    )


@app.exception_handler(DocumentValidationException)
async def document_validation_handler(request: Request, exc: DocumentValidationException):
    """Handle document validation exceptions."""
    return JSONResponse(
        status_code=400,
        content=create_error_response(
            message=f"Document validation failed: {exc.message}",
            error_code="DOCUMENT_VALIDATION_ERROR",
            details={"validation_errors": exc.validation_errors}
        )
    )


@app.exception_handler(DocumentSizeExceededException)
async def document_size_handler(request: Request, exc: DocumentSizeExceededException):
    """Handle document size exceeded exceptions."""
    return JSONResponse(
        status_code=413,
        content=create_error_response(
            message=f"Document too large: {exc.message}",
            error_code="DOCUMENT_SIZE_EXCEEDED",
            details=exc.details
        )
    )


@app.exception_handler(VersionNotFoundException)
async def version_not_found_handler(request: Request, exc: VersionNotFoundException):
    """Handle version not found exceptions."""
    return JSONResponse(
        status_code=404,
        content=create_error_response(
            message=f"Version not found: {exc.message}",
            error_code="VERSION_NOT_FOUND",
            details=exc.details
        )
    )


@app.exception_handler(VersionConflictException)
async def version_conflict_handler(request: Request, exc: VersionConflictException):
    """Handle version conflict exceptions."""
    return JSONResponse(
        status_code=409,
        content=create_error_response(
            message=f"Version conflict: {exc.message}",
            error_code="VERSION_CONFLICT",
            details=exc.details
        )
    )


@app.exception_handler(BulkOperationTimeoutException)
async def bulk_timeout_handler(request: Request, exc: BulkOperationTimeoutException):
    """Handle bulk operation timeout exceptions."""
    return JSONResponse(
        status_code=408,
        content=create_error_response(
            message=f"Bulk operation timeout: {exc.message}",
            error_code="BULK_OPERATION_TIMEOUT",
            details=exc.details
        )
    )


@app.exception_handler(InvalidLifecycleTransitionException)
async def lifecycle_transition_handler(request: Request, exc: InvalidLifecycleTransitionException):
    """Handle invalid lifecycle transition exceptions."""
    return JSONResponse(
        status_code=400,
        content=create_error_response(
            message=f"Invalid lifecycle transition: {exc.message}",
            error_code="INVALID_LIFECYCLE_TRANSITION",
            details=exc.details
        )
    )


@app.exception_handler(NotificationDeliveryException)
async def notification_delivery_handler(request: Request, exc: NotificationDeliveryException):
    """Handle notification delivery exceptions."""
    return JSONResponse(
        status_code=502,
        content=create_error_response(
            message=f"Notification delivery failed: {exc.message}",
            error_code="NOTIFICATION_DELIVERY_FAILED",
            details=exc.details
        )
    )


# Legacy exception handlers for backward compatibility
@app.exception_handler(ServiceException)
async def service_exception_handler(request: Request, exc: ServiceException):
    """Handle shared service exceptions."""
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            message=str(exc),
            error_code=exc.__class__.__name__,
            details={"request_id": getattr(exc, "request_id", None)}
        )
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle shared validation exceptions."""
    return JSONResponse(
        status_code=400,
        content=create_error_response(
            message=str(exc),
            error_code="VALIDATION_ERROR",
            details={"request_id": getattr(exc, "request_id", None)}
        )
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions."""
    # Log the error for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception in {request.url.path}: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=create_error_response(
            message="An unexpected error occurred. Please try again later.",
            error_code="INTERNAL_SERVER_ERROR",
            details={"path": str(request.url.path)}
        )
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
# METRICS ENDPOINT - Prometheus monitoring
# ============================================================================

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint for monitoring."""
    # This would integrate with a proper metrics collection system
    # For now, return basic service health metrics
    return f"""# HELP doc_store_info Service information
# TYPE doc_store_info gauge
doc_store_info{{version="{config.service_version}",service="doc-store"}} 1

# HELP doc_store_up Service availability
# TYPE doc_store_up gauge
doc_store_up 1

# HELP doc_store_health_status Health check status
# TYPE doc_store_health_status gauge
doc_store_health_status 1
"""

# ============================================================================
# MAIN ENTRY POINT - Clean service startup
# ============================================================================
if __name__ == "__main__":
    """Run the Doc Store service directly."""
    import uvicorn

    # Load port from configuration
    port = get_config_value("port", 5000, section="server", env_key="DOCSTORE_PORT")

    uvicorn.run(app, host="127.0.0.1", port=int(port), log_level="info")
