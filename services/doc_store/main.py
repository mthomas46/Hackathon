"""Doc Store Service - Refactored Domain-Driven Architecture

A comprehensive document storage and analysis service with advanced features
for document management, search, analytics, and lifecycle operations.
"""

from fastapi import FastAPI

# ============================================================================
# SHARED INFRASTRUCTURE - Core service setup
# ============================================================================
from services.shared.config import load_yaml_config, get_config_value
from services.shared.utilities import setup_common_middleware, attach_self_register
from services.shared.health import register_health_endpoints
from services.shared.error_handling import install_error_handlers
from services.shared.constants_new import ServiceNames

# ============================================================================
# NEW DOMAIN-DRIVEN ARCHITECTURE - Clean separation of concerns
# ============================================================================
from .db.schema import init_database
from .infrastructure.cache import docstore_cache
from .api.routes import router as api_router

# ============================================================================
# FASTAPI APPLICATION - Clean and minimal
# ============================================================================
app = FastAPI(
    title="Doc Store Service",
    description="Document storage and analysis service with advanced features",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup shared middleware and utilities
setup_common_middleware(app)
install_error_handlers(app)
register_health_endpoints(app, ServiceNames.DOC_STORE)
attach_self_register(app, ServiceNames.DOC_STORE)

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

# ============================================================================
# MAIN ENTRY POINT - Clean service startup
# ============================================================================
if __name__ == "__main__":
    """Run the Doc Store service directly."""
    import uvicorn
    
    # Load port from configuration
    port = get_config_value("port", 5000, section="doc_store", env_key="DOCSTORE_PORT")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(port),
        log_level="info"
    )
