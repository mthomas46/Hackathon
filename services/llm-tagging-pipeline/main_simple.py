"""LLM Tagging Pipeline - Simple Working Version."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Settings
SERVICE_NAME = "llm-tagging-pipeline"
SERVICE_PORT = 8021

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LLM Tagging Pipeline",
    description="Automated Document Tagging with LLMs",
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


@app.post("/api/v1/tagging/tag")
async def tag_document(document: dict):
    """Tag a document."""
    logger.info(f"Tagging document: {document.get('doc_id', 'unknown')}")
    return {
        "status": "success",
        "doc_id": document.get("doc_id"),
        "tags": ["api", "documentation", "technical"],
        "summary": "This is a sample document summary."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
