"""Service: Bedrock Proxy (Stub)

Endpoints:
- POST /invoke: Process invoke requests with template-based response generation
- GET /health: Health check endpoint

Responsibilities:
- Provide a local gateway interface for structured AI outputs
- Support template-based response formatting without external API calls
- Enable testing scenarios with predictable, structured responses

Dependencies: shared middlewares for request tracking and metrics.
"""
from fastapi import FastAPI
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any

from services.shared.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore
from .modules.processor import process_invoke_request

# Service configuration constants
SERVICE_NAME = "bedrock-proxy"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = 7090

app = FastAPI(
    title="Bedrock Proxy Stub",
    version=SERVICE_VERSION,
    description="Local AI proxy service for structured response generation"
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name=SERVICE_NAME)


@app.get("/health")
async def health():
    """Health check endpoint returning service status and basic information."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "Bedrock proxy stub service is operational"
    }


class InvokeRequest(BaseModel):
    """Request model for AI invoke endpoint with structured response generation.

    Supports template-based response formatting for consistent AI outputs.
    All fields are optional to allow flexible usage patterns.
    """
    model: Optional[str] = None
    """AI model identifier (e.g., 'claude-3-sonnet', 'gpt-4')."""

    region: Optional[str] = None
    """AWS region for model deployment (e.g., 'us-east-1')."""

    prompt: Optional[str] = None
    """Input prompt text for AI processing."""

    params: Optional[Dict[str, Any]] = None
    """Additional parameters to pass through to the AI model."""

    template: Optional[str] = None
    """Response template type: summary|risks|decisions|pr_confidence|life_of_ticket"""

    style: Optional[str] = None
    """Output style format: bullet|paragraph (currently unused)."""

    format: Optional[str] = "md"
    """Output format: md|txt|json"""

    title: Optional[str] = None
    """Custom title for the generated response."""

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v):
        """Validate that prompt is a string if provided."""
        if v is not None and not isinstance(v, str):
            raise ValueError('Prompt must be a string value')
        return v

    @field_validator('template')
    @classmethod
    def validate_template(cls, v):
        """Validate template is one of the supported types."""
        if v is not None:
            valid_templates = ['summary', 'risks', 'decisions', 'pr_confidence', 'life_of_ticket']
            if v.lower() not in valid_templates and v.strip():
                raise ValueError(f'Invalid template "{v}". Supported templates: {", ".join(valid_templates)}')
        return v

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        """Validate output format is supported."""
        if v is not None:
            valid_formats = ['md', 'txt', 'json']
            if v.lower() not in valid_formats:
                raise ValueError(f'Invalid format "{v}". Supported formats: {", ".join(valid_formats)}')
        return v

    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        """Validate model name length."""
        if v is not None and len(v) > 100:
            raise ValueError('Model name exceeds maximum length of 100 characters')
        return v

    @field_validator('region')
    @classmethod
    def validate_region(cls, v):
        """Validate region name length."""
        if v is not None and len(v) > 50:
            raise ValueError('Region name exceeds maximum length of 50 characters')
        return v

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate title length."""
        if v is not None and len(v) > 200:
            raise ValueError('Title exceeds maximum length of 200 characters')
        return v


@app.post("/invoke")
async def invoke(req: InvokeRequest):
    """Process AI invoke request with template-based response generation.

    Accepts a prompt and optional template/format parameters to generate
    structured AI responses without external API calls. Supports multiple
    output formats and template types for consistent testing scenarios.
    """
    return process_invoke_request(
        prompt=req.prompt,
        template=req.template,
        format=req.format,
        title=req.title,
        model=req.model,
        region=req.region,
        **(req.params or {})  # Unpack additional parameters
    )


if __name__ == "__main__":
    """Run the Bedrock Proxy service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )


