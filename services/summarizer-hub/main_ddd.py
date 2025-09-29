"""Summarizer Hub Service - DDD Architecture Main Application.

This is the main FastAPI application for the summarizer-hub service,
implemented using Domain-Driven Design (DDD) principles.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Add service root to path
service_root = Path(__file__).parent
sys.path.insert(0, str(service_root))

from presentation.routes import document_router, summarization_router
from shared.presentation.responses import create_error_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Summarizer Hub API",
    description="""
    AI-Powered Document Summarization and Analysis Service

    This API provides comprehensive document processing capabilities including:
    - Multi-format document summarization
    - Intelligent categorization and tagging
    - Peer review enhancement suggestions
    - Recommendation generation
    - Real-time analysis and insights

    **Key Features:**
    - RESTful API design with comprehensive OpenAPI documentation
    - Multiple AI provider support (OpenAI, Anthropic, etc.)
    - Configurable summarization strategies
    - Quality metrics and validation
    - Enterprise-grade error handling and logging

    **Supported Document Types:**
    - Text documents
    - Code repositories
    - Technical documentation
    - Business reports
    - Research papers
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(document_router)
app.include_router(summarization_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "summarizer-hub",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Summarizer Hub API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=create_error_response(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details=str(exc) if os.getenv("DEBUG", "false").lower() == "true" else None
        )
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_ddd:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
