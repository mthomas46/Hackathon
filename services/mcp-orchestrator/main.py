"""Main FastAPI application for MCP Orchestrator Service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from services.mcp_orchestrator import __version__, __service_name__
from services.mcp_orchestrator.infrastructure.config.settings import get_settings
from services.mcp_orchestrator.infrastructure.repositories.redis_workflow_repository import RedisWorkflowRepository
from services.mcp_orchestrator.presentation.api.routes import workflows_router, health_router
from services.mcp_orchestrator.presentation import dependencies

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
workflow_repository: RedisWorkflowRepository = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info(f"Starting {__service_name__} v{__version__}")
    
    global redis_client, workflow_repository
    
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
        
        # Initialize workflow repository
        workflow_repository = RedisWorkflowRepository(redis_client, settings)
        logger.info("Workflow repository initialized")
        
        # Initialize dependencies
        dependencies.init_dependencies(redis_client, workflow_repository)
        logger.info("Dependencies initialized")
        
        logger.info(f"{__service_name__} startup complete")
        logger.info(f"Max concurrent workflows: {settings.max_concurrent_workflows}")
        logger.info(f"Default strategy: {settings.default_execution_strategy}")
        logger.info(f"Patterns enabled: CoT={settings.enable_chain_of_thought}, "
                   f"Critique={settings.enable_self_critique}, "
                   f"Ensemble={settings.enable_ensemble}")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise
    
    finally:
        # Shutdown
        logger.info(f"Shutting down {__service_name__}")
        
        # Close Redis
        if redis_client:
            await redis_client.close()
            logger.info("Redis connection closed")
        
        logger.info(f"{__service_name__} shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="MCP Orchestrator Service",
    description="Orchestrates complex queries across multiple MCPs using 24 advanced LLM patterns",
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
app.include_router(workflows_router, prefix=settings.api_prefix)

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
            "llm_patterns": 24,
            "execution_strategies": 10,
            "workflow_states": 10,
        },
        "capabilities": [
            "intelligent_planning",
            "multi_mcp_orchestration",
            "pattern_based_execution",
            "result_aggregation",
            "approval_workflows",
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

