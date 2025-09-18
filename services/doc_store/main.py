"""Doc Store Service - Refactored Domain-Driven Architecture

A comprehensive document storage and analysis service with advanced features
for document management, search, analytics, and lifecycle operations.
"""

from fastapi import FastAPI

# ============================================================================
# SHARED INFRASTRUCTURE - Core service setup
# ============================================================================
from services.shared.core.config.config import load_yaml_config, get_config_value
from services.shared.utilities.utilities import setup_common_middleware, attach_self_register
from services.shared.monitoring.health import register_health_endpoints
from services.shared.utilities.error_handling import install_error_handlers
from services.shared.core.constants_new import ServiceNames

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
setup_common_middleware(app, ServiceNames.DOC_STORE)
install_error_handlers(app)
health_manager = register_health_endpoints(app, ServiceNames.DOC_STORE)
attach_self_register(app, ServiceNames.DOC_STORE)

# Custom health endpoint with database_connected field
def check_database_connection():
    """Check if database is connected."""
    try:
        # Import here to avoid circular imports
        from .db.database import get_db
        # Try to get a database connection
        db = next(get_db())
        db.execute("SELECT 1")  # Simple query to test connection
        return True
    except Exception:
        return False

# Override the basic health method to include database_connected
original_basic_health = health_manager.basic_health
async def custom_basic_health():
    """Custom basic health with database_connected."""
    # Get the original health status
    health_status = await original_basic_health()

    # Convert to dict and add database_connected
    health_dict = {
        "status": health_status.status,
        "service": health_status.service,
        "version": health_status.version,
        "timestamp": health_status.timestamp.isoformat(),
        "uptime_seconds": health_status.uptime_seconds,
        "environment": health_status.environment,
        "database_connected": check_database_connection()
    }

    return health_dict

health_manager.basic_health = custom_basic_health

# Register custom health endpoints
from services.shared.monitoring.health import create_health_endpoint, create_system_health_endpoint, create_dependency_health_endpoint

app.get("/health")(create_health_endpoint(health_manager))
app.get("/health/system")(create_system_health_endpoint(health_manager))
app.get("/health/dependency/{service_name}")(create_dependency_health_endpoint(health_manager))

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
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(port),
        log_level="info"
    )
