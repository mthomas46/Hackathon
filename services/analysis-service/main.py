"""Analysis Service - Simplified FastAPI Application.

A basic analysis service for documentation quality assessment.
Simplified version to avoid complex DDD dependencies and shared module issues.
"""

import os
import sys
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Use fallback implementations for standalone operation
print("Starting simplified analysis service (standalone mode)")

def create_success_response(data):
    """Create standardized success response."""
    return {"success": True, "data": data}

def load_service_config(service_type, **kwargs):
    """Fallback config loader."""
    return type('Config', (), {
        'port': 5020,
        'service_name': service_type,
        'service_version': '1.0.0',
        'service_description': f'{service_type} service',
        'server': type('Server', (), {'host': '0.0.0.0', 'port': 5020})()
    })()

# Create FastAPI app
app = FastAPI(
    title="Analysis Service",
    description="Document analysis and quality assessment service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Load configuration
config = load_service_config("analysis-service")
SERVICE_NAME = config.service_name
SERVICE_VERSION = config.service_version

# Basic health endpoint
@app.get("/health")
async def health():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "Analysis service is operational"
    }

# Basic analysis endpoint
class AnalysisRequest(BaseModel):
    text: str
    analysis_type: Optional[str] = "quality"

class AnalysisResponse(BaseModel):
    success: bool
    analysis_type: str
    score: float
    recommendations: list[str]

@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_document(request: AnalysisRequest):
    """Basic document analysis endpoint."""
    # Simple mock analysis - in a real implementation this would use ML models
    score = 0.85 if len(request.text) > 100 else 0.65
    recommendations = []

    if len(request.text) < 50:
        recommendations.append("Document is too short for thorough analysis")
    if "error" in request.text.lower():
        recommendations.append("Document contains error references")
    if score < 0.7:
        recommendations.append("Consider expanding document content")

    return AnalysisResponse(
        success=True,
        analysis_type=request.analysis_type,
        score=score,
        recommendations=recommendations
    )

@app.get("/api/v1/status")
async def service_status():
    """Get service status and capabilities."""
    return create_success_response({
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "capabilities": ["document_analysis", "quality_assessment"],
        "status": "operational"
    })

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", "5020"))
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    print(f"Starting {SERVICE_NAME} on {host}:{port}")
    uvicorn.run(app, host=host, port=port)