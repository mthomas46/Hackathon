"""Service: Bedrock Proxy (Stub)

Endpoints:
- POST /invoke, GET /health

Responsibilities: Provide a small local gateway interface to structure outputs
without calling external providers in tests.
Dependencies: shared middlewares.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any, List

from services.shared.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore

app = FastAPI(title="Bedrock Proxy Stub", version="0.1.0")
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name="bedrock-proxy")


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

    # Remove SQL injection patterns
    text = re.sub(r';\s*--', '', text, flags=re.IGNORECASE)  # Remove SQL comments
    text = re.sub(r';\s*SELECT\s+.*?\s+FROM', '; SELECT * FROM dummy', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove environment variable patterns
    text = re.sub(r'\$\{[^}]+\}', '', text)

    # Remove path traversal patterns
    text = re.sub(r'\.\./', '', text)
    text = re.sub(r'\\', '', text)  # Remove backslashes
    text = re.sub(r'/', '', text)  # Remove forward slashes in path patterns

    # Remove null bytes and other control characters
    text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\r\t')

    return text.strip()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "bedrock-proxy"}


class InvokeRequest(BaseModel):
    model: Optional[str] = None
    region: Optional[str] = None
    prompt: Optional[str] = None
    # Allow generic passthrough fields
    params: Optional[Dict[str, Any]] = None
    template: Optional[str] = None  # summary|risks|decisions|pr_confidence|life_of_ticket
    style: Optional[str] = None  # bullet|paragraph
    format: Optional[str] = "md"  # md|txt|json
    title: Optional[str] = None

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v):
        if v is not None and not isinstance(v, str):
            raise ValueError('Prompt must be a string')
        return v

    @field_validator('template')
    @classmethod
    def validate_template(cls, v):
        if v is not None:
            valid_templates = ['summary', 'risks', 'decisions', 'pr_confidence', 'life_of_ticket']
            if v.lower() not in valid_templates and v.strip():
                raise ValueError(f'Invalid template: {v}. Must be one of {valid_templates}')
        return v

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        if v is not None:
            valid_formats = ['md', 'txt', 'json']
            if v.lower() not in valid_formats:
                raise ValueError(f'Invalid format: {v}. Must be one of {valid_formats}')
        return v

    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        if v is not None:
            if len(v) > 100:
                raise ValueError('Model name too long (max 100 characters)')
            # Sanitize dangerous content
            v = sanitize_for_response(v)
        return v

    @field_validator('region')
    @classmethod
    def validate_region(cls, v):
        if v is not None:
            if len(v) > 50:
                raise ValueError('Region name too long (max 50 characters)')
            # Sanitize dangerous content
            v = sanitize_for_response(v)
        return v

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None and len(v) > 200:
            raise ValueError('Title too long (max 200 characters)')
        return v


def _bullets_from_text(text: str, max_items: int = 5) -> List[str]:
    bullets: List[str] = []
    for line in (text or "").splitlines():
        s = line.strip(" -\t")
        if not s:
            continue
        if len(s) > 2:
            bullets.append(s)
        if len(bullets) >= max_items:
            break
    if not bullets:
        bullets = ["No content provided.", "Add more details to the prompt."]
    return bullets


def _render_md(title: str, sections: Dict[str, List[str]]) -> str:
    lines: List[str] = [f"# {title}"]
    for h, items in sections.items():
        lines.append("")
        lines.append(f"## {h}")
        for it in items:
            lines.append(f"- {it}")
    return "\n".join(lines)


def _render_txt(title: str, sections: Dict[str, List[str]]) -> str:
    lines: List[str] = [title]
    for h, items in sections.items():
        lines.append(f"\n{h}:")
        for it in items:
            lines.append(f"- {it}")
    return "\n".join(lines)


@app.post("/invoke")
async def invoke(req: InvokeRequest):
    # Sanitize the prompt to prevent XSS attacks
    text = sanitize_for_response(req.prompt or "").strip()
    template = (req.template or "").lower()
    fmt = (req.format or "md").lower()

    # Auto-detect template if not explicitly provided
    if not template and text:
        text_lower = text.lower()
        if "summary" in text_lower:
            template = "summary"
        elif "risk" in text_lower:
            template = "risks"
        elif "decision" in text_lower:
            template = "decisions"
        elif ("pr" in text_lower or "pull request" in text_lower) and "confidence" in text_lower:
            template = "pr_confidence"
        elif ("life" in text_lower or "track" in text_lower) and "ticket" in text_lower:
            template = "life_of_ticket"

    title = sanitize_for_response(req.title) if req.title else (
        "PR Confidence Report" if template == "pr_confidence" else (
            "Life of the Ticket" if template == "life_of_ticket" else (
                "Summary" if template == "summary" else "Bedrock Proxy Output"
            )
        )
    )

    # Build canned content
    sections: Dict[str, List[str]] = {}
    if not text:
        sections["Notes"] = ["Empty prompt received."]
    elif template == "summary":
        sections["Summary"] = _bullets_from_text(text, 5)
        sections["Key Points"] = ["Decision captured", "Risks identified", "Actions listed"]
    elif template == "risks":
        sections["Risks"] = [
            "Ambiguous requirements may delay delivery",
            "Insufficient test coverage could miss regressions",
            "Integration dependencies might slip schedules",
        ]
        sections["Mitigations"] = [
            "Clarify acceptance criteria with PO",
            "Add unit/integration tests",
            "Decouple feature flags to reduce risk",
        ]
    elif template == "decisions":
        sections["Decisions"] = [
            "Use FastAPI for microservices",
            "Adopt Redis Pub/Sub for events",
            "Store short-term context in memory-agent",
        ]
        sections["Rationale"] = [
            "Fast API iteration and testability",
            "Simple, reliable eventing",
            "Lightweight context persistence",
        ]
    elif template == "pr_confidence":
        sections["Inputs"] = ["Jira: TICKET-123", "GitHub PR: org/repo#42", "Confluence: Design v1"]
        sections["Extracted Endpoints"] = ["/hello", "/health"]
        sections["Confidence"] = ["Score: 82", "Implements 2/2 endpoints", "No extra endpoints detected"]
        sections["Suggestions"] = ["Add negative tests", "Document error codes in OpenAPI"]
    elif template == "life_of_ticket":
        sections["Timeline"] = [
            "2025-01-01T09:00Z — jira — To Do -> In Progress",
            "2025-01-02T10:00Z — github — PR opened (#42)",
            "2025-01-03T16:00Z — jira — In Review -> Done",
        ]
        sections["Summary"] = ["Work completed", "Docs updated", "Tests passing"]
    else:
        # Default echo-like but structured summary
        sections["Echo"] = _bullets_from_text(text, 5)

    # Sanitize all fields for response
    safe_model = sanitize_for_response(req.model) if req.model else None
    safe_region = sanitize_for_response(req.region) if req.region else None

    if fmt == "json":
        return {
            "title": title,
            "model": safe_model,
            "region": safe_region,
            "sections": sections,
        }
    body = _render_md(title, sections) if fmt == "md" else _render_txt(title, sections)
    return {
        "output": body,
        "model": safe_model,
        "region": safe_region
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7090)


