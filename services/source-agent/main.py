"""Service: Source Agent

Endpoints:
- POST /docs/fetch: Fetch documents from GitHub, Jira, or Confluence sources
- POST /normalize: Normalize data from specified source with proper formatting
- POST /code/analyze: Analyze code for API endpoints and patterns
- GET /sources: List supported sources and their capabilities
- GET /health: Service health check

Responsibilities:
- Consolidate GitHub, Jira, and Confluence agent functionality into a single service
- Fetch and normalize documents from various enterprise sources
- Analyze code for API endpoints and architectural patterns
- Provide secure data handling with validation and sanitization
- Support correlation tracking for distributed operations

Dependencies: shared utilities, httpx for HTTP requests, Atlassian SDK, GitHub API.
"""
from typing import Optional, List
import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

# ============================================================================
# SHARED MODULES - Optimized import consolidation for consistency
# ============================================================================
from services.shared.monitoring.health import register_health_endpoints
from services.shared.core.responses.responses import create_success_response, create_error_response
from services.shared.utilities.error_handling import ValidationException, ServiceException
from services.shared.core.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import utc_now, generate_id, clean_string


from services.shared.utilities.error_handling import safe_execute_async

try:
    import redis.asyncio as aioredis
except Exception:
    aioredis = None

from services.shared.core.models.models import Document
from services.shared.utilities import stable_hash, cached_get
from services.shared.envelopes import DocumentEnvelope
from services.shared.owners import derive_github_owners
from services.shared.integrations.clients.clients import ServiceClients  # type: ignore

# Service configuration constants
SERVICE_NAME = "source-agent"
SERVICE_TITLE = "Source Agent"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5000

# Supported sources and their capabilities
SUPPORTED_SOURCES = ["github", "jira", "confluence"]
SOURCE_CAPABILITIES = {
    "github": ["readme_fetch", "pr_normalization", "code_analysis"],
    "jira": ["issue_normalization"],
    "confluence": ["page_normalization"]
}
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
from .modules.models import DocumentRequest, NormalizationRequest, CodeAnalysisRequest, ArchitectureProcessRequest
from .modules.fetch_handler import fetch_handler
from .modules.normalize_handler import normalize_handler
from .modules.code_analyzer import code_analyzer

# Create FastAPI app directly using shared utilities
app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Unified source agent for fetching and normalizing documents from GitHub, Jira, and Confluence"
)

# Use common middleware setup to reduce duplication across services
from services.shared.utilities import setup_common_middleware, attach_self_register
from services.shared.utilities.error_handling import install_error_handlers
from services.shared.core.constants_new import ServiceNames
setup_common_middleware(app, ServiceNames.SOURCE_AGENT)
install_error_handlers(app)

# Auto-register with orchestrator
attach_self_register(app, ServiceNames.SOURCE_AGENT)




# API Endpoints

@app.post("/docs/fetch")
async def fetch_document(req: DocumentRequest):
    """Fetch document from specified source using handler modules.

    Supports fetching documents from GitHub (READMEs, PRs), Jira (issues),
    and Confluence (pages). Uses appropriate authentication and data
    transformation for each source type.
    """
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
    """Normalize data from specified source using handler modules.

    Applies source-specific normalization rules to standardize data format,
    clean content, and extract structured information from raw source data.
    """
    return normalize_handler.normalize_data(req.source, req.data, req.correlation_id)


@app.post("/architecture/process")
async def process_architecture(req: ArchitectureProcessRequest):
    """Process architectural diagrams using the architecture-digitizer service.

    Forwards diagram processing requests to the architecture-digitizer service
    for normalization into standardized JSON schema.
    """
    try:
        from services.shared.utilities import get_service_client

        client = get_service_client()

        # Forward request to architecture-digitizer
        result = await client.post_json("architecture-digitizer/normalize", {
            "system": req.system,
            "board_id": req.board_id,
            "token": req.token
        })

        context = build_source_agent_context("architecture_process", system=req.system)
        return create_source_agent_success_response("processed", result, **context)

    except Exception as e:
        context = build_source_agent_context("architecture_process", system=req.system)
        return handle_source_agent_error("process architecture", e, **context)


@app.post("/code/analyze")
async def analyze_code(req: CodeAnalysisRequest):
    """Analyze code for API endpoints and patterns using handler modules.

    Performs static analysis on code to identify API endpoints, architectural
    patterns, and potential integration points across different frameworks.
    """
    return code_analyzer.analyze_code(req.text)


# ============================================================================
# HEALTH AND INFO ENDPOINTS - Using shared utilities for consistency
# ============================================================================

# Register standardized health endpoints
register_health_endpoints(app, ServiceNames.SOURCE_AGENT, "1.0.0")

@app.get("/sources")
async def list_sources():
    """List supported sources and their capabilities.

    Returns information about all supported source types (GitHub, Jira, Confluence)
    and their specific capabilities for fetching, normalization, and analysis.
    """
    try:
        sources_data = {
            "sources": SUPPORTED_SOURCES,
            "capabilities": SOURCE_CAPABILITIES
        }

        context = build_source_agent_context("list_sources")
        context = {k: v for k, v in context.items() if k != "operation"}
        return create_source_agent_success_response("sources retrieved", sources_data, **context)

    except Exception as e:
        context = build_source_agent_context("list_sources")
        context = {k: v for k, v in context.items() if k != "operation"}
        return handle_source_agent_error("list sources", e, **context)


if __name__ == "__main__":
    """Run the Source Agent service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )
