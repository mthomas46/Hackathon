"""Main application entry point for llm-tagging-pipeline."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting llm-tagging-pipeline v1.0.0")
    
    # TODO: Initialize dependencies
    # - Ollama tagger
    # - Repositories
    # - Services
    
    yield
    
    logger.info("Shutting down llm-tagging-pipeline")
    
    # TODO: Cleanup
    # - Close Ollama client
    # - Close database connections


# Create FastAPI app
app = FastAPI(
    title="LLM Tagging Pipeline",
    description="Automated LLM-based document metadata extraction service",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "llm-tagging-pipeline",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "llm-tagging-pipeline",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5800,
        reload=True
    )

