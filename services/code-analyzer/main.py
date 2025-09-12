"""Service: Code Analyzer

Endpoints:
- POST /analyze/text, /analyze/files, /analyze/patch, /scan/secure
- POST /style/examples, GET /style/examples, GET /health

Responsibilities: Extract endpoints from code; manage style examples; optional doc-store writes.
Dependencies: shared models/envelopes/hashutil, optional Redis, ServiceClients.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import re
import os

try:
    import redis.asyncio as aioredis  # type: ignore
except Exception:
    aioredis = None

from services.shared.models import Document  # type: ignore
from services.shared.envelopes import DocumentEnvelope  # type: ignore
from services.shared.utilities import stable_hash  # type: ignore


from services.shared.middleware import RequestIdMiddleware, RequestMetricsMiddleware, RateLimitMiddleware  # type: ignore
from services.shared.utilities import attach_self_register  # type: ignore


app = FastAPI(title="Code Analyzer", version="0.1.0")
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name="code-analyzer")
# Rate limit heavy endpoints if enabled via environment toggle
if (os.environ.get("RATE_LIMIT_ENABLED", "").strip().lower() in ("1", "true", "yes")):
    app.add_middleware(
        RateLimitMiddleware,
        limits={
            "/analyze/files": (5.0, 10),
            "/analyze/patch": (5.0, 10),
            "/analyze/text": (10.0, 20),
            "/style/examples": (2.0, 5),
        },
    )

attach_self_register(app, "code-analyzer")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "code-analyzer"}


def _extract_endpoints_from_text(text: str) -> List[str]:
    if not text:
        return []
    out: List[str] = []
    seen = set()
    # Look for decorators and common route patterns (FastAPI/Flask/Express)
    for line in text.splitlines():
        s = line.strip()
        # FastAPI: @app.get("/path")
        if s.startswith("@app.") and "(" in s:
            m = re.search(r"\(\s*['\"]([^'\"]+)['\"]", s)
            if m:
                ep = m.group(1)
                if ep not in seen:
                    seen.add(ep); out.append(ep)
        # Flask: @app.route('/path') optionally with methods
        elif s.startswith("@app.route") and "(" in s:
            m = re.search(r"\(\s*['\"]([^'\"]+)['\"]", s)
            if m:
                ep = m.group(1)
                if ep not in seen:
                    seen.add(ep); out.append(ep)
        # Express: app.get('/path', ...) or router.post("/path", ...)
        elif ("app." in s or "router." in s) and "(" in s:
            m = re.search(r"\b(?:app|router)\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", s, flags=re.IGNORECASE)
            if m:
                ep = m.group(2)
                if ep not in seen:
                    seen.add(ep); out.append(ep)
        else:
            for m in re.findall(r"/(?:[a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-]+)*)", s):
                if m not in seen:
                    seen.add(m); out.append(m)
    return out[:200]


class AnalyzeTextRequest(BaseModel):
    content: str
    repo: Optional[str] = None
    path: Optional[str] = None
    correlation_id: Optional[str] = None
    language: Optional[str] = None
    style_examples: Optional[List[Dict[str, Any]]] = None


_style_examples: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/analyze/text")
async def analyze_text(req: AnalyzeTextRequest):
    eps = _extract_endpoints_from_text(req.content)
    summary = "\n".join(sorted(eps)) or "(no endpoints)"
    # Style guidance (optional)
    style_used: List[Dict[str, Any]] = []
    lang = (req.language or "").lower().strip()
    if req.style_examples:
        style_used.extend(req.style_examples)
    if lang and _style_examples.get(lang):
        style_used.extend(_style_examples[lang])
    style_meta = {"style_examples_used": style_used} if style_used else {}
    doc = Document(
        id=f"code:text:{stable_hash(req.content)[:8]}",
        source_type="code",
        title="Code Analysis",
        content=summary,
        content_hash=stable_hash(summary),
        metadata={"source_link": {"repo": req.repo, "path": req.path}, **style_meta},
        correlation_id=req.correlation_id,
    )
    env = DocumentEnvelope(
        id=doc.id,
        version=doc.version_tag,
        correlation_id=doc.correlation_id,
        source_refs=[{"repo": req.repo, "path": req.path}],
        content_hash=doc.content_hash,
        document=doc.model_dump(),
    )
    if aioredis:
        try:
            host = os.environ.get("REDIS_HOST")
            if host:
                client = aioredis.from_url(f"redis://{host}")
                await client.publish("docs.ingested.code", env.model_dump_json())
                await client.aclose()
        except Exception:
            pass
    # Also store in doc-store if configured using enveloped endpoint
    ds = os.environ.get("DOC_STORE_URL")
    if ds:
        try:
            from services.shared.clients import ServiceClients  # type: ignore
            svc = ServiceClients(timeout=10)
            await svc.post_json(f"{ds}/documents/enveloped", env.model_dump())
        except Exception:
            pass
    return env.model_dump()


class FileItem(BaseModel):
    path: str
    content: str


class AnalyzeFilesRequest(BaseModel):
    files: List[FileItem]
    repo: Optional[str] = None
    correlation_id: Optional[str] = None
    language: Optional[str] = None
    style_examples: Optional[List[Dict[str, Any]]] = None


@app.post("/analyze/files")
async def analyze_files(req: AnalyzeFilesRequest):
    text = "\n".join(f.content for f in req.files)
    eps = sorted(set(_extract_endpoints_from_text(text)))
    summary = "\n".join(eps) or "(no endpoints)"
    style_used: List[Dict[str, Any]] = []
    lang = (req.language or "").lower().strip()
    if req.style_examples:
        style_used.extend(req.style_examples)
    if lang and _style_examples.get(lang):
        style_used.extend(_style_examples[lang])
    style_meta = {"style_examples_used": style_used} if style_used else {}
    doc = Document(
        id=f"code:files:{stable_hash(summary)[:8]}",
        source_type="code",
        title="Code Analysis (files)",
        content=summary,
        content_hash=stable_hash(summary),
        metadata={"source_link": {"repo": req.repo, "files": [f.path for f in req.files]}, "files_analyzed": len(req.files), **style_meta},
        correlation_id=req.correlation_id,
    )
    return DocumentEnvelope(
        id=doc.id,
        version=doc.version_tag,
        correlation_id=doc.correlation_id,
        source_refs=doc.metadata.get("source_link") and [doc.metadata["source_link"]] or [],
        content_hash=doc.content_hash,
        document=doc.model_dump(),
    ).model_dump()


class AnalyzePatchRequest(BaseModel):
    patch: str
    repo: Optional[str] = None
    correlation_id: Optional[str] = None
    language: Optional[str] = None
    style_examples: Optional[List[Dict[str, Any]]] = None


@app.post("/analyze/patch")
async def analyze_patch(req: AnalyzePatchRequest):
    # Naive: analyze added lines only
    added = []
    for line in req.patch.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
    eps = sorted(set(_extract_endpoints_from_text("\n".join(added))))
    summary = "\n".join(eps) or "(no endpoints)"
    style_used: List[Dict[str, Any]] = []
    lang = (req.language or "").lower().strip()
    if req.style_examples:
        style_used.extend(req.style_examples)
    if lang and _style_examples.get(lang):
        style_used.extend(_style_examples[lang])
    style_meta = {"style_examples_used": style_used} if style_used else {}
    doc = Document(
        id=f"code:patch:{stable_hash(req.patch)[:8]}",
        source_type="code",
        title="Code Analysis (patch)",
        content=summary,
        content_hash=stable_hash(summary),
        metadata={"source_link": {"repo": req.repo}, **style_meta},
        correlation_id=req.correlation_id,
    )
    return DocumentEnvelope(
        id=doc.id,
        version=doc.version_tag,
        correlation_id=doc.correlation_id,
        source_refs=doc.metadata.get("source_link") and [doc.metadata["source_link"]] or [],
        content_hash=doc.content_hash,
        document=doc.model_dump(),
    ).model_dump()


class SecureScanRequest(BaseModel):
    content: str
    keywords: Optional[List[str]] = None


@app.post("/scan/secure")
async def scan_secure(req: SecureScanRequest):
    patterns = [
        r"api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9\-_/+=]{8,}['\"]",
        r"secret\s*[:=]",
        r"(password|passwd)\s*[:=]",
        r"Bearer\s+[A-Za-z0-9\-_.]+",
        r"AKIA[0-9A-Z]{16}",  # AWS Access Key ID
        r"-----BEGIN (?:RSA|EC|DSA) PRIVATE KEY-----",
        r"\bssn\b|social security",
        r"credit card|\b(?:\d{4}[- ]){3}\d{4}\b",
    ]
    for kw in req.keywords or []:
        try:
            patterns.append(re.escape(kw))
        except Exception:
            continue
    matches: List[str] = []
    for pat in patterns:
        for m in re.findall(pat, req.content, flags=re.IGNORECASE):
            if m not in matches:
                matches.append(m)
    return {"sensitive": bool(matches), "matches": matches[:100]}


class StyleExample(BaseModel):
    language: str
    snippet: str
    title: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    tags: Optional[List[str]] = None


class StyleExamplesPayload(BaseModel):
    items: List[StyleExample]


@app.post("/style/examples")
async def set_style_examples(payload: StyleExamplesPayload):
    # Replace registry for listed languages
    for ex in payload.items:
        lang = ex.language.lower().strip()
        _style_examples.setdefault(lang, [])
        _style_examples[lang].append(ex.model_dump())
    # Persist to doc-store if configured
    ds = os.environ.get("DOC_STORE_URL")
    if ds:
        try:
            from services.shared.clients import ServiceClients  # type: ignore
            svc = ServiceClients(timeout=10)
            for ex in payload.items:
                meta = {
                    "type": "style_example",
                    "language": ex.language,
                    "title": ex.title,
                    "description": ex.description,
                    "purpose": ex.purpose,
                    "tags": ex.tags or [],
                }
                await svc.post_json(f"{ds}/documents", {
                    "content": ex.snippet,
                    "content_hash": stable_hash(ex.snippet),
                    "metadata": meta,
                })
        except Exception:
            pass
    return {"status": "ok", "languages": list(_style_examples.keys())}


@app.get("/style/examples")
async def get_style_examples(language: Optional[str] = None):
    # Prefer doc-store when available
    ds = os.environ.get("DOC_STORE_URL")
    if ds:
        try:
            from services.shared.clients import ServiceClients  # type: ignore
            svc = ServiceClients(timeout=10)
            params = {"language": language} if language else None
            return await svc.get_json(f"{ds}/style/examples", params=params)
        except Exception:
            pass
    if language:
        return {"items": _style_examples.get(language.lower().strip(), [])}
    return {"items": [{"language": k, "count": len(v)} for k, v in _style_examples.items()]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5085)


