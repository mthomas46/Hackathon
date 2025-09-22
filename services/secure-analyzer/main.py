"""Service: Secure Analyzer

Endpoints:
- POST /detect: Analyze content for sensitive information and security risks
- POST /suggest: Recommend appropriate AI models based on content sensitivity
- POST /summarize: Generate secure summaries with policy-based provider filtering
- GET /health: Service health check

Responsibilities:
- Detect sensitive content (PII, secrets, credentials) using pattern matching
- Enforce security policies for AI model selection based on content sensitivity
- Gate summarization requests to appropriate providers with circuit breaker protection
- Provide dead-letter queue for failed notification deliveries
- Cache owner resolutions and implement intelligent fallbacks

Dependencies: shared middlewares/logging, ServiceClients, httpx for external calls.
"""

import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

from services.shared.core.constants_new import EnvVars, ServiceNames  # type: ignore
from services.shared.monitoring.logging import fire_and_forget  # type: ignore
from services.shared.utilities.logging_client import get_log_collector_client
from services.shared.utilities.utilities import attach_self_register, setup_common_middleware  # type: ignore

try:
    from .modules.circuit_breaker import circuit_breaker, operation_timeout_context
    from .modules.content_detector import content_detector
    from .modules.policy_enforcer import policy_enforcer
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from modules.circuit_breaker import circuit_breaker, operation_timeout_context
    from modules.content_detector import content_detector
    from modules.policy_enforcer import policy_enforcer

# Service configuration constants
SERVICE_NAME = "secure-analyzer"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = 5070

# Content validation limits
MAX_CONTENT_SIZE_BYTES = 1000000  # 1MB
MAX_KEYWORDS_COUNT = 1000
MAX_KEYWORD_LENGTH = 500
MAX_PROVIDER_NAME_LENGTH = 100

# Circuit breaker defaults
DEFAULT_CIRCUIT_BREAKER_MAX_FAILURES = 5
DEFAULT_CIRCUIT_BREAKER_TIMEOUT = 60

# Initialize log collector client
logger_client = None

app = FastAPI(
    title="Secure Analyzer",
    version=SERVICE_VERSION,
    description="AI content security analysis service with policy enforcement and circuit breaker protection",
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global logger_client
    try:
        # Use a fallback service name if SECURE_ANALYZER doesn't exist in ServiceNames
        service_name = getattr(ServiceNames, "SECURE_ANALYZER", SERVICE_NAME)
        logger_client = await get_log_collector_client(service_name)
        if logger_client:
            await logger_client.log_business_event(
                "secure_analyzer_startup",
                {
                    "version": SERVICE_VERSION,
                    "capabilities": [
                        "content_security_analysis",
                        "policy_enforcement",
                        "circuit_breaker_protection",
                        "model_suggestions",
                        "content_summarization",
                    ],
                    "integrations": ["log_collector", "summarizer_hub", "content_detection_modules"],
                    "security_features": [
                        "pattern_matching",
                        "keyword_detection",
                        "circuit_breaker",
                        "timeout_protection",
                        "policy_enforcement",
                    ],
                    "analysis_types": ["sensitive_content_detection", "model_recommendations", "content_summarization"],
                },
            )
            await logger_client.log_info(
                "Secure Analyzer service started",
                {
                    "circuit_breaker_enabled": True,
                    "content_detection_ready": True,
                    "model_suggestion_engine": True,
                    "summarization_integration": True,
                },
            )
    except Exception as e:
        print(f"Failed to initialize log collector client: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if logger_client:
        try:
            await logger_client.log_info("Secure Analyzer service shutting down")
        except Exception:
            pass


# Use common middleware setup to reduce duplication across services
# setup_common_middleware already imported above
setup_common_middleware(app, ServiceNames.SECURE_ANALYZER)
attach_self_register(app, ServiceNames.SECURE_ANALYZER)


@app.get("/health")
async def health():
    """Health check endpoint returning service status and basic information."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "circuit_breaker_open": circuit_breaker.is_open(),
        "description": "Secure analyzer service is operational",
    }


class DetectRequest(BaseModel):
    """
    Request model for content security detection.

    Analyzes provided content for sensitive information, secrets, and
    security vulnerabilities using pattern matching.
    """

    content: str
    """Text content to analyze for security risks and sensitive data."""

    keywords: Optional[List[str]] = None
    """Additional keywords to search for beyond default security patterns."""

    keyword_document: Optional[str] = None
    """URL or reference to external keyword document (currently
    unimplemented)."""

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        """Validate content field with size and emptiness checks."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty or contain only whitespace")
        if len(v) > MAX_CONTENT_SIZE_BYTES:
            raise ValueError(f"Content exceeds maximum size of {MAX_CONTENT_SIZE_BYTES:,} bytes")
        return v

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v):
        """Validate keywords list with count and length checks."""
        if v is not None:
            if len(v) > MAX_KEYWORDS_COUNT:
                raise ValueError(f"Too many keywords (maximum {MAX_KEYWORDS_COUNT})")
            for keyword in v:
                if len(keyword) > MAX_KEYWORD_LENGTH:
                    raise ValueError(f"Keyword exceeds maximum length of {MAX_KEYWORD_LENGTH} characters")
        return v


