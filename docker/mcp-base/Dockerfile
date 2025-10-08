# MCP Base Image - Connects to doc_store for training data
# This is a production-ready MCP that queries actual training documents

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    httpx==0.25.2 \
    pydantic==2.5.0

# Create MCP server that queries doc_store for training documents
RUN echo 'from fastapi import FastAPI, HTTPException\n\
import os\n\
import httpx\n\
import logging\n\
import asyncio\n\
from typing import Dict, Any, List, Optional\n\
\n\
logging.basicConfig(level=logging.INFO)\n\
logger = logging.getLogger(__name__)\n\
\n\
app = FastAPI(title="MCP Instance")\n\
\n\
# Configuration from environment\n\
mcp_id = os.getenv("MCP_ID", "unknown")\n\
mcp_tier = os.getenv("MCP_TIER", "0")\n\
doc_store_url = os.getenv("DOC_STORE_URL", "http://doc_store:5010")\n\
\n\
# Health check endpoint\n\
@app.get("/health")\n\
async def health():\n\
    """Health check endpoint for gateway monitoring."""\n\
    return {\n\
        "status": "healthy",\n\
        "mcp_id": mcp_id,\n\
        "tier": mcp_tier,\n\
        "doc_store": doc_store_url\n\
    }\n\
\n\
# Main query endpoint\n\
@app.post("/api/query")\n\
async def query(body: Dict[str, Any]):\n\
    """Query the MCP using training documents from doc_store."""\n\
    query_text = body.get("query", "")\n\
    max_results = body.get("max_results", 5)\n\
    \n\
    logger.info(f"MCP {mcp_id} received query: {query_text[:100]}...")\n\
    \n\
    try:\n\
        # Query doc_store for relevant training documents\n\
        async with httpx.AsyncClient(timeout=10.0) as client:\n\
            search_response = await client.post(\n\
                f"{doc_store_url}/api/v1/search",\n\
                json={\n\
                    "query": query_text,\n\
                    "limit": max_results\n\
                }\n\
            )\n\
            \n\
            if search_response.status_code == 200:\n\
                docs = search_response.json()\n\
                \n\
                if docs and len(docs) > 0:\n\
                    # Use actual document content from training data\n\
                    top_doc = docs[0]\n\
                    answer = top_doc.get("content", "No content available")\n\
                    sources = [d.get("source", "unknown") for d in docs[:3]]\n\
                    confidence = 0.85\n\
                    \n\
                    logger.info(f"✅ MCP {mcp_id} found {len(docs)} relevant documents")\n\
                else:\n\
                    # No documents found in training data\n\
                    answer = f"No relevant training documents found for query: {query_text}"\n\
                    sources = []\n\
                    confidence = 0.0\n\
                    logger.warning(f"⚠️ MCP {mcp_id} found no documents for query")\n\
            else:\n\
                # doc_store unavailable or error\n\
                answer = f"Document store unavailable (status {search_response.status_code}). Cannot access training documents."\n\
                sources = ["doc_store_error"]\n\
                confidence = 0.0\n\
                logger.error(f"❌ doc_store returned {search_response.status_code}")\n\
    \n\
    except httpx.ConnectError as e:\n\
        logger.error(f"❌ Cannot connect to doc_store at {doc_store_url}: {e}")\n\
        answer = f"Cannot connect to document store. MCP {mcp_id} cannot access training documents."\n\
        sources = ["connection_error"]\n\
        confidence = 0.0\n\
    \n\
    except httpx.TimeoutException as e:\n\
        logger.error(f"❌ Timeout querying doc_store: {e}")\n\
        answer = f"Document store timeout. Query took too long."\n\
        sources = ["timeout_error"]\n\
        confidence = 0.0\n\
    \n\
    except Exception as e:\n\
        logger.error(f"❌ Error querying doc_store: {e}", exc_info=True)\n\
        answer = f"Error accessing training documents: {str(e)}"\n\
        sources = ["error"]\n\
        confidence = 0.0\n\
    \n\
    return {\n\
        "mcp_id": mcp_id,\n\
        "query": query_text,\n\
        "answer": answer,\n\
        "confidence": confidence,\n\
        "sources": sources,\n\
        "tier": mcp_tier\n\
    }\n\
\n\
# Root endpoint\n\
@app.get("/")\n\
async def root():\n\
    """Root endpoint with MCP information."""\n\
    return {\n\
        "mcp_id": mcp_id,\n\
        "tier": mcp_tier,\n\
        "status": "running",\n\
        "doc_store": doc_store_url,\n\
        "endpoints": ["/health", "/api/query"]\n\
    }\n\
' > /app/main.py

EXPOSE 8080
EXPOSE 3000

# Use MCP_PORT environment variable or default to 8080
CMD python -m uvicorn main:app --host 0.0.0.0 --port ${MCP_PORT:-8080}
