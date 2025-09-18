"""Refactored Service: Doc Store

New architecture with domain-driven design and clean separation of concerns.
"""
from fastapi import FastAPI
from services.shared.core.config.config import load_yaml_config, get_config_value
from services.shared.utilities.utilities import setup_common_middleware, attach_self_register
from services.shared.monitoring.health import register_health_endpoints
from services.shared.utilities.error_handling import install_error_handlers
from services.shared.core.constants_new import ServiceNames

# Database initialization
from .db.schema import init_database

# API routes
from .api.routes import router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    # Load configuration
    _cfg = load_yaml_config("services/doc_store/config.yaml")

    # Create FastAPI app
    app = FastAPI(
        title="Doc Store Service",
        description="Document storage and analysis service with advanced features",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Setup common middleware
    setup_common_middleware(app)

    # Install error handlers
    install_error_handlers(app)

    # Register health endpoints
    register_health_endpoints(app, ServiceNames.DOC_STORE)

    # Attach self-registration
    attach_self_register(app, ServiceNames.DOC_STORE)

    # Initialize database
    @app.on_event("startup")
    async def startup_event():
        """Initialize service on startup."""
        init_database()

    # Include API routes
    app.include_router(router)

    return app


# Create global app instance for backward compatibility
app = create_app()


if __name__ == "__main__":
    import uvicorn

    # Load config for port
    _cfg = load_yaml_config("services/doc_store/config.yaml")
    port = get_config_value("port", 5000, section="doc_store", env_key="DOCSTORE_PORT")

    uvicorn.run(
        "services.doc_store.main_refactored:app",
        host="0.0.0.0",
        port=int(port),
        reload=True
    )
