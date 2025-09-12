"""Service: Bedrock Proxy (Stub)

Endpoints:
- POST /invoke, GET /health

Responsibilities: Provide a small local gateway interface to structure outputs
without calling external providers in tests.
Dependencies: shared middlewares.
"""
from fastapi import FastAPI
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any

from services.shared.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore
from .modules.processor import process_invoke_request

app = FastAPI(title="Bedrock Proxy Stub", version="0.1.0")
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name="bedrock-proxy")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "bedrock-proxy"}


class InvokeRequest(BaseModel):
    """Request model for invoke endpoint."""
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
        return v

    @field_validator('region')
    @classmethod
    def validate_region(cls, v):
        if v is not None:
            if len(v) > 50:
                raise ValueError('Region name too long (max 50 characters)')
        return v

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None and len(v) > 200:
            raise ValueError('Title too long (max 200 characters)')
        return v


@app.post("/invoke")
async def invoke(req: InvokeRequest):
    """Process invoke request with template-based response generation."""
    return process_invoke_request(
        prompt=req.prompt,
        template=req.template,
        format=req.format,
        title=req.title,
        model=req.model,
        region=req.region,
        params=req.params
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7090)


