"""MCP Logs - Main Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.config.settings import Settings
from presentation.api import (
    log_router,
    stream_router,
    anomaly_router,
    alert_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Settings
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    logger.info(f"Elasticsearch: {settings.elasticsearch_host}:{settings.elasticsearch_port}")
    logger.info(f"Anomaly detection: {'enabled' if settings.anomaly_detection_enabled else 'disabled'}")
    
    yield
    
    logger.info("Shutting down")


# Create FastAPI app
app = FastAPI(
    title="MCP Logs",
    description="Centralized Logging & Observability Platform",
    version=settings.service_version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(log_router)
app.include_router(stream_router)
app.include_router(anomaly_router)
app.include_router(alert_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "description": "Centralized Logging & Observability",
        "status": "operational",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "elasticsearch": f"{settings.elasticsearch_host}:{settings.elasticsearch_port}",
        "anomaly_detection": settings.anomaly_detection_enabled,
        "alerting": settings.alerting_enabled,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
    )

