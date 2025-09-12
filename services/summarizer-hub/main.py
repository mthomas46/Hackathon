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
import os
import httpx

from services.shared.logging import fire_and_forget  # type: ignore
from services.shared.middleware import RequestMetricsMiddleware, RequestIdMiddleware, RateLimitMiddleware  # type: ignore
from services.shared.utilities import attach_self_register  # type: ignore
from services.shared.config import load_yaml_config, get_config_value  # type: ignore
from services.shared.constants_new import ServiceNames  # type: ignore

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
def _load_hub_config() -> Dict[str, Any]:
    path = get_config_value("SH_CONFIG", "services/summarizer-hub/config.yaml", section="summarizer_hub", env_key="SH_CONFIG")
    return load_yaml_config(path)


def _merge_provider_from_config(p: ProviderConfig, cfg: Dict[str, Any]) -> ProviderConfig:
    # Find provider by name in config and fill missing fields
    providers = (cfg.get("providers") or [])
    for entry in providers:
        if str(entry.get("name")).lower() == p.name.lower():
            return ProviderConfig(
                name=p.name,
                model=p.model or entry.get("model"),
                endpoint=p.endpoint or entry.get("endpoint"),
                api_key=p.api_key or entry.get("api_key"),
                region=p.region or entry.get("region"),
                profile=p.profile or entry.get("profile"),
            )
    return p


def analyze_consistency(summaries: Dict[str, str]) -> Dict[str, Any]:
    # Simple diff-based analysis across provider outputs
    agreed: List[str] = []
    disagreements: Dict[str, List[str]] = {}
    # Tokenize by lines; naive approach for starter
    provider_lines = {k: set((v or "").splitlines()) for k, v in summaries.items()}
    if not provider_lines:
        return {"agreed": [], "differences": {}}
    # Agreed lines: intersection across providers
    lines_sets = list(provider_lines.values())
    intersection = set(lines_sets[0])
    for s in lines_sets[1:]:
        intersection &= s
    agreed = sorted(l for l in intersection if l.strip())
    # Differences per provider: lines not in intersection
    for name, lines in provider_lines.items():
        diff = sorted(l for l in lines if l.strip() and l not in intersection)
        if diff:
            disagreements[name] = diff
    return {"agreed": agreed, "differences": disagreements}


async def _summarize_with_ollama(p: ProviderConfig, prompt: Optional[str], text: str) -> str:
    ollama_host = get_config_value("OLLAMA_HOST", "http://localhost:11434", section="summarizer_hub", env_key="OLLAMA_HOST")
    url = (p.endpoint or ollama_host).rstrip("/") + "/api/generate"
    payload = {"model": p.model or "llama3", "prompt": ((prompt + "\n\n") if prompt else "") + text}
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            # Simplified: many gateways stream; assume full text under 'response'
            data = r.json()
            return str(data.get("response") or "")
        except Exception:
            return ""


async def _summarize_with_openai(p: ProviderConfig, prompt: Optional[str], text: str) -> str:
    # Placeholder stub; real implementation would call OpenAI chat/completions
    return ((prompt + "\n\n") if prompt else "") + text


async def _summarize_with_anthropic(p: ProviderConfig, prompt: Optional[str], text: str) -> str:
    # Placeholder stub
    return ((prompt + "\n\n") if prompt else "") + text


async def _summarize_with_grok(p: ProviderConfig, prompt: Optional[str], text: str) -> str:
    # Placeholder stub
    return ((prompt + "\n\n") if prompt else "") + text


