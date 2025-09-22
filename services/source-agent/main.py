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

from fastapi import FastAPI, HTTPException

from services.shared.core.constants_new import ServiceNames

# ============================================================================
# SHARED MODULES - Optimized import consolidation for consistency
# ============================================================================
from services.shared.monitoring.health import register_health_endpoints

try:
    import redis.asyncio as aioredis
except Exception:
    aioredis = None

import time

from services.shared.core.constants_new import ServiceNames
from services.shared.integrations.clients.clients import ServiceClients  # type: ignore
from services.shared.utilities.logging_client import get_log_collector_client

# Service configuration constants
SERVICE_NAME = "source-agent"
SERVICE_TITLE = "Source Agent"
SERVICE_VERSION = "1.0.0"
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
from .modules.models import ArchitectureProcessRequest, CodeAnalysisRequest, DocumentRequest, NormalizationRequest
from .modules.normalize_handler import normalize_handler

# ============================================================================
# SHARED UTILITIES - Leveraging centralized functionality across modules
# ============================================================================
from .modules.shared_utils import (
    build_source_agent_context,
    create_source_agent_success_response,
    handle_source_agent_error,
)

# Initialize log collector client
logger_client = None

# Create FastAPI app directly using shared utilities
app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Unified source agent for fetching and normalizing documents from GitHub, Jira, and Confluence",
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global logger_client
    try:
        # Use a fallback service name if SOURCE_AGENT doesn't exist in ServiceNames
        service_name = getattr(ServiceNames, "SOURCE_AGENT", SERVICE_NAME)
        logger_client = await get_log_collector_client(service_name)
        if logger_client:
            await logger_client.log_business_event(
                "source_agent_startup",
                {
                    "version": SERVICE_VERSION,
                    "capabilities": [
                        "document_fetching",
                        "data_normalization",
                        "code_analysis",
                        "source_integration",
                        "correlation_tracking",
                    ],
                    "integrations": ["github_api", "jira_api", "confluence_api", "log_collector", "doc_store"],
                    "supported_sources": ["github", "jira", "confluence"],
                    "features": [
                        "secure_data_handling",
                        "validation_sanitization",
                        "owner_derivation",
                        "caching_optimization",
                    ],
                },
            )
            await logger_client.log_info(
                "Source Agent service started",
                {
                    "supported_sources": ["github", "jira", "confluence"],
                    "document_fetching_enabled": True,
                    "normalization_engine_ready": True,
                    "code_analysis_available": True,
                },
            )
    except Exception as e:
        print(f"Failed to initialize log collector client: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if logger_client:
        try:
            await logger_client.log_info("Source Agent service shutting down")
        except Exception:
            pass


from services.shared.core.constants_new import ServiceNames

# Use common middleware setup to reduce duplication across services
from services.shared.utilities import attach_self_register, setup_common_middleware
from services.shared.utilities.error_handling import install_error_handlers

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
    start_time = time.time()
    request_id = f"source_fetch_{int(time.time() * 1000)}"

    try:
        # Log document fetch start
        if logger_client:
            await logger_client.log_business_event(
                "document_fetch_started",
                {
                    "request_id": request_id,
                    "source": req.source,
                    "identifier": req.identifier,
                    "document_type": req.doc_type,
                    "has_auth": bool(req.auth_token),
                    "include_metadata": req.include_metadata,
                    "fetch_operation": "single_document",
                },
            )

            await logger_client.log_info(
                "Starting document fetch from source",
                {
                    "request_id": request_id,
                    "source": req.source,
                    "identifier": req.identifier,
                    "document_type": req.doc_type,
                    "external_api_call": True,
                },
            )

        if req.source == "github":
            # Extract owner and repo for GitHub
            owner, repo = req.identifier.split(":", 1)

            # Log GitHub-specific details
            if logger_client:
                await logger_client.log_info(
                    "Fetching from GitHub repository",
                    {"request_id": request_id, "owner": owner, "repository": repo, "document_type": req.doc_type},
                )

            result = await fetch_handler.fetch_github_document(owner, repo, req)

        elif req.source == "jira":
            # Log Jira-specific details
            if logger_client:
                await logger_client.log_info(
                    "Fetching from Jira issue/ticket",
                    {"request_id": request_id, "jira_identifier": req.identifier, "document_type": req.doc_type},
                )

            result = await fetch_handler.fetch_jira_document(req)

        elif req.source == "confluence":
            # Log Confluence-specific details
            if logger_client:
                await logger_client.log_info(
                    "Fetching from Confluence page",
                    {"request_id": request_id, "confluence_identifier": req.identifier, "document_type": req.doc_type},
                )

            result = await fetch_handler.fetch_confluence_document(req)

        else:
            # Log unsupported source error
            error_time = time.time() - start_time
            if logger_client:
                await logger_client.log_error(
                    f"Document fetch failed: Unsupported source {req.source}",
                    {
                        "request_id": request_id,
                        "source": req.source,
                        "identifier": req.identifier,
                        "error_type": "unsupported_source",
                        "processing_time_seconds": error_time,
                    },
                    error=Exception(f"Unsupported source: {req.source}"),
                )

                await logger_client.log_business_event(
                    "document_fetch_failed",
                    {
                        "request_id": request_id,
                        "source": req.source,
                        "identifier": req.identifier,
                        "error_type": "unsupported_source",
                        "processing_time_seconds": error_time,
                    },
                )

            raise HTTPException(status_code=400, detail=f"Unsupported source: {req.source}")

        processing_time = time.time() - start_time

        # Calculate result metrics
        result_size = len(str(result)) if result else 0
        has_content = bool(result and result.get("content"))
        has_metadata = bool(result and result.get("metadata"))

        # Log successful document fetch completion
        if logger_client:
            await logger_client.log_business_event(
                "document_fetch_completed",
                {
                    "request_id": request_id,
                    "source": req.source,
                    "identifier": req.identifier,
                    "document_type": req.doc_type,
                    "result_size_bytes": result_size,
                    "has_content": has_content,
                    "has_metadata": has_metadata,
                    "processing_time_seconds": processing_time,
                    "success": True,
                },
            )

            await logger_client.log_performance_metric(
                "document_fetch",
                processing_time,
                {
                    "request_id": request_id,
                    "source": req.source,
                    "document_type": req.doc_type,
                    "fetch_success": True,
                    "result_has_content": has_content,
                },
            )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is (already logged above for unsupported source)
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log document fetch failure
        if logger_client:
            await logger_client.log_error(
                f"Document fetch failed: {str(e)}",
                {
                    "request_id": request_id,
                    "source": getattr(req, "source", "unknown"),
                    "identifier": getattr(req, "identifier", "unknown"),
                    "document_type": getattr(req, "doc_type", "unknown"),
                    "error_type": type(e).__name__,
                    "processing_time_seconds": error_time,
                    "external_api_failure": True,
                },
                error=e,
            )

            await logger_client.log_business_event(
                "document_fetch_failed",
                {
                    "request_id": request_id,
                    "source": getattr(req, "source", "unknown"),
                    "identifier": getattr(req, "identifier", "unknown"),
                    "document_type": getattr(req, "doc_type", "unknown"),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_time_seconds": error_time,
                },
            )

        raise


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
            "architecture-digitizer/normalize", {"system": req.system, "board_id": req.board_id, "token": req.token}
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
register_health_endpoints(app, ServiceNames.SOURCE_AGENT, "1.0.0")


@app.get("/sources")
async def list_sources():
    """List supported sources and their capabilities.

    Returns information about all supported source types (GitHub, Jira, Confluence)
    and their specific capabilities for fetching, normalization, and analysis.
    """
    try:
        sources_data = {"sources": SUPPORTED_SOURCES, "capabilities": SOURCE_CAPABILITIES}

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

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info")
