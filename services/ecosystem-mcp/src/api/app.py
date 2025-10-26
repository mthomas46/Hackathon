"""
FastAPI application factory.

Creates REST API with OpenAPI/Swagger documentation.
"""

import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ..config import settings
from ..storage import init_database, close_database, init_chroma, close_chroma, get_database
from ..storage.chromadb_client import get_chroma_client
from ..utils import init_redis, close_redis
from ..utils.redis_client import get_redis_client
from ..utils.logging_config import configure_structured_logging
from ..utils.log_rotation import setup_log_rotation

from .routes import health, admin, search, documents, query, logs, ollama, metrics, standard, ask, ollama_status, infrastructure, containers, redis_admin, postgres_admin, diagnostics, config_viewer, embeddings_admin, job_recovery, path_resolver, temporal_versioning, documentation_runs, job_progress, performance_optimization, cache_analytics, discovery, discovery_admin, orchestration, documentation, timeline, temporal_rag, maintenance, reports, consolidation, dynamic_rag
from .routes import analysis as analysis_routes
# embeddings import moved below to handle conditional loading
from .middleware import RequestIDMiddleware, TimeoutMiddleware, MetricsMiddleware
from .exception_handlers import register_exception_handlers

logger = logging.getLogger(__name__)

# Global shutdown event
_shutdown_event: Optional[asyncio.Event] = None


def setup_signal_handlers(app: FastAPI):
    """
    Setup graceful shutdown signal handlers.
    
    Handles SIGTERM and SIGINT to ensure clean shutdown.
    """
    global _shutdown_event
    _shutdown_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        """Handle shutdown signals."""
        signal_name = "SIGTERM" if sig == signal.SIGTERM else "SIGINT"
        logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        
        if _shutdown_event:
            _shutdown_event.set()
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("Signal handlers registered for graceful shutdown")