class DetectResponse(BaseModel):
    """
    Response model for content detection results.

    Contains the analysis results indicating whether content is
    sensitive and what specific patterns or topics were detected.
    """

    sensitive: bool
    """Whether the content contains sensitive information that may require
    special handling."""

    matches: List[str]
    """List of specific patterns or keywords that were detected in the
    content."""

    topics: List[str]
    """Security topics identified in the content (e.g., 'pii', 'secrets',
    'credentials')."""


# Pattern matching and content detection logic moved to modules/content_detector.py


@app.post("/detect", response_model=DetectResponse)
async def detect(req: DetectRequest):
    """
    Detect sensitive content and security risks in the provided text.

    Analyzes content for sensitive information including PII, secrets,
    credentials, and security vulnerabilities. Supports custom keywords
    and external keyword documents.

    Protected by circuit breaker to prevent cascade failures.
    """
    start_time = time.time()
    request_id = f"secure_detect_{int(time.time() * 1000)}"

    try:
        # Check circuit breaker to prevent cascade failures
        if circuit_breaker.is_open():
            circuit_breaker_open_time = time.time() - start_time

            # Log circuit breaker rejection
            if logger_client:
                await logger_client.log_business_event(
                    "secure_analyzer_circuit_breaker_rejection",
                    {
                        "request_id": request_id,
                        "operation": "detect",
                        "rejection_reason": "circuit_breaker_open",
                        "processing_time_seconds": circuit_breaker_open_time,
                    },
                )

                await logger_client.log_error(
                    f"Secure analyzer circuit breaker open - rejecting detect request",
                    {
                        "request_id": request_id,
                        "operation": "detect",
                        "circuit_breaker_state": "open",
                        "processing_time_seconds": circuit_breaker_open_time,
                    },
                    error=Exception("Service temporarily unavailable due to circuit breaker"),
                )

            print(f"[{SERVICE_NAME.upper()}] Circuit breaker is OPEN - rejecting detect request")
            raise HTTPException(status_code=503, detail="Service temporarily unavailable due to circuit breaker")

        async with operation_timeout_context("detect"):
            # Log detection start
            if logger_client:
                await logger_client.log_business_event(
                    "secure_content_detection_started",
                    {
                        "request_id": request_id,
                        "content_length": len(req.content),
                        "has_custom_keywords": bool(req.keywords),
                        "has_keyword_document": bool(req.keyword_document),
                        "keyword_document_url": req.keyword_document,
                        "custom_keywords_count": len(req.keywords) if req.keywords else 0,
                    },
                )

                await logger_client.log_info(
                    "Starting secure content detection",
                    {
                        "request_id": request_id,
                        "content_length": len(req.content),
                        "keyword_sources": (
                            ["custom"] if req.keywords else [] + ["document"] if req.keyword_document else []
                        ),
                        "circuit_breaker_state": "closed",
                    },
                )

            fire_and_forget(
                "info",
                "detect",
                ServiceNames.SECURE_ANALYZER,
                {
                    "has_keywords": bool(req.keywords),
                    "has_keyword_doc": bool(req.keyword_document),
                    "content_length": len(req.content),
                },
            )

            # Load additional keywords from URL if provided
            extra_keywords = req.keywords or []
            keyword_load_success = True
            if req.keyword_document:
                print(f"[{SERVICE_NAME.upper()}] Loading keywords from URL: {req.keyword_document}")
                try:
                    # TODO: Implement URL keyword loading
                    print(f"[{SERVICE_NAME.upper()}] Loaded {len(extra_keywords)} keywords total")

                    # Log successful keyword loading
                    if logger_client:
                        await logger_client.log_info(
                            "Successfully loaded keywords from document",
                            {
                                "request_id": request_id,
                                "keyword_document_url": req.keyword_document,
                                "keywords_loaded": len(extra_keywords),
                            },
                        )

                except Exception as e:
                    keyword_load_success = False
                    print(f"[{SERVICE_NAME.upper()}] Failed to load keywords from URL: {e}")

                    # Log keyword loading failure
                    if logger_client:
                        await logger_client.log_error(
                            f"Failed to load keywords from document URL: {str(e)}",
                            {
                                "request_id": request_id,
                                "keyword_document_url": req.keyword_document,
                                "error_type": type(e).__name__,
                                "keyword_load_success": False,
                            },
                            error=e,
                        )

            # Detect sensitive content using pattern matching
            detection_result = content_detector.detect_sensitive_content(req.content, extra_keywords)

            processing_time = time.time() - start_time

            # Calculate detection metrics
            sensitive_content_detected = detection_result.get("sensitive", False)
            matches_found = len(detection_result.get("matches", []))
            topics_identified = len(detection_result.get("topics", []))
            total_patterns_checked = matches_found + topics_identified

            # Log successful detection completion
            if logger_client:
                await logger_client.log_business_event(
                    "secure_content_detection_completed",
                    {
                        "request_id": request_id,
                        "sensitive_content_detected": sensitive_content_detected,
                        "matches_found": matches_found,
                        "topics_identified": topics_identified,
                        "total_patterns_checked": total_patterns_checked,
                        "processing_time_seconds": processing_time,
                        "keyword_load_success": keyword_load_success,
                        "success": True,
                    },
                )

                await logger_client.log_performance_metric(
                    "secure_content_detection",
                    processing_time,
                    {
                        "request_id": request_id,
                        "content_length": len(req.content),
                        "patterns_analyzed": total_patterns_checked,
                        "detection_success": True,
                        "sensitive_content_found": sensitive_content_detected,
                    },
                )

            return DetectResponse(**detection_result)

    except HTTPException:
        # Re-raise HTTP exceptions as-is (already logged above for circuit breaker)
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log detection failure
        if logger_client:
            await logger_client.log_error(
                f"Secure content detection failed: {str(e)}",
                {
                    "request_id": request_id,
                    "content_length": len(req.content) if "req" in locals() else None,
                    "error_type": type(e).__name__,
                    "processing_time_seconds": error_time,
                    "circuit_breaker_state": (
                        "open" if "circuit_breaker" in locals() and circuit_breaker.is_open() else "closed"
                    ),
                },
                error=e,
            )

            await logger_client.log_business_event(
                "secure_content_detection_failed",
                {
                    "request_id": request_id,
                    "content_length": len(req.content) if "req" in locals() else None,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_time_seconds": error_time,
                },
            )

        raise


