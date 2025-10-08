# MCP Base Image - Minimal FastAPI server for MCP instances

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

# Create minimal MCP server
RUN echo 'from fastapi import FastAPI\n\
import os\n\
\n\
app = FastAPI()\n\
\n\
mcp_id = os.getenv("MCP_ID", "unknown")\n\
mcp_tier = os.getenv("MCP_TIER", "0")\n\
\n\
@app.get("/health")\n\
async def health():\n\
    return {"status": "healthy", "mcp_id": mcp_id, "tier": mcp_tier}\n\
\n\
@app.post("/api/query")\n\
async def query(body: dict):\n\
    query_text = body.get("query", "")\n\
    return {\n\
        "mcp_id": mcp_id,\n\
        "query": query_text,\n\
        "answer": f"This is MCP {mcp_id} (tier {mcp_tier}) responding to: {query_text}. This MCP has been trained on documentation and can provide contextual answers.",\n\
        "confidence": 0.95,\n\
        "sources": ["training_documents"]\n\
    }\n\
\n\
@app.get("/")\n\
async def root():\n\
    return {"mcp_id": mcp_id, "tier": mcp_tier, "status": "running"}\n\
' > /app/main.py

EXPOSE 8080
EXPOSE 3000

# Use MCP_PORT environment variable or default to 8080
CMD python -m uvicorn main:app --host 0.0.0.0 --port ${MCP_PORT:-8080}

