"""
FastAPI application factory.

Creates REST API with OpenAPI/Swagger documentation.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ..config import settings
from ..storage import init_database, close_database, init_chroma, close_chroma
from ..utils import init_redis, close_redis

from .routes import health, admin, search, documents, query, logs, ollama

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown of services.
    """
    # Startup
    logger.info("=" * 80)
    logger.info("ECOSYSTEM MCP SERVICE STARTING")
    logger.info("=" * 80)
    
    # Run preflight checks
    logger.info("\n🔍 Running preflight checks...")
    from ..utils.preflight import run_preflight_checks
    try:
        await run_preflight_checks(fail_fast=True)
    except RuntimeError as e:
        # Preflight checks failed, already logged
        logger.error(f"Preflight check error: {e}")
        raise
    
    logger.info("\n🚀 Initializing services...")
    try:
        await init_database()
        logger.info("  ✅ Database initialized")
        
        await init_chroma()
        logger.info("  ✅ ChromaDB initialized")
        
        await init_redis()
        logger.info("  ✅ Redis initialized")
        
        logger.info("\n✅ ALL SERVICES INITIALIZED SUCCESSFULLY")
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"\n❌ Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("\n" + "=" * 80)
    logger.info("SHUTTING DOWN SERVICES")
    logger.info("=" * 80)
    await close_redis()
    logger.info("  ✅ Redis closed")
    await close_chroma()
    logger.info("  ✅ ChromaDB closed")
    await close_database()
    logger.info("  ✅ Database closed")
    logger.info("✅ SHUTDOWN COMPLETE")
    logger.info("=" * 80)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Ecosystem MCP Service",
        description="""
        Intelligent refactoring knowledge base with MCP integration.
        
        Provides:
        - Semantic search across documentation
        - Pattern recognition and suggestions
        - Cost-tracked AI model access
        - Complete ingestion pipeline
        
        ## Interfaces
        
        - **MCP Protocol**: AI agent access via stdio
        - **REST API**: Human/ops access via HTTP
        
        ## Features
        
        - Multi-model routing (Ollama, Claude, Cursor)
        - Document versioning with git integration
        - Fault-tolerant ingestion pipeline
        - Real-time job monitoring
        """,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
    app.include_router(search.router, prefix="/api/v1", tags=["Search"])
    app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
    app.include_router(query.router, prefix="/api/v1/query", tags=["Query"])
    app.include_router(logs.router, prefix="/api/v1/logs", tags=["Logs"])
    app.include_router(ollama.router, prefix="/api/v1/ollama", tags=["Ollama"])
    
    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint with service info."""
        return {
            "service": "Ecosystem MCP",
            "version": "0.1.0",
            "status": "operational",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc)
            }
        )
    
    return app

