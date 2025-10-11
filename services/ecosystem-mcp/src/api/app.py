"""
FastAPI application factory.

Creates REST API with OpenAPI/Swagger documentation.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ..config import settings
from ..storage import init_database, close_database, init_chroma, close_chroma
from ..utils import init_redis, close_redis
from ..utils.logging_config import configure_structured_logging
from ..utils.log_rotation import setup_log_rotation

from .routes import health, admin, search, documents, query, logs, ollama
from .middleware import RequestIDMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown of services.
    """
    # Configure structured logging FIRST (before any logging calls)
    json_logs = settings.environment != "development"
    configure_structured_logging(
        log_level=settings.log_level,
        json_logs=json_logs,
        include_timestamp=True
    )
    
    # Add log rotation for persistent logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_handler = setup_log_rotation(
        log_file=log_dir / "mcp.log",
        max_bytes=10 * 1024 * 1024,  # 10MB
        backup_count=5,
        log_level=settings.log_level
    )
    logging.getLogger().addHandler(log_handler)
    
    logger.info("✅ Structured logging configured (JSON: %s)", json_logs)
    logger.info("✅ Log rotation configured (10MB, 5 backups)")
    
    # Startup
    logger.info("=" * 80)
    logger.info("ECOSYSTEM MCP SERVICE STARTING")
    logger.info("=" * 80)
    
    # Run preflight checks
    logger.info("\n🔍 Running preflight checks...")
    from ..utils.preflight import run_preflight_checks
    import os
    
    # Support lenient mode for development
    mode = os.getenv("PREFLIGHT_MODE", "strict")
    fail_fast = os.getenv("PREFLIGHT_FAIL_FAST", "false").lower() == "true"
    
    try:
        await run_preflight_checks(fail_fast=fail_fast, mode=mode)
    except Exception as e:
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
    # Initialize rate limiter
    limiter = Limiter(key_func=get_remote_address)
    
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
        
        ## Rate Limiting
        
        - Health endpoints: 60/minute
        - Query endpoints: 20/minute
        - Search endpoints: 10/minute
        - Admin endpoints: 5/minute
        """,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Attach rate limiter to app state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Request ID middleware (for distributed tracing)
    app.add_middleware(RequestIDMiddleware)
    
    # CORS middleware - Configured for security
    # In production, restrict origins to specific domains
    allowed_origins = [
        "http://localhost:3000",  # Local development (React/Next.js)
        "http://localhost:8000",  # API itself
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    # Add production origins from environment variable
    if settings.environment == "production":
        # Example: CORS_ORIGINS="https://app.example.com,https://dashboard.example.com"
        import os
        prod_origins = os.getenv("CORS_ORIGINS", "").split(",")
        allowed_origins.extend([o.strip() for o in prod_origins if o.strip()])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,  # ✅ FIXED: Specific origins only
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # ✅ FIXED: Specific methods
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],  # ✅ FIXED: Specific headers
        expose_headers=["X-Request-ID"],  # Expose request ID to clients
        max_age=600,  # Cache preflight requests for 10 minutes
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

