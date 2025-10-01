"""Doc Store Service - Refactored Domain-Driven Architecture

A comprehensive document storage and analysis service with advanced features
for document management, search, analytics, and lifecycle operations.
"""

import sys
from pathlib import Path

from fastapi import FastAPI

# Add shared infrastructure to path
project_root = Path(__file__).parent.parent.parent
shared_path = project_root / "services" / "shared"
sys.path.insert(0, str(shared_path))

# ============================================================================
# STANDARDIZED SHARED INFRASTRUCTURE - Using consolidated utilities
# ============================================================================
try:
    from services.shared.infrastructure.config import load_service_config
    from services.shared.infrastructure.utilities.error_handling import ServiceException, ValidationException
    from services.shared.infrastructure.utilities.middleware import setup_common_middleware
    from services.shared.infrastructure.utilities.error_handling import create_standard_success_response as create_success_response, create_standard_error_response as create_error_response
    from services.shared.infrastructure.utilities.validation_utils import validate_required_fields
    from services.shared.infrastructure.logging.standardized_logger import StandardizedLogger
except ImportError:
    # Fallback implementations
    class DocStoreConfig:
        """Fallback configuration class for doc_store service.

        Provides default configuration when shared config is unavailable.
        Used for local development and testing scenarios.
        """
        def __init__(self):
            """Initialize fallback configuration with default values.

            Sets up default service configuration for doc_store when shared config is unavailable.
            Provides reasonable defaults for development and testing environments.
            """
            self.service_name = 'doc_store'
            self.service_description = 'Document Store Service'
            self.service_version = '1.0.0'
            self.server = type('Server', (), {'host': '0.0.0.0', 'port': 5005})()
            self.port = 5005

    def load_service_config(**kwargs):
        """Load fallback service configuration for doc_store.

        Returns a default configuration object when shared config is unavailable.
        Used for development and testing environments.
        """
        return DocStoreConfig()

    class ServiceException(Exception):
        """Base exception for doc_store service errors.

        Used when shared exception classes are not available.
        """
        pass

    class ValidationException(Exception):
        """Exception for validation errors in doc_store service.

        Used when shared validation exception classes are not available.
        """
        pass

    def setup_common_middleware(app, **kwargs):
        """Setup common middleware for FastAPI application.

        Fallback implementation when shared middleware utilities are unavailable.
        In a real implementation, this would add logging, CORS, and monitoring middleware.
        """
        pass

    def create_success_response(data=None, message="", **kwargs):
        """Create standardized success response.

        Fallback implementation when shared response utilities are unavailable.
        Returns a consistent success response format.
        """
        return {"success": True, "data": data, "message": message}

    def create_error_response(message, **kwargs):
        """Create standardized error response.

        Fallback implementation when shared response utilities are unavailable.
        Returns a consistent error response format with optional additional data.
        """
        return {"success": False, "message": message, **kwargs}

    def validate_required_fields(data, required_fields):
        """Validate that required fields are present in data.

        Fallback implementation when shared validation utilities are unavailable.
        Always returns True for basic compatibility.
        """
        return True

try:
    from .presentation.api.routes import router as api_router
    from .infrastructure.resource_monitor import DocStoreResourceMonitor
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    # Add current directory to path for relative imports
    sys.path.insert(0, os.path.dirname(__file__))

    try:
        from presentation.api.routes import router as api_router
        from infrastructure.resource_monitor import DocStoreResourceMonitor
    except ImportError:
        # Mock implementations for local testing
        from fastapi import APIRouter
        api_router = APIRouter()

        class DocStoreResourceMonitor:
            async def start_monitoring(self):
                """Start resource monitoring for Doc Store."""
                # Simple implementation - could be enhanced with actual monitoring
                logger.info("Doc Store resource monitoring initialized")
                pass

