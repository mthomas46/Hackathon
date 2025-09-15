"""Service: Summarizer Hub

Endpoints:
- POST /summarize/ensemble: Orchestrate summarization across multiple LLM providers
- GET /health: Service health check

Responsibilities:
- Fan out summarization requests to configured providers (Ollama, OpenAI, Anthropic, Grok, Bedrock)
- Merge outputs from multiple providers into normalized results
- Analyze consistency across provider responses
- Support rate limiting via environment configuration
- Handle provider fallback and error recovery
- Record job data to frontend cache for visualization and monitoring

Dependencies: shared middlewares, httpx for HTTP requests, optional Bedrock SDK.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from services.shared.logging import fire_and_forget  # type: ignore
from services.shared.middleware import RequestMetricsMiddleware, RequestIdMiddleware, RateLimitMiddleware  # type: ignore
from services.shared.utilities import attach_self_register  # type: ignore
from services.shared.config import get_config_value  # type: ignore
from services.shared.constants_new import ServiceNames  # type: ignore

from .modules.config_manager import config_manager
from .modules.provider_manager import provider_manager
from .modules.response_processor import response_processor

# Service configuration constants
SERVICE_NAME = "summarizer-hub"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = 5060

# Rate limiting defaults (when enabled)
DEFAULT_ENSEMBLE_RATE_LIMIT_REQUESTS_PER_SECOND = 2.0
DEFAULT_ENSEMBLE_RATE_LIMIT_BURST_SIZE = 5

# Provider timeout defaults
DEFAULT_PROVIDER_TIMEOUT_SECONDS = 60
DEFAULT_BEDROCK_TIMEOUT_SECONDS = 90

app = FastAPI(
    title="Summarizer Hub",
    version=SERVICE_VERSION,
    description="Multi-provider LLM summarization orchestration service"
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name=SERVICE_NAME)
attach_self_register(app, SERVICE_NAME)

# Rate limiting configuration (optional)
_rate_limit_enabled = str(get_config_value("RATE_LIMIT_ENABLED", False, section="summarizer_hub", env_key="RATE_LIMIT_ENABLED")).strip().lower() in ("1", "true", "yes")
if _rate_limit_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        limits={
            "/summarize/ensemble": (DEFAULT_ENSEMBLE_RATE_LIMIT_REQUESTS_PER_SECOND, DEFAULT_ENSEMBLE_RATE_LIMIT_BURST_SIZE),
        },
    )


@app.get("/health")
async def health():
    """Health check endpoint returning service status and basic information."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "Summarizer hub service is operational"
    }


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider in summarization requests.

    Specifies which provider to use and how to connect to it.
    Provider configurations can be merged with hub-wide defaults.
    """

    name: str
    """Provider name (e.g., "ollama", "openai", "anthropic", "grok", "bedrock")."""

    model: Optional[str] = None
    """Model identifier specific to the provider."""

    endpoint: Optional[str] = None
    """Custom endpoint URL for local gateways or proxies."""

    api_key: Optional[str] = None
    """API key for authenticated providers (not recommended for production)."""

    region: Optional[str] = None
    """AWS region for Bedrock providers."""

    profile: Optional[str] = None
    """AWS named profile for Bedrock providers."""


class SummarizeRequest(BaseModel):
    """Request model for ensemble summarization across multiple providers.

    Orchestrates summarization of text using multiple LLM providers,
    with optional custom prompts and configuration merging.
    """

    text: str
    """The text content to summarize."""

    providers: List[ProviderConfig]
    """List of provider configurations to use for summarization."""

    prompt: Optional[str] = None
    """Optional custom prompt to prepend to the text for each provider."""

    use_hub_config: Optional[bool] = True
    """Whether to merge provider configs with hub-wide configuration defaults."""




@app.post("/summarize/ensemble")
async def summarize_ensemble(req: SummarizeRequest):
    """Orchestrate ensemble summarization across multiple LLM providers.

    Fan out the summarization request to all specified providers, collect their
    outputs, analyze consistency across responses, and return normalized results.
    Supports provider configuration merging and automatic fallback handling.

    Protected by optional rate limiting when enabled.
    """
    fire_and_forget("info", "summarize_ensemble", ServiceNames.SUMMARIZER_HUB, {
        "provider_count": len(req.providers),
        "providers": [p.name for p in req.providers],
        "use_hub_config": req.use_hub_config,
        "text_length": len(req.text)
    })

    # Validate request requirements
    if not req.providers:
        raise HTTPException(status_code=400, detail="At least one provider configuration is required")

    # Initialize results collection
    provider_summaries: Dict[str, str] = {}

    # Load hub configuration for provider merging (if enabled)
    hub_config = config_manager.load_hub_config() if req.use_hub_config else {}

    # Process each provider
    for provider_config in req.providers:
        # Merge with hub configuration if available
        if hub_config:
            provider_config = config_manager.merge_provider_from_config(provider_config, hub_config)

        # Execute summarization with the provider
        summary_output = await provider_manager.summarize_with_provider(
            provider_config.name, provider_config, req.prompt, req.text
        )
        provider_summaries[provider_config.name] = summary_output

    # Ensure all outputs are strings (minimal validation)
    for provider_name, output in list(provider_summaries.items()):
        if not isinstance(output, str):
            provider_summaries[provider_name] = str(output)

    # Analyze consistency across provider outputs
    consistency_analysis = response_processor.analyze_consistency(provider_summaries)

    # Normalize responses to common structure
    normalized_results = response_processor.normalize_response(provider_summaries)

    # Record job in frontend cache for visualization
    try:
        import time
        start_time = time.time()
        # Simulate execution time calculation (in a real implementation, you'd track this)
        execution_time = time.time() - start_time

        # Extract models from providers
        models = {}
        for provider_config in req.providers:
            if provider_config.model:
                models[provider_config.name] = provider_config.model

        # Record the job
        frontend_url = get_config_value("FRONTEND_URL", "http://frontend:3000", section="summarizer_hub", env_key="FRONTEND_URL")
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{frontend_url}/api/summarizer/record-job", json={
                "job_id": f"ensemble_{int(time.time())}",
                "text_length": len(req.text),
                "providers": [p.name for p in req.providers],
                "models": models,
                "prompt": req.prompt,
                "execution_time": execution_time,
                "results": {
                    "summaries": provider_summaries,
                    "normalized": normalized_results
                },
                "consistency_analysis": consistency_analysis
            })
    except Exception as e:
        # Don't fail the summarization if caching fails
        fire_and_forget("warning", "cache_recording_failed", ServiceNames.SUMMARIZER_HUB, {"error": str(e)})

    return {
        "summaries": provider_summaries,
        "analysis": consistency_analysis,
        "normalized": normalized_results
    }


if __name__ == "__main__":
    """Run the Summarizer Hub service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )

