"""Report handling functionality for the Orchestrator service.

This module contains all report-related endpoints and utilities,
extracted from the main orchestrator service to improve maintainability.
"""

from fastapi import Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from .shared_utils import (
    get_orchestrator_service_client,
    get_service_url,
    prepare_correlation_headers,
    handle_service_error,
    create_service_success_response,
    build_orchestrator_context
)


class ReportRequest(BaseModel):
    """Request model for report generation."""
    kind: str  # "generate"|"life_of_ticket"|"pr_confidence"
    format: Optional[str] = "json"
    payload: Dict[str, Any] = {}


class SuggestSummarizationRequest(BaseModel):
    """Request model for summarization suggestions."""
    content: str
    keywords: Optional[List[str]] = None
    keyword_document: Optional[str] = None
    override_policy: Optional[bool] = False


async def _proxy_request(service_url: str, path: str, body: Dict[str, Any], headers: Dict[str, str]):
    """Shared proxy function for service communication using shared utilities."""
    try:
        service_client = get_orchestrator_service_client()
        return await service_client.post_json(f"{service_url}{path}", body, headers=headers)
    except Exception as e:
        return handle_service_error("proxy request", e, service_url=service_url, path=path)


# Service URL helpers removed - using shared utilities

async def request_report(req: ReportRequest, request: Request):
    """Handle report generation requests with standardized patterns."""
    fire_and_forget("info", "request_report called", ServiceNames.ORCHESTRATOR, {"kind": req.kind})

    # Centralized service URL resolution
    reporting_url = _get_service_url("reporting", "http://reporting:5030")
    headers = _prepare_correlation_headers(request)

    # Standardized path resolution
    path_map = {
        "life_of_ticket": "/reports/life-of-ticket",
        "pr_confidence": "/reports/pr_confidence",
        "generate": "/reports/generate"
    }
    path = path_map.get(req.kind, "/reports/generate")

    # Clean payload preparation
    body = req.payload.copy()
    if req.format:
        body["format"] = req.format

    return await _proxy_request(reporting_url, path, body, headers)


async def summarization_suggest(req: SuggestSummarizationRequest, request: Request):
    """Handle summarization suggestion requests with standardized patterns."""
    fire_and_forget("info", "summarization_suggest called", ServiceNames.ORCHESTRATOR, {"override": req.override_policy})

    # Centralized service URL resolution
    sa_url = _get_service_url("secure_analyzer", "http://secure-analyzer:5070")
    headers = _prepare_correlation_headers(request)

    # Get summarization suggestion
    suggestion_payload = {
        "content": req.content,
        "keywords": req.keywords,
        "keyword_document": req.keyword_document,
    }
    suggestion = await _proxy_request(sa_url, "/suggest", suggestion_payload, headers)

    # Perform summarization with policy-aware provider selection
    providers = None if req.override_policy else [
        {"name": name} for name in suggestion.get("allowed_models", [])
    ]

    summarize_payload = {
        "content": req.content,
        "providers": providers,
        "override_policy": req.override_policy,
        "keywords": req.keywords,
        "keyword_document": req.keyword_document,
    }
    result = await _proxy_request(sa_url, "/summarize", summarize_payload, headers)

    # Return standardized response format
    return {
        "suggestion": suggestion,
        "result": result,
        "policy_override": req.override_policy,
        "providers_used": providers
    }
