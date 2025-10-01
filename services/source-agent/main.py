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
import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException

from services.shared.infrastructure.config import load_service_config
from services.shared.utilities.resource_monitor import monitor_resources

# ============================================================================
# SHARED MODULES - Optimized import consolidation for consistency
# ============================================================================
from services.shared.infrastructure.monitoring.health import register_health_endpoints

try:
    import redis.asyncio as aioredis
except Exception:
    aioredis = None

# from services.shared.integrations.clients.clients import ServiceClients  # type: ignore - commented out as this module may not exist

# Load standardized configuration
config = load_service_config(
    service_type="source-agent",
    config_file="./config.yaml",  # Optional config file override
)

# Service configuration from standardized config
SERVICE_NAME = config.service_name
SERVICE_TITLE = config.service_description or "Source Agent"
SERVICE_VERSION = config.service_version
DEFAULT_API_PORT = int(os.environ.get("SERVICE_API_PORT", 5070))

# Supported sources and their capabilities
SUPAPI_PORTED_SOURCES = ["github", "jira", "confluence"]
SOURCE_CAPABILITIES = {
    "github": ["readme_fetch", "pr_normalization", "code_analysis"],
    "jira": ["issue_normalization"],
    "confluence": ["page_normalization"],
}
# ============================================================================
# SIMPLIFIED DOMAIN SERVICES - Standalone operation
# ============================================================================
# Use fallback implementations for standalone operation
print("Starting simplified source-agent (standalone mode)")

class MockFetchHandler:
    """Mock fetch handler for standalone operation."""
    @staticmethod
    async def fetch_github_document(owner: str, repo: str, req) -> dict:
        """Mock GitHub document fetch."""
        return {
            "status": "success",
            "message": f"Mock fetch completed for {owner}/{repo}",
            "data": {
                "document": {
                    "id": f"{owner}/{repo}",
                    "content": f"Mock content for {owner}/{repo}",
                    "source": "github"
                },
                "source": req.source if hasattr(req, 'source') else "github",
                "via": "mock-service",
            }
        }

class MockNormalizeHandler:
    """Mock normalize handler for standalone operation."""
    @staticmethod
    async def normalize_document(content: str, source: str) -> dict:
        """Mock document normalization."""
        return {
            "normalized_content": content,
            "source_type": source,
            "processing_metadata": {"mock": True}
        }

class MockCodeAnalyzer:
    """Mock code analyzer for standalone operation."""
    @staticmethod
    async def analyze_codebase(self, repo_url: str) -> dict:
        """Mock code analysis."""
        return {
            "analysis_type": "code",
            "repo_url": repo_url,
            "findings": ["Mock analysis completed"],
            "complexity_score": 0.5
        }

class MockIntelligentIngestionService:
    """Mock intelligent ingestion service for standalone operation."""
    async def ingest_document(self, document: dict) -> dict:
        """Mock document ingestion."""
        return {
            "ingestion_id": "mock-id",
            "status": "completed",
            "document_id": document.get("id", "unknown")
        }

# Use mock implementations
FetchHandler = MockFetchHandler
NormalizeHandler = MockNormalizeHandler
CodeAnalyzer = MockCodeAnalyzer
IntelligentIngestionService = MockIntelligentIngestionService()

# ============================================================================
# APPLICATION MODELS - API request/response models
# ============================================================================
from .presentation.models import (
    ArchitectureProcessRequest,
    CodeAnalysisRequest,
    DocumentRequest,
    NormalizationRequest,
    DocumentResponse,
    NormalizationResponse,
    CodeAnalysisResponse,
    ArchitectureProcessResponse,
    SourceCapabilities,
)

# ============================================================================
# SHARED UTILITIES - Leveraging centralized functionality
# ============================================================================
from services.shared.presentation.api.responses import (
    create_error_response,
    create_success_response,
)
from services.shared.infrastructure.utilities import clean_string, utc_now

# Initialize logger
logger = logging.getLogger(__name__)

# Create FastAPI app directly using shared utilities
app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Unified source agent for fetching and normalizing documents from GitHub, Jira, and Confluence",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Use common middleware setup to reduce duplication across services
from services.shared.infrastructure.utilities import attach_self_register, setup_common_middleware
from services.shared.infrastructure.utilities.error_handling import install_error_handlers

# Setup standardized middleware and utilities
setup_common_middleware(app, service_name=config.service_name)
install_error_handlers(app)

# Auto-register with orchestrator
attach_self_register(app, config.service_name)


# API Endpoints


