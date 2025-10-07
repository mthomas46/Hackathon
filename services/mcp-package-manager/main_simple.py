"""MCP Package Manager - Simple Working Version."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Settings
SERVICE_NAME = "mcp-package-manager"
SERVICE_PORT = 8103

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP Package Manager",
    description="Package Management for MCPs",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": SERVICE_NAME,
        "status": "running",
        "docs_url": "/docs"
    }


@app.get("/api/v1/packages")
async def list_packages():
    """List all packages."""
    return {
        "packages": [],
        "count": 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
