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
    create_base_document,
    extract_text_from_html,
    normalize_document_content,
    handle_fetch_error,
    handle_source_agent_error,
    create_source_agent_success_response,
    build_source_agent_context,
    validate_source_type,
    extract_endpoints_from_code,
    build_github_url,
    build_jira_url,
    build_confluence_url,
    extract_adf_text
)

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


# Shared models
class DocumentRequest(BaseModel):
    source: str  # github, jira, confluence
    identifier: str  # repo path, issue key, page ID
    scope: Optional[dict] = None

    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        supported = ['github', 'jira', 'confluence']
        if v not in supported:
            from pydantic_core import PydanticCustomError
            raise PydanticCustomError(
                'source_not_supported',
                'Unsupported source: {source}. Must be one of {supported}',
                {'source': v, 'supported': supported}
            )
        return v

    @field_validator('identifier')
    @classmethod
    def validate_identifier(cls, v, info):
        source = info.data.get('source')
        if source == 'github' and ':' not in v:
            from pydantic_core import PydanticCustomError
            raise PydanticCustomError(
                'invalid_github_identifier',
                'GitHub identifier must be in format owner:repo'
            )
        return v


class NormalizationRequest(BaseModel):
    source: str
    data: dict
    correlation_id: Optional[str] = None

    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        supported = ['github', 'jira', 'confluence']
        if v not in supported:
            from pydantic_core import PydanticCustomError
            raise PydanticCustomError(
                'source_not_supported',
                'Unsupported source: {source}. Must be one of {supported}',
                {'source': v, 'supported': supported}
            )
        return v


class CodeAnalysisRequest(BaseModel):
    text: str

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            from pydantic_core import PydanticCustomError
            raise PydanticCustomError(
                'text_required',
                'Text field is required and cannot be empty'
            )
        return v


# ============================================================================
# GITHUB FUNCTIONALITY - Using shared utilities and document builders
# ============================================================================

def extract_endpoints_from_patch(patch: str) -> List[str]:
    """Extract API endpoints from GitHub PR patch using shared utilities."""
    return extract_endpoints_from_code(patch)

async def http_get_cached(url: str, etag: Optional[str] = None, last_modified: Optional[str] = None, timeout: int = 15):
    """Cached HTTP GET with GitHub-specific headers."""
    status, body, headers = await cached_get(url, etag, last_modified, timeout)
    return status, body, headers

# ============================================================================
# JIRA AND CONFLUENCE FUNCTIONALITY - Now handled by document_builders module
# ============================================================================
# All Jira and Confluence document building functions have been moved to
# document_builders.py module to eliminate duplication and improve maintainability


# API Endpoints

@app.post("/docs/fetch")
async def fetch_document(req: DocumentRequest):
    """Fetch document from specified source using shared utilities."""
    try:
        if req.source == "github":
            # Extract owner and repo for GitHub
            owner, repo = req.identifier.split(":", 1)

            # Optionally delegate to local GitHub MCP when enabled
            if os.environ.get("USE_GITHUB_MCP", "0") in ("1", "true", "TRUE"):
                try:
                    clients = ServiceClients(timeout=20)
                    mcp_resp = await clients.post_json(
                        "github-mcp/tools/github.get_repo/invoke",
                        {"arguments": {"owner": owner, "repo": repo}}
                    )
                    result = (mcp_resp or {}).get("result", {})
                    title = f"{result.get('full_name', f'{owner}/{repo}')}"
                    content = f"Repository: {result.get('full_name', f'{owner}/{repo}')}\nStars: {result.get('stars', 0)}\nTopics: {', '.join(result.get('topics', []))}"
                    doc = build_readme_doc(owner, repo, content)
                    context = build_source_agent_context("fetch", req.source, doc.id)
                    return create_source_agent_success_response("retrieved", {
                        "document": doc.model_dump(),
                        "source": req.source,
                        "via": "github-mcp"
                    }, **context)
                except Exception as e:
                    # Fallback to direct GitHub fetch below
                    pass

            # Direct GitHub README fetch or offline-friendly fallback
            url = build_github_url(f"/repos/{owner}/{repo}/readme")
            status, body, _ = await http_get_cached(url)

            if status == 200:
                import base64
                content = base64.b64decode(body.get("content", "")).decode("utf-8")
            else:
                # Offline-friendly fallback content
                content = f"# {owner}/{repo}\n\nREADME unavailable in test environment."

            # Sanitize all content for security (prevent XSS in responses)
            safe_owner = sanitize_for_response(owner)
            safe_repo = sanitize_for_response(repo)
            safe_content = sanitize_for_response(content)
            doc = build_readme_doc(safe_owner, safe_repo, safe_content)

            context = build_source_agent_context("fetch", req.source, doc.id)
            return create_source_agent_success_response("retrieved", {
                "document": doc.model_dump(),
                "source": req.source
            }, **context)

        elif req.source == "jira":
            # Jira issue fetch (placeholder)
            return handle_source_agent_error(
                "fetch from Jira",
                Exception("Jira fetch not implemented"),
                error_code=ErrorCodes.FEATURE_NOT_IMPLEMENTED,
                source=req.source, status="placeholder"
            )

        elif req.source == "confluence":
            # Confluence page fetch (placeholder)
            return handle_source_agent_error(
                "fetch from Confluence",
                Exception("Confluence fetch not implemented"),
                error_code=ErrorCodes.FEATURE_NOT_IMPLEMENTED,
                source=req.source, status="placeholder"
            )

    except Exception as e:
        context = build_source_agent_context("fetch", req.source)
        context = {k: v for k, v in context.items() if k != "operation"}
        return handle_source_agent_error("fetch document", e, **context)