async def cleanup_resources():
    """
    Cleanup all resources during shutdown.
    
    Ensures:
    - Database connections are closed
    - Redis connections are closed
    - ChromaDB connections are closed
    - Any in-flight operations complete
    """
    logger.info("Starting resource cleanup...")
    
    try:
        # Give in-flight requests time to complete (max 10 seconds)
        logger.info("Waiting for in-flight requests to complete...")
        await asyncio.sleep(2)  # Short grace period
        
        # Close database connections
        try:
            db = get_database()
            await db.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
        
        # Close Redis connections
        try:
            redis = get_redis_client()
            await redis.close()
            logger.info("Redis connections closed")
        except Exception as e:
            logger.error(f"Error closing Redis: {e}")
        
        # Close ChromaDB connections (best effort)
        try:
            chroma = get_chroma_client()
            # ChromaDB doesn't have explicit close, but we can release reference
            logger.info("ChromaDB connections released")
        except Exception as e:
            logger.warning(f"Error releasing ChromaDB: {e}")
        
        logger.info("Resource cleanup complete")
        
    except Exception as e:
        logger.error(f"Error during resource cleanup: {e}")


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
    
    # Setup signal handlers for graceful shutdown
    setup_signal_handlers(app)
    
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
        
        # Verify Redis persistence
        from ..utils.redis_persistence_checker import verify_redis_persistence
        redis_check = await verify_redis_persistence()
        if redis_check["warnings"]:
            for warning in redis_check["warnings"]:
                logger.warning(f"  ⚠️  Redis: {warning}")
        
        # Start ingestion worker
        from ..services.ingestion import get_ingestion_worker
        ingestion_worker = get_ingestion_worker()
        await ingestion_worker.start()
        logger.info("  ✅ Ingestion worker started")
        
        # 🆕 PHASE 2.2: Start retry worker
        from ..services.ingestion.retry_worker import get_retry_worker
        retry_worker = get_retry_worker()
        await retry_worker.start()
        logger.info("  ✅ Retry worker started")
        
        # Detect and handle orphaned jobs on startup
        # 🚨 TEMPORARILY DISABLED to prevent re-queuing actively processing jobs during debugging
        # TODO: Re-enable with improved logic (check worker heartbeat, progress updates)
        logger.info("  ⏭️  Orphaned job detection DISABLED (temporary)")
        # try:
        #     from ..services.ingestion.orphaned_job_detector import detect_orphaned_jobs
        #     orphan_result = await detect_orphaned_jobs()
        #     if orphan_result["orphaned_found"] > 0:
        #         logger.warning(
        #             f"  ⚠️  Orphaned jobs detected: {orphan_result['failed_old']} failed, "
        #             f"{orphan_result['requeued_recent']} re-queued, "
        #             f"{orphan_result['orphaned_found']} total orphaned"
        #         )
        #     else:
        #         logger.info("  ✅ No orphaned jobs detected")
        # except Exception as e:
        #     logger.error(f"  ❌ Orphaned job detection failed: {e}", exc_info=True)
        
        logger.info("\n✅ ALL SERVICES INITIALIZED SUCCESSFULLY")
        
        # Initialize metrics
        from ..utils.metrics import init_service_metrics
        init_service_metrics(version="0.1.0", environment=settings.environment)
        logger.info("  ✅ Metrics initialized")
        
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"\n❌ Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown - graceful cleanup
    logger.info("\n" + "=" * 80)
    logger.info("SHUTTING DOWN SERVICES")
    logger.info("=" * 80)
    
    # Stop ingestion worker
    try:
        from ..services.ingestion import get_ingestion_worker
        worker = get_ingestion_worker()
        await worker.stop()
        logger.info("  ✅ Ingestion worker stopped")
    except Exception as e:
        logger.error(f"Error stopping ingestion worker: {e}")
    
    # 🆕 PHASE 2.2: Stop retry worker
    try:
        from ..services.ingestion.retry_worker import get_retry_worker
        retry_worker = get_retry_worker()
        await retry_worker.stop()
        logger.info("  ✅ Retry worker stopped")
    except Exception as e:
        logger.error(f"Error stopping retry worker: {e}")
    
    # Use cleanup_resources for graceful shutdown
    await cleanup_resources()
    
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
    
    # Register exception handlers (includes rate limit handler)
    register_exception_handlers(app)
    
    # Middleware stack (order matters - last added = first executed)
    # 1. Metrics (outermost - tracks everything)
    app.add_middleware(MetricsMiddleware)
    
    # 2. Request timeout (applies to entire request)
    app.add_middleware(TimeoutMiddleware, default_timeout=120.0)  # Increased for LLM generation
    
    # 3. Request ID (for distributed tracing)
    app.add_middleware(RequestIDMiddleware)
    
    # Response compression for better performance
    from fastapi.middleware.gzip import GZipMiddleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB
    
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
    app.include_router(infrastructure.router, prefix="/api/v1", tags=["Infrastructure"])  # ✅ Infrastructure monitoring
    app.include_router(standard.router, tags=["Standard"])  # ✅ Standard ecosystem endpoints
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
    app.include_router(search.router, prefix="/api/v1", tags=["Search"])
    app.include_router(ask.router, prefix="/api/v1", tags=["RAG"])  # ✅ RAG question answering
    app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
    app.include_router(query.router, prefix="/api/v1", tags=["Query"])
    
    # Embeddings exploration and analysis (conditionally loaded)
    try:
        from .routes import embeddings
        app.include_router(embeddings.router, prefix="/api/v1/embeddings", tags=["Embeddings"])
    except ImportError:
        logger.warning("Embeddings module not available, skipping embeddings routes")
    
    # Enhanced query with mode and tier selection
    from .routes import query_enhanced
    app.include_router(query_enhanced.router, prefix="/api/v1", tags=["Enhanced Query"])
    
    # Multi-pass query processing
    from .routes import multi_pass
    app.include_router(multi_pass.router, prefix="/api/v1", tags=["Multi-Pass Query"])
    
    app.include_router(logs.router, prefix="/api/v1", tags=["Logs"])
    app.include_router(ollama.router, prefix="/api/v1", tags=["Ollama"])
    app.include_router(ollama_status.router, prefix="/api/v1", tags=["Ollama Status"])  # ✅ Ollama instance monitoring
    
    # Cache monitoring
    from .routes import cache_stats
    app.include_router(cache_stats.router, prefix="/api/v1", tags=["Monitoring"])
    
    # Container management
    app.include_router(containers.router, prefix="/api/v1", tags=["Containers"])
    
    # Database administration
    app.include_router(redis_admin.router, prefix="/api/v1", tags=["Redis Admin"])
    app.include_router(postgres_admin.router, prefix="/api/v1", tags=["PostgreSQL Admin"])
    
    # Diagnostics and configuration
    app.include_router(diagnostics.router, prefix="/api/v1", tags=["Diagnostics"])
    app.include_router(config_viewer.router, prefix="/api/v1", tags=["Configuration"])
    
    # Worker management and health monitoring
    from .routes import workers
    app.include_router(workers.router, prefix="/api/v1/admin", tags=["Workers"])
    
    # Performance optimization
    app.include_router(performance_optimization.router, prefix="/api/v1/admin", tags=["Performance"])
    
    # Phase 4: Cache analytics
    app.include_router(cache_analytics.router, prefix="/api/v1/admin", tags=["Cache Analytics"])
    
    # Ingestion log streaming
    from .routes import ingestion_logs
    app.include_router(ingestion_logs.router, prefix="/api/v1/admin", tags=["Ingestion Logs"])
    
    # Embeddings administration
    app.include_router(embeddings_admin.router, prefix="/api/v1/admin", tags=["Embeddings"])
    
    # Job recovery and checkpoints
    app.include_router(job_recovery.router, prefix="/api/v1", tags=["Job Recovery"])
    
    # Real-time job progress tracking
    app.include_router(job_progress.router, prefix="/api/v1/admin", tags=["Job Progress"])
    
    # Path resolution for host machine paths
    app.include_router(path_resolver.router, prefix="/api/v1/path", tags=["Path Resolution"])
    
    # Temporal versioning and timeline queries
    app.include_router(temporal_versioning.router, prefix="/api/v1/versioning", tags=["Temporal Versioning"])
    
    # Timeline-based document analysis
    app.include_router(timeline.router, tags=["Timeline Analysis"])
    
    # Temporal RAG queries (Phase 2.1)
    app.include_router(temporal_rag.router, prefix="/api/v1/rag", tags=["Temporal RAG"])
    
    # Documentation maintenance (Phase 2.2)
    app.include_router(maintenance.router, prefix="/api/v1/maintenance", tags=["Documentation Maintenance"])
    
    # Advanced analysis features (Phase 3)
    app.include_router(analysis_routes.router, prefix="/api/v1/analysis", tags=["Advanced Analysis"])
    
    # Report generation (Phase 5.2)
    app.include_router(reports.router, tags=["Report Generation"])
    
    # Document consolidation (Phase 5.3)
    app.include_router(consolidation.router, tags=["Document Consolidation"])
    
    # Dynamic Temporal RAG (Phase 6)
    app.include_router(dynamic_rag.router, tags=["Dynamic Temporal RAG"])
    
    # Documentation run management
    app.include_router(documentation_runs.router, prefix="/api/v1/documentation", tags=["Documentation Runs"])
    
    # Discovery and processing plans (Phase 1)
    app.include_router(discovery.router, prefix="/api/v1", tags=["Discovery"])
    app.include_router(discovery_admin.router, prefix="/api/v1/admin", tags=["Discovery Admin"])
    
    # Orchestration and parallel execution (Phase 2)
    app.include_router(orchestration.router, prefix="/api/v1", tags=["Orchestration"])
    
    # Multi-pass documentation (Phase 4)
    app.include_router(documentation.router, prefix="/api/v1", tags=["Documentation"])
    
    app.include_router(metrics.router, tags=["Metrics"])
    
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
    
    return app

