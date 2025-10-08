"""Kafka Ingestion Service - Simple Working Version."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import httpx
import os

# Settings
SERVICE_NAME = "kafka-ingestion-service"
SERVICE_PORT = 5700
DOC_STORE_URL = os.getenv("DOC_STORE_URL", "http://doc_store:5010")

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
    doc_id = document.get('document_id') or document.get('doc_id', 'unknown')
    logger.info(f"Ingesting document: {doc_id}")
    
    # Send to doc_store
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Prepare document payload for doc_store
            # Note: doc_store expects content and optional metadata/id
            doc_payload = {
                "content": document.get("content", ""),
                "metadata": {
                    "title": document.get("title", doc_id),
                    "source_url": document.get("source_url", ""),
                    "tags": document.get("tags", []),
                    "categories": document.get("categories", []),
                    "correlation_id": document.get("correlation_id", ""),
                    **document.get("metadata", {})
                }
            }
            
            # Add custom ID if provided (optional - doc_store will auto-generate if not provided)
            if doc_id and doc_id != "unknown":
                doc_payload["id"] = doc_id
            
            logger.info(f"Sending document {doc_id} to doc_store at {DOC_STORE_URL}")
            
            response = await client.post(
                f"{DOC_STORE_URL}/api/v1/documents",
                json=doc_payload
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Successfully sent document {doc_id} to doc_store")
                doc_store_success = True
            else:
                logger.error(f"❌ doc_store returned {response.status_code}: {response.text[:200]}")
                doc_store_success = False
                
    except Exception as e:
        logger.error(f"❌ Failed to send to doc_store: {e}")
        doc_store_success = False
    
    return {
        "status": "success",
        "message": "Document ingested",
        "doc_id": doc_id,
        "job_id": "job_123",
        "doc_store_sent": doc_store_success
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
