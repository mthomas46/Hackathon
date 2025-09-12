"""Consolidated Source Agent Service.

Combines GitHub, Jira, and Confluence agent functionality into a single service.
"""
from typing import Optional, List
import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

# ============================================================================
# SHARED MODULES - Optimized import consolidation for consistency
# ============================================================================
from services.shared.health import register_health_endpoints
from services.shared.responses import create_success_response, create_error_response
from services.shared.error_handling import ValidationException, ServiceException
from services.shared.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import utc_now, generate_id, clean_string


def sanitize_for_response(text: str) -> str:
    """Sanitize text to prevent XSS attacks in JSON responses."""
    if not text:
        return ""

    # Remove HTML tags
    import re
    text = re.sub(r'<[^>]+>', '', text)

    # Remove dangerous JavaScript event handlers and attributes
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)

    # Remove quotes that could be used to break out of attributes
    text = text.replace('"', '').replace("'", '')

    return clean_string(text)
from services.shared.error_handling import safe_execute_async

try:
    import redis.asyncio as aioredis
except Exception:
    aioredis = None

from services.shared.models import Document
from services.shared.utilities import stable_hash, cached_get
from services.shared.envelopes import DocumentEnvelope
from services.shared.owners import derive_github_owners
from services.shared.clients import ServiceClients  # type: ignore
from .modules.document_builders import (
    build_readme_doc,
    extract_endpoints_from_patch,
    build_jira_doc,
    storage_html_to_text,
    build_confluence_doc
)

# ============================================================================
# SHARED UTILITIES - Leveraging centralized functionality across modules
# ============================================================================
from .modules.shared_utils import (
    sanitize_for_response,
    handle_source_agent_error,
    create_source_agent_success_response,
    build_source_agent_context,
    extract_endpoints_from_code,
    build_github_url
)

# ============================================================================
# HANDLER MODULES - Extracted business logic
# ============================================================================
from .modules.models import DocumentRequest, NormalizationRequest, CodeAnalysisRequest
from .modules.fetch_handler import fetch_handler
from .modules.normalize_handler import normalize_handler
from .modules.code_analyzer import code_analyzer

# Create FastAPI app directly using shared utilities
app = FastAPI(title="Source Agent", version="1.0.0")

# Use common middleware setup to reduce duplication across services
from services.shared.utilities import setup_common_middleware, attach_self_register
from services.shared.error_handling import install_error_handlers
from services.shared.constants_new import ServiceNames
setup_common_middleware(app, ServiceNames.SOURCE_AGENT)
install_error_handlers(app)

# Auto-register with orchestrator
attach_self_register(app, ServiceNames.SOURCE_AGENT)




# API Endpoints

@app.post("/docs/fetch")
async def fetch_document(req: DocumentRequest):
    """Fetch document from specified source using handler modules."""
    if req.source == "github":
        # Extract owner and repo for GitHub
        owner, repo = req.identifier.split(":", 1)
        return await fetch_handler.fetch_github_document(owner, repo, req)

    elif req.source == "jira":
        return await fetch_handler.fetch_jira_document(req)

    elif req.source == "confluence":
        return await fetch_handler.fetch_confluence_document(req)


@app.post("/normalize")
async def normalize_data(req: NormalizationRequest):
    """Normalize data from specified source using handler modules."""
    return normalize_handler.normalize_data(req.source, req.data, req.correlation_id)


@app.post("/code/analyze")
async def analyze_code(req: CodeAnalysisRequest):
    """Analyze code for API endpoints and patterns using handler modules."""
    return code_analyzer.analyze_code(req.text)


# ============================================================================
# HEALTH AND INFO ENDPOINTS - Using shared utilities for consistency
# ============================================================================

# Register standardized health endpoints
register_health_endpoints(app, ServiceNames.SOURCE_AGENT, "1.0.0")

@app.get("/sources")
async def list_sources():
    """List supported sources using shared utilities."""
    try:
        sources_data = {
            "sources": ["github", "jira", "confluence"],
            "capabilities": {
                "github": ["readme_fetch", "pr_normalization", "code_analysis"],
                "jira": ["issue_normalization"],
                "confluence": ["page_normalization"]
            }
        }

        context = build_source_agent_context("list_sources")
        context = {k: v for k, v in context.items() if k != "operation"}
        return create_source_agent_success_response("sources retrieved", sources_data, **context)

    except Exception as e:
        context = build_source_agent_context("list_sources")
        context = {k: v for k, v in context.items() if k != "operation"}
        return handle_source_agent_error("list sources", e, **context)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