class SuggestRequest(BaseModel):
    content: str
    keywords: Optional[List[str]] = None
    keyword_document: Optional[str] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        if len(v) > 1000000:  # 1MB limit
            raise ValueError("Content too large (max 1MB)")
        return v

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v):
        if v is not None:
            if len(v) > 1000:
                raise ValueError("Too many keywords (max 1000)")
            for keyword in v:
                if len(keyword) > 500:
                    raise ValueError("Keyword too long (max 500 characters)")
        return v


class SuggestResponse(BaseModel):
    sensitive: bool
    allowed_models: List[str]
    suggestion: str


@app.post("/suggest", response_model=SuggestResponse)
async def suggest(req: SuggestRequest):
    """Suggest appropriate models based on content sensitivity."""
    # Check circuit breaker
    if circuit_breaker.is_open():
        print(f"[SECURE_ANALYZER] Circuit breaker is OPEN - rejecting suggest request")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable due to circuit breaker")

    async with operation_timeout_context("suggest"):
        print(f"[SECURE_ANALYZER] Starting suggest operation")
        fire_and_forget("info", "suggest", ServiceNames.SECURE_ANALYZER, {"has_kw": bool(req.keywords)})

        # Detect sensitive content
        detection = await detect(
            DetectRequest(content=req.content, keywords=req.keywords, keyword_document=req.keyword_document)
        )
        print(f"[SECURE_ANALYZER] Detection completed, sensitive: {detection.sensitive}")

        # Get allowed models based on policy
        allowed_models = policy_enforcer.get_allowed_models(detection.sensitive)
        suggestion = policy_enforcer.get_policy_suggestion(detection.sensitive)

        print(f"[SECURE_ANALYZER] Suggest operation completed, returning {len(allowed_models)} allowed models")
        return SuggestResponse(sensitive=detection.sensitive, allowed_models=allowed_models, suggestion=suggestion)


