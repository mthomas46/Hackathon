"""Service: Code Analyzer

Endpoints:
- POST /analyze/text: Analyze text content for API endpoints and patterns
- POST /analyze/files: Analyze multiple files for endpoints and patterns
- POST /analyze/patch: Analyze git patches for endpoint changes
- POST /scan/secure: Scan content for sensitive information and security issues
- POST /style/examples: Set programming style examples by language
- GET /style/examples: Retrieve style examples, optionally filtered by language
- GET /health: Service health check

Responsibilities:
- Extract API endpoints from various code formats (FastAPI, Flask, Express.js)
- Manage programming style examples for code quality assessment
- Perform security scanning for sensitive information
- Optional persistence to doc_store and Redis for analysis results

Dependencies: shared models/envelopes/hashutil, optional Redis, ServiceClients.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os

from services.shared.middleware import RequestIdMiddleware, RequestMetricsMiddleware, RateLimitMiddleware  # type: ignore
from services.shared.utilities import attach_self_register  # type: ignore

from .modules.analysis_processor import (
    process_text_analysis,
    process_files_analysis,
    process_patch_analysis
)
from .modules.security_scanner import scan_for_sensitive_content
from .modules.style_manager import style_manager
from .modules.persistence import persist_analysis_result

# Service configuration constants
SERVICE_NAME = "code-analyzer"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = 5085

# Rate limiting configuration (when enabled)
RATE_LIMITS = {
    "/analyze/files": (5.0, 10),  # 5 requests/second, burst of 10
    "/analyze/patch": (5.0, 10),  # 5 requests/second, burst of 10
    "/analyze/text": (10.0, 20),  # 10 requests/second, burst of 20
    "/style/examples": (2.0, 5),  # 2 requests/second, burst of 5
}

app = FastAPI(
    title="Code Analyzer",
    version=SERVICE_VERSION,
    description="Service for analyzing code to extract API endpoints, manage style examples, and perform security scanning"
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name=SERVICE_NAME)

# Rate limit heavy endpoints if enabled via environment toggle
rate_limit_enabled = os.environ.get("RATE_LIMIT_ENABLED", "").strip().lower() in ("1", "true", "yes")
if rate_limit_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        limits=RATE_LIMITS,
    )

attach_self_register(app, SERVICE_NAME)


@app.get("/health")
async def health():
    """Health check endpoint returning service status and basic information."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "rate_limiting": rate_limit_enabled,
        "description": "Code analyzer service is operational"
    }


# Endpoint extraction logic moved to modules/endpoint_extractor.py


class AnalyzeTextRequest(BaseModel):
    """Request model for text analysis endpoint.

    Used to analyze plain text content for API endpoints, patterns,
    and code quality assessment.
    """
    content: str
    """The text content to analyze for endpoints and patterns."""

    repo: Optional[str] = None
    """Repository identifier for source tracking."""

    path: Optional[str] = None
    """File path within the repository for source tracking."""

    correlation_id: Optional[str] = None
    """Unique identifier for request correlation across services."""

    language: Optional[str] = None
    """Programming language hint (e.g., 'python', 'javascript')."""

    style_examples: Optional[List[Dict[str, Any]]] = None
    """Custom style examples to use for code quality assessment."""


@app.post("/analyze/text")
async def analyze_text(req: AnalyzeTextRequest):
    """Analyze text content for API endpoints and coding patterns.

    Processes the provided text to extract API endpoints, analyze code patterns,
    and assess code quality based on configured style examples.
    """
    result = process_text_analysis(
        content=req.content,
        repo=req.repo,
        path=req.path,
        correlation_id=req.correlation_id,
        language=req.language,
        style_examples=req.style_examples
    )

    # Persist analysis result to external services (Redis/doc_store)
    await persist_analysis_result(result)

    return result


class FileItem(BaseModel):
    """Represents a single file with path and content for analysis."""
    path: str
    """File path relative to repository root."""
    content: str
    """Full text content of the file."""


class AnalyzeFilesRequest(BaseModel):
    """Request model for multi-file analysis endpoint.

    Used to analyze multiple files simultaneously for API endpoints
    and coding patterns across a codebase.
    """
    files: List[FileItem]
    """List of files to analyze."""

    repo: Optional[str] = None
    """Repository identifier for source tracking."""

    correlation_id: Optional[str] = None
    """Unique identifier for request correlation across services."""

    language: Optional[str] = None
    """Programming language hint for all files."""

    style_examples: Optional[List[Dict[str, Any]]] = None
    """Custom style examples to use for code quality assessment."""


@app.post("/analyze/files")
async def analyze_files(req: AnalyzeFilesRequest):
    """Analyze multiple files simultaneously for API endpoints and patterns.

    Processes a batch of files to extract endpoints, analyze code patterns,
    and provide consolidated analysis results across the entire codebase.
    """
    result = process_files_analysis(
        files=req.files,
        repo=req.repo,
        correlation_id=req.correlation_id,
        language=req.language,
        style_examples=req.style_examples
    )

    # Persist analysis result to external services (Redis/doc_store)
    await persist_analysis_result(result)

    return result


class AnalyzePatchRequest(BaseModel):
    patch: str
    repo: Optional[str] = None
    correlation_id: Optional[str] = None
    language: Optional[str] = None
    style_examples: Optional[List[Dict[str, Any]]] = None


@app.post("/analyze/patch")
async def analyze_patch(req: AnalyzePatchRequest):
    """Analyze git patch for endpoints and patterns."""
    result = process_patch_analysis(
        patch=req.patch,
        repo=req.repo,
        correlation_id=req.correlation_id,
        language=req.language,
        style_examples=req.style_examples
    )

    # Persist result to external services
    await persist_analysis_result(result)

    return result


class SecureScanRequest(BaseModel):
    content: str
    keywords: Optional[List[str]] = None


@app.post("/scan/secure")
async def scan_secure(req: SecureScanRequest):
    """Scan content for sensitive information and security vulnerabilities."""
    return scan_for_sensitive_content(req.content, req.keywords)


class StyleExample(BaseModel):
    language: str
    snippet: str
    title: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    tags: Optional[List[str]] = None


class StyleExamplesPayload(BaseModel):
    items: List[StyleExample]


@app.post("/style/examples")
async def set_style_examples(payload: StyleExamplesPayload):
    """Set style examples for programming languages."""
    # Convert to dict format for storage
    examples_data = [item.model_dump() for item in payload.items]

    # Add to style manager
    style_manager.add_examples(examples_data)

    # Persist to external storage
    style_manager.persist_examples(examples_data)

    return {"status": "ok", "languages": style_manager.languages}


@app.get("/style/examples")
async def get_style_examples(language: Optional[str] = None):
    """Get style examples, optionally filtered by language."""
    return style_manager.get_examples(language)


if __name__ == "__main__":
    """Run the Code Analyzer service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )


