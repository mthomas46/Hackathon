"""Service: Summarizer Hub

Endpoints:
- POST /summarize/ensemble, GET /health

Responsibilities: Fan out summarization to configured providers, merge outputs,
and return normalized results. Supports rate limiting via env toggle.
Dependencies: shared middlewares, optional Bedrock native/HTTP, httpx.
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

app = FastAPI(title="Summarizer Hub", version="0.1.0")
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name="summarizer-hub")
attach_self_register(app, "summarizer-hub")
_rate_limit_enabled = str(get_config_value("RATE_LIMIT_ENABLED", False, section="summarizer_hub", env_key="RATE_LIMIT_ENABLED")).strip().lower() in ("1", "true", "yes")
if _rate_limit_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        limits={
            "/summarize/ensemble": (2.0, 5),
        },
    )


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "summarizer-hub"}


class ProviderConfig(BaseModel):
    name: str  # e.g., "ollama", "openai", "anthropic", "grok"
    model: Optional[str] = None
    endpoint: Optional[str] = None  # for local gateways
    api_key: Optional[str] = None
    region: Optional[str] = None  # for bedrock
    profile: Optional[str] = None  # for bedrock (optional named profile)


class SummarizeRequest(BaseModel):
    text: str
    providers: List[ProviderConfig]
    prompt: Optional[str] = None
    # Optional: allow referencing hub config providers by name only (no model/endpoint provided inline)
    use_hub_config: Optional[bool] = True




@app.post("/summarize/ensemble")
async def summarize_ensemble(req: SummarizeRequest):
    fire_and_forget("info", "summarize_ensemble", ServiceNames.SUMMARIZER_HUB, {"providers": [p.name for p in req.providers] if req.providers else []})
    if not req.providers:
        raise HTTPException(status_code=400, detail="providers required")
    summaries: Dict[str, str] = {}
    hub_cfg = config_manager.load_hub_config() if req.use_hub_config else {}
    for p in req.providers:
        if hub_cfg:
            p = config_manager.merge_provider_from_config(p, hub_cfg)
        output = await provider_manager.summarize_with_provider(p.name, p, req.prompt, req.text)
        summaries[p.name] = output
    # Minimal schema validation: ensure each provider returns string output
    for k, v in list(summaries.items()):
        if not isinstance(v, str):
            summaries[k] = str(v)
    analysis = response_processor.analyze_consistency(summaries)
    normalized = response_processor.normalize_response(summaries)
    return {"summaries": summaries, "analysis": analysis, "normalized": normalized}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5060)