async def _summarize_with_bedrock(p: ProviderConfig, prompt: Optional[str], text: str) -> str:
    """Invoke Amazon Bedrock using native AWS SDK if configured, else proxy HTTP.

    Native path if AWS_REGION (or p.region) is set and boto3 is available; otherwise, try HTTP gateway.
    """
    content = ((prompt + "\n\n") if prompt else "") + text
    # Try native SDK
    try:
        import boto3  # type: ignore
        import json as pyjson
        region = p.region or get_config_value("BEDROCK_REGION", os.environ.get("AWS_REGION") or "us-east-1", section="summarizer_hub", env_key="BEDROCK_REGION")
        model_id = p.model or get_config_value("BEDROCK_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0", section="summarizer_hub", env_key="BEDROCK_MODEL")
        client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=(__import__('services.shared.credentials', fromlist=['get_secret']).get_secret("AWS_ACCESS_KEY_ID")),
            aws_secret_access_key=(__import__('services.shared.credentials', fromlist=['get_secret']).get_secret("AWS_SECRET_ACCESS_KEY")),
            aws_session_token=(__import__('services.shared.credentials', fromlist=['get_secret']).get_secret("AWS_SESSION_TOKEN")),
        )
        # Anthropic Messages format
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "messages": [{"role": "user", "content": content}],
        }
        resp = client.invoke_model(modelId=model_id, body=pyjson.dumps(body))
        payload = pyjson.loads(resp.get("body", b"{}"))
        # Extract text depending on provider schema
        if isinstance(payload, dict):
            # Anthropic returns content array with text
            parts = payload.get("content") or []
            texts = []
            for part in parts:
                t = part.get("text") or part.get("content")
                if t:
                    texts.append(t)
            return "\n".join(texts)
        return ""
    except Exception:
        pass

    # Fallback: HTTP proxy
    url = (p.endpoint or get_config_value("BEDROCK_ENDPOINT", "", section="summarizer_hub", env_key="BEDROCK_ENDPOINT") or "").strip()
    if not url:
        return content
    headers = {}
    from services.shared.credentials import get_secret as _get_secret
    api_key = p.api_key or _get_secret("BEDROCK_API_KEY") or get_config_value("BEDROCK_API_KEY", None, section="summarizer_hub", env_key="BEDROCK_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "model": p.model or get_config_value("BEDROCK_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0", section="summarizer_hub", env_key="BEDROCK_MODEL"),
        "region": p.region or get_config_value("BEDROCK_REGION", os.environ.get("AWS_REGION", "us-east-1"), section="summarizer_hub", env_key="BEDROCK_REGION"),
        "prompt": content,
    }
    async with httpx.AsyncClient(timeout=90) as client:
        try:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            return str(data.get("output") or data.get("response") or "")
        except Exception:
            return ""


PROVIDER_IMPLS = {
    "ollama": _summarize_with_ollama,
    "openai": _summarize_with_openai,
    "anthropic": _summarize_with_anthropic,
    "grok": _summarize_with_grok,
    "bedrock": _summarize_with_bedrock,
}


@app.post("/summarize/ensemble")
async def summarize_ensemble(req: SummarizeRequest):
    fire_and_forget("info", "summarize_ensemble", ServiceNames.SUMMARIZER_HUB, {"providers": [p.name for p in req.providers] if req.providers else []})
    if not req.providers:
        raise HTTPException(status_code=400, detail="providers required")
    summaries: Dict[str, str] = {}
    hub_cfg = _load_hub_config() if req.use_hub_config else {}
    for p in req.providers:
        if hub_cfg:
            p = _merge_provider_from_config(p, hub_cfg)
        impl = PROVIDER_IMPLS.get(p.name.lower())
        if impl is None:
            # Fallback: echo with tag
            content = (req.prompt + "\n\n" if req.prompt else "") + req.text
            summaries[p.name] = f"[{p.name}]\n" + content
            continue
        output = await impl(p, req.prompt, req.text)
        summaries[p.name] = output or f"[{p.name}]\n" + ((req.prompt + "\n\n") if req.prompt else "") + req.text
    # Minimal schema validation: ensure each provider returns string output
    for k, v in list(summaries.items()):
        if not isinstance(v, str):
            summaries[k] = str(v)
    analysis = analyze_consistency(summaries)
    # Normalize outputs to a common shape for downstream consumers
    normalized: Dict[str, Dict[str, Any]] = {}
    for name, text in summaries.items():
        lines = (text or "").splitlines()
        bullets = [l.strip("- ") for l in lines if l.strip().startswith("-")][:20]
        risks = [l for l in lines if "risk" in l.lower()][:10]
        decisions = [l for l in lines if "decision" in l.lower()][:10]
        normalized[name] = {
            "summary_text": text,
            "bullets": bullets,
            "risks": risks,
            "decisions": decisions,
        }
    return {"summaries": summaries, "analysis": analysis, "normalized": normalized}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5060)

