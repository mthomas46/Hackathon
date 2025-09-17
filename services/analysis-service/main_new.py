"""Refactored Analysis Service - Clean Architecture with DDD and CQRS

This is the new, clean main.py file that replaces the monolithic 2,753-line version.
It uses focused controllers and follows Domain-Driven Design principles.

Original file: 2,753 lines with 53+ endpoints mixed with business logic
New file: ~200 lines with clean separation of concerns and proper architecture
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# ============================================================================
# SHARED MODULES - Optimized import consolidation
# ============================================================================
from services.shared.monitoring.health import register_health_endpoints
from services.shared.core.responses import create_success_response, create_error_response
from services.shared.utilities.error_handling import ServiceException, install_error_handlers
from services.shared.core.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities.utilities import utc_now, generate_id, setup_common_middleware, attach_self_register

# ============================================================================
# CONTROLLERS - Clean separation of endpoint responsibilities
# ============================================================================
# Temporarily using absolute imports for local development
try:
    from .presentation.controllers import (
        AnalysisController,
        RemediationController,
        WorkflowController,
        RepositoryController,
        DistributedController,
        ReportsController,
        FindingsController,
        IntegrationController,
        PRConfidenceController
    )
    from .presentation.compatibility_layer import register_compatibility_endpoints
except ImportError:
    # Fallback for when running as script
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from presentation.controllers import (
        AnalysisController,
        RemediationController,
        WorkflowController,
        RepositoryController,
        DistributedController,
        ReportsController,
        FindingsController,
        IntegrationController,
        PRConfidenceController
    )
    from presentation.compatibility_layer import register_compatibility_endpoints

# ============================================================================
# DEPENDENCY INJECTION - Clean dependency management
# ============================================================================
from .infrastructure.repositories import SQLiteDocumentRepository, SQLiteAnalysisRepository, SQLiteFindingRepository
from .infrastructure.config import InfrastructureConfig
from .application.use_cases import PerformAnalysisUseCase
from .domain.services import DocumentService, AnalysisService, FindingService
from .domain.factories import DocumentFactory, FindingFactory


def create_application() -> FastAPI:
    """Create and configure the FastAPI application with clean architecture."""

    # ============================================================================
    # APPLICATION CONFIGURATION
    # ============================================================================
    SERVICE_NAME = "analysis-service"
    SERVICE_TITLE = "Analysis Service"
    SERVICE_VERSION = "1.0.0"
    DEFAULT_PORT = 5020

    # Create FastAPI app with clean configuration
    app = FastAPI(
        title=SERVICE_TITLE,
        description="""Document analysis and consistency checking service for the LLM Documentation Ecosystem.

        **Architecture**: Domain-Driven Design with CQRS and Clean Architecture
        **Endpoints**: 50+ organized across focused controllers
        **Features**: Advanced document analysis, distributed processing, workflow integration
        """,
        version=SERVICE_VERSION,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # ============================================================================
    # INFRASTRUCTURE SETUP
    # ============================================================================
    # Load configuration
    config = InfrastructureConfig.from_env()

    # Initialize repositories
    document_repo = SQLiteDocumentRepository()
    analysis_repo = SQLiteAnalysisRepository()
    finding_repo = SQLiteFindingRepository()

    # Initialize domain services
    document_service = DocumentService()
    analysis_service = AnalysisService({})
    finding_service = FindingService()

    # Initialize factories
    document_factory = DocumentFactory(document_service)
    finding_factory = FindingFactory(finding_service)

    # ============================================================================
    # APPLICATION SERVICES SETUP
    # ============================================================================
    # Initialize use cases
    perform_analysis_use_case = PerformAnalysisUseCase(
        analysis_service=analysis_service,
        document_repository=document_repository,
        analysis_repository=analysis_repository
    )

    # ============================================================================
    # CONTROLLER INITIALIZATION
    # ============================================================================
    # Initialize controllers with their dependencies
    analysis_controller = AnalysisController(
        perform_analysis_use_case=perform_analysis_use_case,
        document_repository=document_repository,
        analysis_repository=analysis_repository,
        analysis_service=analysis_service
    )

    remediation_controller = RemediationController()
    workflow_controller = WorkflowController()
    repository_controller = RepositoryController()
    distributed_controller = DistributedController()
    reports_controller = ReportsController()
    findings_controller = FindingsController()
    integration_controller = IntegrationController()
    pr_confidence_controller = PRConfidenceController()

    # ============================================================================
    # COMPATIBILITY LAYER REGISTRATION
    # ============================================================================
    # Register backward compatibility endpoints
    register_compatibility_endpoints(app)

    # ============================================================================
    # ROUTER REGISTRATION - Clean endpoint organization
    # ============================================================================
    controllers = [
        ("/analyze", analysis_controller),
        ("/remediate", remediation_controller),
        ("/workflows", workflow_controller),
        ("/repositories", repository_controller),
        ("/distributed", distributed_controller),
        ("/reports", reports_controller),
        ("", findings_controller),  # Root level for /findings
        ("/integration", integration_controller),
        ("", pr_confidence_controller),  # Root level for /pr-confidence
    ]

    for prefix, controller in controllers:
        app.include_router(
            controller.get_router(),
            prefix=prefix,
            tags=[controller.__class__.__name__.replace('Controller', '').lower()]
        )

    # ============================================================================
    # MIDDLEWARE & INFRASTRUCTURE
    # ============================================================================
    # Setup common middleware (CORS, logging, rate limiting, etc.)
    setup_common_middleware(app, ServiceNames.ANALYSIS_SERVICE)

    # Add CORS middleware for web client support
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Install error handlers
    install_error_handlers(app)

    # Register health endpoints
    register_health_endpoints(app, ServiceNames.ANALYSIS_SERVICE, SERVICE_VERSION)

    # Auto-register with orchestrator
    attach_self_register(app, ServiceNames.ANALYSIS_SERVICE)

    # ============================================================================
    # STARTUP EVENT - Initialize resources
    # ============================================================================
    @app.on_event("startup")
    async def startup_event():
        """Initialize resources on startup."""
        # Initialize database connections
        # Setup external service connections
        # Initialize caching layer
        # Setup monitoring and metrics
        print(f"🚀 {SERVICE_TITLE} v{SERVICE_VERSION} started successfully")
        print("📊 Architecture: Domain-Driven Design with CQRS")
        print(f"🔧 Controllers: {len(controllers)} registered")
        print("✨ Clean Architecture: Domain ← Application ← Infrastructure ← Presentation")

    # ============================================================================
    # SHUTDOWN EVENT - Cleanup resources
    # ============================================================================
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup resources on shutdown."""
        # Close database connections
        # Cleanup external service connections
        # Flush caches and metrics
        print(f"🛑 {SERVICE_TITLE} shutting down gracefully")

    return app


# ============================================================================
# APPLICATION FACTORY - Create the FastAPI application
# ============================================================================
app = create_application()


# ============================================================================
# DEVELOPMENT SERVER - For local development and testing
# ============================================================================
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", DEFAULT_PORT))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"🎯 Starting {SERVICE_TITLE} on {host}:{port}")
    print("📚 API Documentation: http://localhost:{port}/docs")
    print("🔄 Alternative Docs: http://localhost:{port}/redoc")

    uvicorn.run(
        "main_new:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )


# ============================================================================
# SERVICE METADATA - For service discovery and monitoring
# ============================================================================
SERVICE_METADATA = {
    "name": SERVICE_NAME,
    "title": SERVICE_TITLE,
    "version": SERVICE_VERSION,
    "description": "Document analysis and consistency checking service",
    "architecture": "Domain-Driven Design with CQRS and Clean Architecture",
    "endpoints": 50,
    "controllers": 9,
    "features": [
        "Advanced document analysis",
        "Distributed processing",
        "Workflow integration",
        "Cross-repository analysis",
        "Automated remediation",
        "Real-time monitoring"
    ],
    "dependencies": [
        "Document Store",
        "Prompt Store",
        "Interpreter",
        "Source Agent",
        "Orchestrator"
    ]
}