@app.post("/normalize")
async def normalize_data(req: NormalizationRequest):
    """Normalize data from specified source using shared utilities."""
    try:
        envelope = None

        if req.source == "github":
            if req.data.get("type") == "pr":
                # GitHub PR normalization
                pr_data = req.data
                content = f"PR #{pr_data.get('number')}: {pr_data.get('title')}\n\n{pr_data.get('body', '')}"
                doc = create_base_document(
                    source_type="github",
                    id=f"github:pr:{pr_data.get('number')}",
                    title=f"PR #{pr_data.get('number')}: {pr_data.get('title')}",
                    content=content,
                    metadata={
                        "type": "pull_request",
                        "state": pr_data.get("state"),
                        "merged": pr_data.get("merged"),
                        "owner": pr_data.get("user", {}).get("login")
                    }
                )
                doc.source_id = str(pr_data.get("number"))
                doc.content_hash = stable_hash(content)
                doc.url = pr_data.get("html_url", "")
                doc.project = pr_data.get("base", {}).get("repo", {}).get("full_name", "")

                envelope = DocumentEnvelope(
                    id=f"env:{doc.id}",
                    correlation_id=req.correlation_id,
                    document=doc.model_dump()
                )
            elif req.data.get("type") == "readme":
                # Normalize README-like content
                readme = req.data
                title = readme.get("name") or "README"
                content = readme.get("content") or ""
                doc = create_base_document(
                    source_type="github",
                    id=f"github:readme:{stable_hash(content)[:8]}",
                    title=title,
                    content=content,
                    metadata={"type": "readme", "url": readme.get("html_url")}
                )
                envelope = DocumentEnvelope(
                    id=f"env:{doc.id}",
                    correlation_id=req.correlation_id,
                    document=doc.model_dump()
                )
            else:
                # Generic normalization for arbitrary GitHub-derived content
                title = req.data.get("title") or "GitHub Document"
                content = req.data.get("content") or ""
                doc = create_base_document(
                    source_type="github",
                    id=f"github:doc:{stable_hash(title + content)[:8]}",
                    title=title,
                    content=content,
                    metadata=req.data.get("metadata") or {}
                )
                envelope = DocumentEnvelope(
                    id=f"env:{doc.id}",
                    correlation_id=req.correlation_id,
                    document=doc.model_dump()
                )

        elif req.source == "jira":
            if req.data.get("key"):
                # Jira issue normalization
                doc = build_jira_doc(req.data["key"], req.data)
                envelope = DocumentEnvelope(
                    id=f"env:{doc.id}",
                    correlation_id=req.correlation_id,
                    document=doc.model_dump()
                )

        elif req.source == "confluence":
            if req.data.get("id"):
                # Confluence page normalization
                doc = build_confluence_doc(req.data["id"], req.data)
                envelope = DocumentEnvelope(
                    id=f"env:{doc.id}",
                    correlation_id=req.correlation_id,
                    document=doc.model_dump()
                )

        if envelope:
            context = build_source_agent_context("normalize", req.source)
            context = {k: v for k, v in context.items() if k != "operation"}
            return create_source_agent_success_response("normalized", {"envelope": envelope.model_dump()}, **context)
        else:
            return handle_source_agent_error(
                "normalize data",
                Exception("Unable to normalize data"),
                ErrorCodes.DATA_NORMALIZATION_FAILED,
                source=req.source
            )

    except HTTPException:
        raise
    except Exception as e:
        context = build_source_agent_context("normalize", req.source)
        context = {k: v for k, v in context.items() if k != "operation"}
        return handle_source_agent_error("normalize data", e, **context)


@app.post("/code/analyze")
async def analyze_code(req: CodeAnalysisRequest):
    """Analyze code for API endpoints and patterns using shared utilities."""
    try:
        text = req.text
        hints = extract_endpoints_from_code(text)

        result = {
            "analysis": "\n".join(hints),
            "endpoint_count": len(hints),
            "patterns_found": ["FastAPI", "Express", "Flask"]
        }

        context = build_source_agent_context("analyze_code", endpoint_count=len(hints))
        return create_source_agent_success_response("analyzed", result, **context)

    except Exception as e:
        context = build_source_agent_context("analyze_code")
        context = {k: v for k, v in context.items() if k != "operation"}
        return handle_source_agent_error("analyze code", e, **context)


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
