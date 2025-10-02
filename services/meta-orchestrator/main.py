#!/usr/bin/env python3
"""
Meta-Orchestration Service
Manages the lifecycle and configuration of other services in the ecosystem
"""

import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import structlog

from api.routes import router
from core.orchestrator import MetaOrchestrator
from config.settings import Settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Meta-Orchestration Service",
    description="""
    Comprehensive service orchestration and configuration management system.

    **Core Features:**
    - Service lifecycle management (start, stop, restart)
    - Dynamic configuration modification
    - Real-time health monitoring
    - Configuration drift detection
    - Production readiness validation
    - Docker Compose validation
    - Automated conflict resolution

    **API Categories:**
    - **Service Management**: Control individual services
    - **Configuration**: Modify and validate configurations
    - **Monitoring**: Health checks and alerts
    - **Audit**: Comprehensive validation and drift detection
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Service Management",
            "description": "Operations for managing individual services"
        },
        {
            "name": "Configuration",
            "description": "Configuration modification and management"
        },
        {
            "name": "Monitoring",
            "description": "Health monitoring and alerts"
        },
        {
            "name": "Audit & Validation",
            "description": "Comprehensive audit, validation, and drift detection"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load settings
settings = Settings()

# Initialize meta-orchestrator (will be initialized in startup event)
meta_orchestrator = None

# Initialize monitoring service (will be initialized in startup event)
monitoring_service = None

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize the meta-orchestrator and monitoring service"""
    global meta_orchestrator, monitoring_service
    print("🚀 STARTUP EVENT CALLED - Starting Meta-Orchestration Service")
    logger.info("🚀 Starting Meta-Orchestration Service")
    try:
        # Initialize meta-orchestrator
        meta_orchestrator = MetaOrchestrator(settings)
        await meta_orchestrator.initialize()

        # Initialize monitoring service
        from monitoring.service import MonitoringService
        monitoring_service = MonitoringService(meta_orchestrator, db_path="/tmp/monitoring.db")
        await monitoring_service.initialize()

        # Start monitoring in background
        await monitoring_service.start_monitoring(
            drift_interval=300,    # 5 minutes
            health_interval=60,    # 1 minute
            analytics_interval=3600  # 1 hour
        )

        # Set the global instances in routes module
        import api.routes
        api.routes.meta_orchestrator = meta_orchestrator
        api.routes.monitoring_service = monitoring_service

        print("✅ Meta-Orchestrator and Monitoring Service initialization completed")
        logger.info("✅ Meta-Orchestrator and Monitoring Service initialization completed")
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        logger.error(f"❌ Service initialization failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        logger.error(f"Traceback: {traceback.format_exc()}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global monitoring_service
    logger.info("🛑 Shutting down Meta-Orchestration Service")

    if monitoring_service:
        await monitoring_service.stop_monitoring()
    await meta_orchestrator.cleanup()

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "meta-orchestrator",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Meta-Orchestration Service",
        "description": "Manages lifecycle and configuration of hackathon ecosystem services",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.service.debug,
        log_level=settings.service.log_level.lower()
    )
