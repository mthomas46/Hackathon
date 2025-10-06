"""Main FastAPI application for MCP Gateway Service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from services.mcp_gateway import __version__, __service_name__
from services.mcp_gateway.infrastructure.config.settings import get_settings
from services.mcp_gateway.infrastructure.repositories.redis_mcp_registry_repository import RedisMCPRegistryRepository
from services.mcp_gateway.infrastructure.health.health_checker import HealthChecker
from services.mcp_gateway.application.use_cases.update_health_use_case import UpdateHealthUseCase
from services.mcp_gateway.presentation.api.routes import gateway_router, health_router
from services.mcp_gateway.presentation import dependencies

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Global instances
redis_client: redis.Redis = None
registry_repository: RedisMCPRegistryRepository = None
health_checker: HealthChecker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info(f"Starting {__service_name__} v{__version__}")
    
    global redis_client, registry_repository, health_checker
    
    try:
        # Initialize Redis
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            socket_connect_timeout=settings.redis_socket_connect_timeout,
            socket_timeout=settings.redis_socket_timeout,
            decode_responses=False
        )
        await redis_client.ping()
        logger.info("Redis connection established")
        
        # Initialize repository
        registry_repository = RedisMCPRegistryRepository(redis_client, settings)
        logger.info("Registry repository initialized")
        
        # Initialize dependencies
        dependencies.init_dependencies(redis_client, registry_repository)
        logger.info("Dependencies initialized")
        
        # Start health checker
        if settings.health_check_enabled:
            update_health_use_case = UpdateHealthUseCase(registry_repository)
            health_checker = HealthChecker(
                registry_repository,
                update_health_use_case,
                settings
            )
            await health_checker.start()
            logger.info("Health checker started")
        
        logger.info(f"{__service_name__} startup complete")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise
    
    finally:
        # Shutdown
        logger.info(f"Shutting down {__service_name__}")
        
        # Stop health checker
        if health_checker:
            await health_checker.stop()
            logger.info("Health checker stopped")
        
        # Close Redis
        if redis_client:
            await redis_client.close()
            logger.info("Redis connection closed")
        
        logger.info(f"{__service_name__} shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="MCP Gateway Service",
    description="Single entry point for all MCP interactions with intelligent routing and load balancing",
    version=__version__,
    docs_url=settings.docs_url,
    openapi_url=settings.openapi_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(health_router)
app.include_router(gateway_router, prefix=settings.api_prefix)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": __service_name__,
        "version": __version__,
        "status": "operational",
        "docs": settings.docs_url
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_api_port,
        reload=settings.debug_mode,
        log_level=settings.log_level.lower()
    )

