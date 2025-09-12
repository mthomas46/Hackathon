"""Service: Code Analyzer

Endpoints:
- POST /analyze/text, /analyze/files, /analyze/patch, /scan/secure
- POST /style/examples, GET /style/examples, GET /health

Responsibilities: Extract endpoints from code; manage style examples; optional doc-store writes.
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

app = FastAPI(title="Code Analyzer", version="0.1.0")
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name="code-analyzer")

# Rate limit heavy endpoints if enabled via environment toggle
if (os.environ.get("RATE_LIMIT_ENABLED", "").strip().lower() in ("1", "true", "yes")):
    app.add_middleware(
        RateLimitMiddleware,
        limits={
            "/analyze/files": (5.0, 10),
            "/analyze/patch": (5.0, 10),
            "/analyze/text": (10.0, 20),
            "/style/examples": (2.0, 5),
        },
    )

attach_self_register(app, "code-analyzer")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "code-analyzer"}


# Endpoint extraction logic moved to modules/endpoint_extractor.py


class AnalyzeTextRequest(BaseModel):
    content: str
    repo: Optional[str] = None
    path: Optional[str] = None
    correlation_id: Optional[str] = None
    language: Optional[str] = None
    style_examples: Optional[List[Dict[str, Any]]] = None


@app.post("/analyze/text")
async def analyze_text(req: AnalyzeTextRequest):
    """Analyze text content for endpoints and patterns."""
    result = process_text_analysis(
        content=req.content,
        repo=req.repo,
        path=req.path,
        correlation_id=req.correlation_id,
        language=req.language,
        style_examples=req.style_examples
    )

    # Persist result to external services
    await persist_analysis_result(result)

    return result


class FileItem(BaseModel):
    path: str
    content: str


class AnalyzeFilesRequest(BaseModel):
    files: List[FileItem]
    repo: Optional[str] = None
    correlation_id: Optional[str] = None
    language: Optional[str] = None
    style_examples: Optional[List[Dict[str, Any]]] = None


@app.post("/analyze/files")
async def analyze_files(req: AnalyzeFilesRequest):
    """Analyze multiple files for endpoints and patterns."""
    result = process_files_analysis(
        files=req.files,
        repo=req.repo,
        correlation_id=req.correlation_id,
        language=req.language,
        style_examples=req.style_examples
    )

    # Persist result to external services
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5085)