@app.post(
    "/docs/fetch",
    response_model=DocumentResponse,
    summary="Fetch Document from Source",
    description="Fetch documents from supported sources including GitHub, Jira, and Confluence. Uses appropriate authentication and data transformation for each source type.",
    tags=["Documents"]
)
async def fetch_document(req: DocumentRequest) -> DocumentResponse:
    """Fetch document from specified source.

    Supports fetching documents from:
    - GitHub: READMEs, PRs, repository information
    - Jira: Issues, projects, workflows
    - Confluence: Pages, spaces, documentation

    Uses appropriate authentication and data transformation for each source type.
    """
    try:
        if req.source == "github":
            # Extract owner and repo for GitHub
            owner, repo = req.identifier.split(":", 1)
            return await FetchHandler.fetch_github_document(owner, repo, req)

        elif req.source == "jira":
            return await FetchHandler.fetch_jira_document(req)

        elif req.source == "confluence":
            return await FetchHandler.fetch_confluence_document(req)

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {req.source}")

    except ConnectionError as e:
        logger.error(f"Connection error fetching document: {e}")
        raise HTTPException(status_code=502, detail=f"External service unavailable: {str(e)}")
    except TimeoutError as e:
        logger.error(f"Timeout error fetching document: {e}")
        raise HTTPException(status_code=504, detail=f"Request timeout: {str(e)}")
    except ValueError as e:
        logger.error(f"Validation error fetching document: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching document: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post(
    "/normalize",
    response_model=NormalizationResponse,
    summary="Normalize Data from Source",
    description="Apply source-specific normalization rules to standardize data format, clean content, and extract structured information from raw source data.",
    tags=["Normalization"]
)
async def normalize_data(req: NormalizationRequest) -> NormalizationResponse:
    """Normalize data from specified source.

    Applies normalization rules for:
    - GitHub: Repository metadata, README content, issue data
    - Jira: Issue fields, workflow states, user assignments
    - Confluence: Page content, space metadata, attachment info

    Returns standardized data format regardless of source.
    """
    try:
        result = NormalizeHandler.normalize_data(req.source, req.data, req.correlation_id)
        return NormalizationResponse(
            status="success",
            normalized_data=result,
            source=req.source
        )
    except ValueError as e:
        logger.error(f"Validation error during normalization: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid normalization data: {str(e)}")
    except KeyError as e:
        logger.error(f"Missing required field during normalization: {e}")
        raise HTTPException(status_code=400, detail=f"Missing required field: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during normalization: {e}")
        raise HTTPException(status_code=500, detail=f"Normalization processing failed: {str(e)}")


@app.post(
    "/architecture/process",
    response_model=ArchitectureProcessResponse,
    summary="Process Architecture Diagrams",
    description="Process architectural diagrams and normalize them into standardized JSON schema using the architecture-digitizer service.",
    tags=["Architecture"]
)
async def process_architecture(req: ArchitectureProcessRequest) -> ArchitectureProcessResponse:
    """Process architectural diagrams using the architecture-digitizer service.

    Forwards diagram processing requests to the architecture-digitizer service
    for normalization into standardized JSON schema. Supports various diagram
    formats including UML, ERD, and system architecture diagrams.
    """
    try:
        from services.shared.infrastructure.utilities import get_service_client

        client = get_service_client()

        # Forward request to architecture-digitizer
        result = await client.post_json(
            "architecture-digitizer/normalize",
            {"system": req.system, "board_id": req.board_id, "token": req.token},
        )

        context = build_source-agent_context("architecture_process", system=req.system)
        return create_source-agent_success_response("processed", result, **context)

    except Exception as e:
        context = build_source-agent_context("architecture_process", system=req.system)
        return handle_source-agent_error("process architecture", e, **context)


@app.post(
    "/code/analyze",
    response_model=CodeAnalysisResponse,
    summary="Analyze Code for API Endpoints",
    description="Perform static analysis on code to identify API endpoints, architectural patterns, and potential integration points across different frameworks.",
    tags=["Code Analysis"]
)
async def analyze_code(req: CodeAnalysisRequest) -> CodeAnalysisResponse:
    """Analyze code for API endpoints and patterns.

    Performs static analysis to identify:
    - API endpoints and HTTP methods
    - Architectural patterns (MVC, Repository, etc.)
    - Framework-specific constructs
    - Code complexity metrics

    Supports multiple programming languages and frameworks.
    """
    try:
        result = CodeAnalyzer.analyze_code(
            req.source,
            req.code,
            req.language,
            req.context
        )
        return CodeAnalysisResponse(
            status="success",
            analysis=result,
            endpoints=result.get("endpoints", []),
            patterns=result.get("patterns", [])
        )
    except ValueError as e:
        logger.error(f"Validation error during code analysis: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid code analysis request: {str(e)}")
    except FileNotFoundError as e:
        logger.error(f"File not found during code analysis: {e}")
        raise HTTPException(status_code=404, detail=f"Source file not found: {str(e)}")
    except PermissionError as e:
        logger.error(f"Permission error during code analysis: {e}")
        raise HTTPException(status_code=403, detail=f"Access denied to source file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during code analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Code analysis processing failed: {str(e)}")


# ============================================================================
# HEALTH AND INFO ENDPOINTS - Using shared utilities for consistency
# ============================================================================

# Register standardized health endpoints
register_health_endpoints(app, config.service_name, config.service_version)


@app.get(
    "/sources",
    summary="List Supported Sources",
    description="Returns information about all supported source types (GitHub, Jira, Confluence) and their specific capabilities for fetching, normalization, and analysis.",
    tags=["Information"],
    response_model=Dict[str, Any]
)
async def list_sources() -> Dict[str, Any]:
    """List supported sources and their capabilities.

    Returns comprehensive information about supported source systems including:
    - Supported source types and their capabilities
    - Available operations and integrations
    - Service version and metadata
    """
    try:
        sources_data = {
            "sources": SUPAPI_PORTED_SOURCES,
            "capabilities": SOURCE_CAPABILITIES,
            "supported_operations": [
                "document_fetching",
                "data_normalization",
                "code_analysis",
                "architecture_processing"
            ],
            "version": SERVICE_VERSION
        }

        return create_success_response(
            data=sources_data,
            message="Sources retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error listing sources: {e}")
        return create_error_response(
            message="Failed to retrieve sources",
            error=str(e)
        )


# Health endpoint
@app.get("/health")
async def health():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "source-agent",
        "version": "1.0.0",
        "description": "Source Agent service is operational"
    }


if __name__ == "__main__":
    """Run the Source Agent service directly."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_API_PORT, log_level="info")