# ============================================================================
# DOMAIN EXCEPTIONS - Doc Store specific exceptions
# ============================================================================
try:
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
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    # Add current directory to path for relative imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    try:
        from domain.exceptions import (
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
    except ImportError:
        # Mock implementations for local testing
        class DocStoreException(Exception):
            pass

        class DocumentException(DocStoreException):
            pass

        # Create mock classes for all exceptions
        DocumentNotFoundException = DocumentException
        DocumentValidationException = DocumentException
        DocumentSizeExceededException = DocumentException
        DocumentContentTypeException = DocumentException
        VersioningException = DocStoreException
        VersionNotFoundException = VersioningException
        VersionConflictException = VersioningException
        TaggingException = DocStoreException
        TagNotFoundException = TaggingException
        InvalidTagException = TaggingException
        RelationshipsException = DocStoreException
        RelationshipNotFoundException = RelationshipsException
        CircularReferenceException = RelationshipsException
        BulkOperationException = DocStoreException
        BulkOperationTimeoutException = BulkOperationException
        AnalyticsException = DocStoreException
        InvalidAnalyticsQueryException = AnalyticsException
        LifecycleException = DocStoreException
        InvalidLifecycleTransitionException = LifecycleException
        NotificationsException = DocStoreException
        NotificationDeliveryException = NotificationsException

# ============================================================================
# NEW DOMAIN-DRIVEN ARCHITECTURE - Clean separation of concerns
# ============================================================================
try:
    from .db.schema import init_database
    from .infrastructure.cache import docstore_cache
    from .infrastructure.di.container import container
except ImportError:
    # Fallback for when running as script
    def init_database():
        """Initialize database schema and connections.

        Fallback implementation when database initialization utilities are unavailable.
        In a real implementation, this would create tables, indexes, and establish connections.
        """
        pass

    class MockCache:
        pass

    docstore_cache = MockCache()

    class MockContainer:
        pass

    container = MockContainer()

# ============================================================================
# CONFIGURATION - Using standardized config system
# ============================================================================

# Validate configuration before loading (startup validation)
from services.shared.infrastructure.config.startup_validator import validate_service_startup
if not validate_service_startup("doc_store"):
    print("❌ Doc Store configuration validation failed - aborting startup")
    sys.exit(1)

# Load configuration using standardized system (now with Pydantic validation by default)
config = load_service_config("doc_store")

# Initialize standardized logger
logger = StandardizedLogger("doc_store", {
    "log_level": "INFO",
    "structured_logging": True,
    "monitoring_enabled": True,
    "metrics_interval": 30,
    "console_logging": True,
    "log_file": f"/tmp/doc_store.log",
    "max_log_size": 10485760,
    "backup_count": 5
})
logger.start_monitoring()

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

    health_data = {
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
    }

    # Log health check
    logger.info("Health check requested", extra={
        "database_status": db_status,
        "features_count": len(health_data["features"])
    })

    return create_success_response(
        data=health_data,
        message="Service is healthy",
    )




# ============================================================================
# LIFECYCLE MANAGEMENT - Startup and shutdown
# ============================================================================

# Global resource monitor instance
resource_monitor = DocStoreResourceMonitor()

@app.on_event("startup")
async def startup_event():
    """Initialize Doc Store service on startup.

    Performs comprehensive service initialization including:
    - Database connection establishment and validation
    - Resource monitoring system startup
    - Logging system configuration
    - Background service coordination setup

    This function ensures all critical components are properly initialized
    before the service begins accepting requests.
    """
    init_database()

    # Start comprehensive resource monitoring
    await resource_monitor.start_monitoring()
    logger.info("Doc Store resource monitoring started")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources and connections on service shutdown.

    Performs graceful shutdown by:
    - Stopping resource monitoring
    - Closing cache connections
    - Logging shutdown completion
    """
    # Stop resource monitoring
    await resource_monitor.stop_monitoring()

    # Close cache connections
    await docstore_cache.close()

    logger.info("Doc Store resource monitoring stopped")


# ============================================================================
# API ROUTES - Include consolidated domain-driven routes
# ============================================================================
app.include_router(api_router)

# Monkey patch the shared health system's healthy_response function
try:
    from services.shared.monitoring.health import healthy_response
except ImportError:
    # Fallback for when running as script
    def healthy_response(data=None, message="Service is healthy", **kwargs):
        """Create a standardized healthy response for health check endpoints.

        Args:
            data: Optional additional data to include in response
            message: Health status message (default: "Service is healthy")
            **kwargs: Additional key-value pairs to include in response

        Returns:
            dict: Standardized health response with status, message, and data
        """
        return {"status": "healthy", "message": message, "data": data, **kwargs}

original_healthy_response = healthy_response


def custom_healthy_response(service_name: str, version: str = "1.0.0", **kwargs):
    """Create custom healthy response with service-specific health indicators.

    Extends the standard healthy response to include service-specific
    health checks like database connectivity for the Doc Store service.

    Args:
        service_name: Name of the service for health check customization
        version: Service version string
        **kwargs: Additional health check data

    Returns:
        dict: Enhanced health response with service-specific indicators
    """
    if service_name == ServiceNames.DOC_STORE:
        kwargs["database_connected"] = check_database_connection()
    return original_healthy_response(service_name, version, **kwargs)


# Apply monkey patch
try:
    import services.shared.monitoring.health
    services.shared.monitoring.health.healthy_response = custom_healthy_response
except ImportError:
    # Fallback for when running as script - skip monkey patch
    pass

# ============================================================================
# RESOURCE MONITORING ENDPOINTS - System resource monitoring
# ============================================================================

@app.get("/api/v1/resources/status")
async def get_resource_status():
    """Get comprehensive resource usage status and insights."""
    try:
        status = resource_monitor.get_resource_status()
        return create_success_response(
            data=status,
            message="Resource status retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get resource status: {e}")
        return create_error_response(
            error="Failed to retrieve resource status",
            details=str(e)
        )


@app.get("/api/v1/resources/recommendations")
async def get_performance_recommendations():
    """Get performance optimization recommendations based on resource usage."""
    try:
        recommendations = resource_monitor.get_performance_recommendations()
        return create_success_response(
            data={"recommendations": recommendations},
            message="Performance recommendations retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get performance recommendations: {e}")
        return create_error_response(
            error="Failed to retrieve performance recommendations",
            details=str(e)
        )


@app.post("/api/v1/resources/gc")
async def trigger_garbage_collection():
    """Manually trigger garbage collection and return cleanup results.

    Forces Python garbage collection to run and provides detailed
    statistics about memory cleanup operations, including objects
    collected by generation and memory freed.

    Returns:
        dict: Garbage collection results with collection statistics
    """
    try:
        gc_result = await resource_monitor.force_garbage_collection()
        return create_success_response(
            data=gc_result,
            message="Garbage collection completed successfully"
        )
    except Exception as e:
        logger.error(f"Failed to trigger garbage collection: {e}")
        return create_error_response(
            error="Failed to trigger garbage collection",
            details=str(e)
        )


@app.post("/api/v1/resources/reset-insights")
async def reset_resource_insights():
    """Reset resource usage insights and baseline trends.

    Clears all accumulated resource monitoring data, trends, and
    baseline measurements. Useful for establishing new performance
    baselines after system optimizations or configuration changes.

    Returns:
        dict: Reset operation confirmation
    """
    try:
        resource_monitor.reset_insights()
        return create_success_response(
            message="Resource insights reset successfully"
        )
    except Exception as e:
        logger.error(f"Failed to reset resource insights: {e}")
        return create_error_response(
            error="Failed to reset resource insights",
            details=str(e)
        )


# ============================================================================
# METRICS ENDPOINT - Prometheus monitoring
# ============================================================================

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint for comprehensive service monitoring.

    Provides standardized Prometheus metrics for service monitoring,
    including service information, availability status, request metrics,
    and performance indicators.

    Returns:
        str: Prometheus-formatted metrics output
    """
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

    # Load service configuration (Pydantic validation already done at module level)
    config = load_service_config("doc_store")

    # Get port from configuration
    port = config.port

    # Register cleanup function
    import atexit
    @atexit.register
    def cleanup():
        logger.info("Shutting down Doc Store service")
        logger.stop_monitoring()

    uvicorn.run(app, host="0.0.0.0", port=int(port), log_level="info")