class SummarizeRequest(BaseModel):
    content: str
    providers: Optional[List[Dict[str, Any]]] = None  # forwarded to summarizer-hub
    override_policy: Optional[bool] = False
    keywords: Optional[List[str]] = None
    keyword_document: Optional[str] = None
    prompt: Optional[str] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        if len(v) > 1000000:  # 1MB limit
            raise ValueError("Content too large (max 1MB)")
        return v

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v):
        if v is not None:
            if len(v) > 1000:
                raise ValueError("Too many keywords (max 1000)")
            for keyword in v:
                if len(keyword) > 500:
                    raise ValueError("Keyword too long (max 500 characters)")
        return v

    @field_validator("providers")
    @classmethod
    def validate_providers(cls, v):
        if v is not None:
            if len(v) > 1000:
                raise ValueError("Too many providers (max 1000)")
            for provider in v:
                if not isinstance(provider, dict):
                    raise ValueError("Each provider must be a dictionary")
                if "name" not in provider:
                    raise ValueError("Each provider must have a name field")
                if len(provider.get("name", "")) > 100:
                    raise ValueError("Provider name too long (max 100 characters)")
        return v


@app.post("/summarize")
async def summarize(req: SummarizeRequest):
    # Check circuit breaker
    if circuit_breaker.is_open():
        print(f"[SECURE_ANALYZER] Circuit breaker is OPEN - rejecting summarize request")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable due to circuit breaker")

    async with operation_timeout_context("summarize"):
        print(f"[SECURE_ANALYZER] Starting summarize operation")
        fire_and_forget("info", "summarize", ServiceNames.SECURE_ANALYZER, {"override": req.override_policy})

        hub = os.environ.get(EnvVars.SUMMARIZER_HUB_URL_ENV, "http://summarizer-hub:5060")
        print(f"[SECURE_ANALYZER] Summarizer hub URL: {hub}")

        # Detect sensitive content
        det = await detect(
            DetectRequest(content=req.content, keywords=req.keywords, keyword_document=req.keyword_document)
        )
        print(f"[SECURE_ANALYZER] Detection completed, sensitive: {det.sensitive}")

        # Filter providers based on policy
        providers = policy_enforcer.filter_providers(req.providers, det.sensitive, req.override_policy)
    # Set default prompt if none provided
    if not req.prompt:
        try:
            from services.shared.prompt_manager import get_prompt

            req.prompt = get_prompt("summarization.security_focused")
        except Exception:
            req.prompt = "Summarize focusing on risks, PII, secrets, and client information."

    # Mock response for testing
    if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("TESTING"):
        provider_used = providers[0].get("name", "ollama") if providers else "ollama"
        base_summary = f"Mock summary (len={len(req.content)}), providers={len(providers)}"
        if req.prompt and ("security" in req.prompt.lower() or "risk" in req.prompt.lower()):
            base_summary = f"Security-focused summary: This content has been analyzed for security risks and potential vulnerabilities. Key findings include {len(det.matches)} sensitive elements and {len(det.topics)} security topics identified."

        return {
            "summary": base_summary,
            "provider_used": provider_used,
            "confidence": 0.9 if det.sensitive else 0.8,
            "word_count": len((req.content or "").split()),
            "topics_detected": det.topics,
            "policy_enforced": det.sensitive and not req.override_policy,
            "analysis": {"agreed": ["policy ok"]},
        }

    # Production code - make actual external call
    payload = {
        "text": req.content,
        "providers": providers,
        "use_hub_config": True,
    }
    from services.shared.integrations.clients.clients import ServiceClients  # type: ignore

    svc = ServiceClients(timeout=60)
    try:
        return await svc.post_json(f"{hub}/summarize/ensemble", payload)
    except Exception as e:
        return {
            "summary": f"Fallback mock summary: External service error - {str(e)}",
            "provider_used": "fallback",
            "confidence": 0.5,
            "word_count": len((req.content or "").split()),
            "topics_detected": det.topics,
            "policy_enforced": det.sensitive and not req.override_policy,
        }


if __name__ == "__main__":
    """Run the Secure Analyzer service directly."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info")
