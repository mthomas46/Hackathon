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

# Create MCP server that queries doc_store with semantic search support
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
app = FastAPI(title="MCP Instance with Semantic Search")\n\
\n\
# Configuration from environment\n\
mcp_id = os.getenv("MCP_ID", "unknown")\n\
mcp_tier = os.getenv("MCP_TIER", "0")\n\
doc_store_url = os.getenv("DOC_STORE_URL", "http://doc_store:5010")\n\
use_semantic = os.getenv("USE_SEMANTIC_SEARCH", "true").lower() == "true"\n\
semantic_weight = float(os.getenv("SEMANTIC_WEIGHT", "0.7"))\n\
\n\
# Health check endpoint\n\
@app.get("/health")\n\
async def health():\n\
    """Health check endpoint for gateway monitoring."""\n\
    return {\n\
        "status": "healthy",\n\
        "mcp_id": mcp_id,\n\
        "tier": mcp_tier,\n\
        "doc_store": doc_store_url,\n\
        "semantic_search_enabled": use_semantic,\n\
        "semantic_weight": semantic_weight\n\
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
        # Query doc_store with hybrid search (semantic + keyword)\n\
        async with httpx.AsyncClient(timeout=15.0) as client:\n\
            search_response = await client.post(\n\
                f"{doc_store_url}/api/v1/search?use_semantic={str(use_semantic).lower()}&semantic_weight={semantic_weight}",\n\
                json={\n\
                    "query": query_text,\n\
                    "limit": max_results\n\
                }\n\
            )\n\
            \n\
            if search_response.status_code == 200:\n\
                response_data = search_response.json()\n\
                \n\
                # Extract data and metadata from response\n\
                if isinstance(response_data, dict) and "data" in response_data:\n\
                    search_data = response_data["data"]\n\
                    docs = search_data.get("results", [])\n\
                    search_mode = search_data.get("search_mode", "unknown")\n\
                elif isinstance(response_data, dict):\n\
                    docs = response_data.get("items", [])\n\
                    search_mode = "legacy"\n\
                else:\n\
                    docs = response_data\n\
                    search_mode = "legacy"\n\
                \n\
                if docs and len(docs) > 0:\n\
                    # Use actual document content from training data\n\
                    top_doc = docs[0]\n\
                    answer = top_doc.get("content", "No content available")\n\
                    sources = [d.get("id", "unknown") for d in docs[:3]]\n\
                    \n\
                    # Use semantic similarity score if available, otherwise use combined score\n\
                    if "semantic_similarity" in top_doc:\n\
                        confidence = top_doc.get("semantic_similarity", 0.85)\n\
                    elif "score" in top_doc:\n\
                        confidence = top_doc.get("score", 0.85)\n\
                    else:\n\
                        confidence = 0.85\n\
                    \n\
                    logger.info(f"✅ MCP {mcp_id} found {len(docs)} documents via {search_mode} search, top score: {confidence:.2f}")\n\
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
        "tier": mcp_tier,\n\
        "semantic_search_used": use_semantic,\n\
        "semantic_weight": semantic_weight if use_semantic else 0.0\n\
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
        "semantic_search_enabled": use_semantic,\n\
        "semantic_weight": semantic_weight,\n\
        "search_mode": "hybrid" if use_semantic else "keyword",\n\
        "endpoints": ["/health", "/api/query"]\n\
    }\n\
' > /app/main.py

# Copy the mcp_response_generator.py file
COPY mcp_response_generator.py /app/mcp_response_generator.py

EXPOSE 8080
EXPOSE 3000

# Use MCP_PORT environment variable or default to 8080
CMD python -m uvicorn main:app --host 0.0.0.0 --port ${MCP_PORT:-8080}
