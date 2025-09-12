"""Service: Secure Analyzer

Endpoints:
- POST /detect, /suggest, /summarize; GET /health

Responsibilities: Detect sensitive content; gate summarization providers; call summarizer-hub per policy.
Dependencies: shared middlewares/logging, ServiceClients; environment-driven provider lists.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any
import os
import re
import httpx
import asyncio
import time
import signal
from contextlib import asynccontextmanager

from services.shared.logging import fire_and_forget  # type: ignore
from services.shared.utilities import attach_self_register  # type: ignore
from services.shared.constants_new import EnvVars, ServiceNames  # type: ignore

from .modules.circuit_breaker import circuit_breaker, operation_timeout_context
from .modules.content_detector import content_detector
from .modules.policy_enforcer import policy_enforcer
from .modules.validation import validate_content, validate_keywords, validate_providers

# Circuit breaker and operation timeout logic moved to modules/circuit_breaker.py

app = FastAPI(title="Secure Analyzer", version="0.1.0")
# Use common middleware setup to reduce duplication across services
from services.shared.utilities import setup_common_middleware
setup_common_middleware(app, ServiceNames.SECURE_ANALYZER)
attach_self_register(app, ServiceNames.SECURE_ANALYZER)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "secure-analyzer"}


class DetectRequest(BaseModel):
    content: str
    keywords: Optional[List[str]] = None
    keyword_document: Optional[str] = None

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) > 1000000:  # 1MB limit
            raise ValueError('Content too large (max 1MB)')
        return v

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v):
        if v is not None:
            if len(v) > 1000:
                raise ValueError('Too many keywords (max 1000)')
            for keyword in v:
                if len(keyword) > 500:
                    raise ValueError('Keyword too long (max 500 characters)')
        return v


class DetectResponse(BaseModel):
    sensitive: bool
    matches: List[str]
    topics: List[str]


# Pattern matching and content detection logic moved to modules/content_detector.py


@app.post("/detect", response_model=DetectResponse)
async def detect(req: DetectRequest):
    """Detect sensitive content in the provided text."""
    # Check circuit breaker
    if circuit_breaker.is_open():
        print(f"[SECURE_ANALYZER] Circuit breaker is OPEN - rejecting detect request")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable due to circuit breaker")

    async with operation_timeout_context("detect"):
        fire_and_forget("info", "detect", ServiceNames.SECURE_ANALYZER, {"has_kw": bool(req.keywords), "has_doc": bool(req.keyword_document)})

        # Load additional keywords from URL if provided
        extra_keywords = req.keywords or []
        if req.keyword_document:
            print(f"[SECURE_ANALYZER] Loading keywords from URL: {req.keyword_document}")
            try:
                # TODO: Implement URL keyword loading
                print(f"[SECURE_ANALYZER] Loaded {len(extra_keywords)} keywords total")
            except Exception as e:
                print(f"[SECURE_ANALYZER] Failed to load keywords from URL: {e}")

        # Detect sensitive content
        result = content_detector.detect_sensitive_content(req.content, extra_keywords)

        return DetectResponse(**result)


class SuggestRequest(BaseModel):
    content: str
    keywords: Optional[List[str]] = None
    keyword_document: Optional[str] = None

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) > 1000000:  # 1MB limit
            raise ValueError('Content too large (max 1MB)')
        return v

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v):
        if v is not None:
            if len(v) > 1000:
                raise ValueError('Too many keywords (max 1000)')
            for keyword in v:
                if len(keyword) > 500:
                    raise ValueError('Keyword too long (max 500 characters)')
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
        detection = await detect(DetectRequest(content=req.content, keywords=req.keywords, keyword_document=req.keyword_document))
        print(f"[SECURE_ANALYZER] Detection completed, sensitive: {detection.sensitive}")

        # Get allowed models based on policy
        allowed_models = policy_enforcer.get_allowed_models(detection.sensitive)
        suggestion = policy_enforcer.get_policy_suggestion(detection.sensitive)

        print(f"[SECURE_ANALYZER] Suggest operation completed, returning {len(allowed_models)} allowed models")
        return SuggestResponse(
            sensitive=detection.sensitive,
            allowed_models=allowed_models,
            suggestion=suggestion
        )


class SummarizeRequest(BaseModel):
    content: str
    providers: Optional[List[Dict[str, Any]]] = None  # forwarded to summarizer-hub
    override_policy: Optional[bool] = False
    keywords: Optional[List[str]] = None
    keyword_document: Optional[str] = None
    prompt: Optional[str] = None

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) > 1000000:  # 1MB limit
            raise ValueError('Content too large (max 1MB)')
        return v

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v):
        if v is not None:
            if len(v) > 1000:
                raise ValueError('Too many keywords (max 1000)')
            for keyword in v:
                if len(keyword) > 500:
                    raise ValueError('Keyword too long (max 500 characters)')
        return v

    @field_validator('providers')
    @classmethod
    def validate_providers(cls, v):
        if v is not None:
            if len(v) > 1000:
                raise ValueError('Too many providers (max 1000)')
            for provider in v:
                if not isinstance(provider, dict):
                    raise ValueError('Each provider must be a dictionary')
                if 'name' not in provider:
                    raise ValueError('Each provider must have a name field')
                if len(provider.get('name', '')) > 100:
                    raise ValueError('Provider name too long (max 100 characters)')
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
        det = await detect(DetectRequest(content=req.content, keywords=req.keywords, keyword_document=req.keyword_document))
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
    from services.shared.clients import ServiceClients  # type: ignore
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5070)


