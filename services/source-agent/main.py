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

import os

from fastapi import FastAPI

from services.shared.infrastructure.config import load_service_config

# ============================================================================
# SHARED MODULES - Optimized import consolidation for consistency
# ============================================================================
from services.shared.monitoring.health import register_health_endpoints

try:
    import redis.asyncio as aioredis
except Exception:
    aioredis = None

from services.shared.integrations.clients.clients import ServiceClients  # type: ignore

# Load standardized configuration
config = load_service_config(
    service_type="source-agent",
    config_file="./config.yaml",  # Optional config file override
)

# Service configuration from standardized config
SERVICE_NAME = config.service_name
SERVICE_TITLE = config.service_description or "Source Agent"
SERVICE_VERSION = config.service_version
DEFAULT_PORT = int(os.environ.get("SERVICE_PORT", 5070))

# Supported sources and their capabilities
SUPPORTED_SOURCES = ["github", "jira", "confluence"]
SOURCE_CAPABILITIES = {
    "github": ["readme_fetch", "pr_normalization", "code_analysis"],
    "jira": ["issue_normalization"],
    "confluence": ["page_normalization"],
}
from .modules.code_analyzer import code_analyzer
from .modules.fetch_handler import fetch_handler

# ============================================================================
# HANDLER MODULES - Extracted business logic
# ============================================================================
from .modules.models import (
    ArchitectureProcessRequest,
    CodeAnalysisRequest,
    DocumentRequest,
    NormalizationRequest,
)
from .modules.normalize_handler import normalize_handler

# ============================================================================
# SHARED UTILITIES - Leveraging centralized functionality across modules
# ============================================================================
from .modules.shared_utils import (
    build_source_agent_context,
    create_source_agent_success_response,
    handle_source_agent_error,
)

# Create FastAPI app directly using shared utilities
app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Unified source agent for fetching and normalizing documents from GitHub, Jira, and Confluence",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Use common middleware setup to reduce duplication across services
from services.shared.utilities import attach_self_register, setup_common_middleware
from services.shared.utilities.error_handling import install_error_handlers

# Setup standardized middleware and utilities
setup_common_middleware(app, service_name=config.service_name)
install_error_handlers(app)

# Auto-register with orchestrator
attach_self_register(app, config.service_name)


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
        result = await client.post_json(
            "architecture-digitizer/normalize",
            {"system": req.system, "board_id": req.board_id, "token": req.token},
        )

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
register_health_endpoints(app, config.service_name, config.service_version)


@app.get("/sources")
async def list_sources():
    """List supported sources and their capabilities.

    Returns information about all supported source types (GitHub, Jira, Confluence)
    and their specific capabilities for fetching, normalization, and analysis.
    """
    try:
        sources_data = {
            "sources": SUPPORTED_SOURCES,
            "capabilities": SOURCE_CAPABILITIES,
        }

        context = build_source_agent_context("list_sources")
        context = {k: v for k, v in context.items() if k != "operation"}
        return create_source_agent_success_response(
            "sources retrieved", sources_data, **context
        )

    except Exception as e:
        context = build_source_agent_context("list_sources")
        context = {k: v for k, v in context.items() if k != "operation"}
        return handle_source_agent_error("list sources", e, **context)


if __name__ == "__main__":
    """Run the Source Agent service directly."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=DEFAULT_PORT, log_level="info")
