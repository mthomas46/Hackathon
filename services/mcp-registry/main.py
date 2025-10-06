"""Main FastAPI application for MCP Registry Service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from services.mcp_registry import __version__, __service_name__
from services.mcp_registry.infrastructure.config.settings import get_settings
from services.mcp_registry.infrastructure.repositories.redis_registry_repository import RedisRegistryRepository
from services.mcp_registry.infrastructure.repositories.local_filesystem_storage_repository import LocalFilesystemStorageRepository
from services.mcp_registry.presentation.api.routes import registry_router, health_router
from services.mcp_registry.presentation import dependencies

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
registry_repository: RedisRegistryRepository = None
storage_repository: LocalFilesystemStorageRepository = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info(f"Starting {__service_name__} v{__version__}")
    
    global redis_client, registry_repository, storage_repository
    
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
        
        # Initialize repositories
        registry_repository = RedisRegistryRepository(redis_client, settings.redis_key_prefix)
        storage_repository = LocalFilesystemStorageRepository(settings.local_storage_path)
        logger.info("Repositories initialized")
        
        # Initialize dependencies
        dependencies.init_dependencies(redis_client, registry_repository, storage_repository)
        logger.info("Dependencies initialized")
        
        logger.info(f"{__service_name__} startup complete")
        logger.info(f"Storage backend: {settings.default_storage_backend}")
        logger.info(f"Export format: {settings.default_export_format}")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise
    
    finally:
        # Shutdown
        logger.info(f"Shutting down {__service_name__}")
        
        if redis_client:
            await redis_client.close()
            logger.info("Redis connection closed")
        
        logger.info(f"{__service_name__} shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="MCP Registry Service",
    description="Registry for MCP export, import, versioning, and storage management",
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
app.include_router(registry_router, prefix=settings.api_prefix)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": __service_name__,
        "version": __version__,
        "status": "operational",
        "docs": settings.docs_url,
        "features": {
            "export_formats": ["msgpack", "json", "compressed_tar", "zip", "docker_image"],
            "storage_backends": ["local_filesystem", "s3_compatible", "redis"],
            "versioning": "semantic (MAJOR.MINOR.PATCH)",
        },
        "capabilities": [
            "mcp_export",
            "mcp_import",
            "version_management",
            "registry_search",
            "integrity_verification",
            "security_scanning",
        ]
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

