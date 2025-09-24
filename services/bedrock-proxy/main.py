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

from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel, field_validator

from services.shared.utilities.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore

try:
    from .modules.processor import process_invoke_request
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from modules.processor import process_invoke_request

# ============================================================================
# STANDARDIZED CONFIGURATION
# ============================================================================
from services.shared.infrastructure.config import load_service_config
from services.shared.utilities import setup_common_middleware
from services.shared.presentation.responses import create_error_response, create_success_response
from services.shared.monitoring.health import register_health_endpoints

# Load standardized configuration
config = load_service_config(
    service_type="bedrock-proxy",
    config_file="./config.yaml"  # Optional config file override
)

# Service configuration from standardized config
SERVICE_NAME = config.service_name
SERVICE_TITLE = config.service_description or "Bedrock Proxy Stub"
SERVICE_VERSION = config.service_version
DEFAULT_PORT = config.port

app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Local AI proxy service for structured response generation",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup standardized middleware and utilities
setup_common_middleware(app, service_name=SERVICE_NAME)

# Register standardized health endpoints
register_health_endpoints(app, SERVICE_NAME, SERVICE_VERSION)


@app.get("/health")
async def health():
    """Enhanced health check endpoint with standardized response."""
    try:
        return create_success_response(
            data={
                "status": "healthy",
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "features": {
                    "ai_proxy": True,
                    "structured_responses": True,
                    "template_processing": True,
                    "stub_mode": True,
                }
            },
            message="Bedrock proxy service is operational"
        )
    except Exception as e:
        return create_error_response(
            message=f"Health check failed: {str(e)}",
            error_code="HEALTH_CHECK_FAILED",
            details={"error": str(e)}
        )


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

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v):
        """Validate that prompt is a string if provided."""
        if v is not None and not isinstance(v, str):
            raise ValueError("Prompt must be a string value")
        return v

    @field_validator("template")
    @classmethod
    def validate_template(cls, v):
        """Validate template is one of the supported types."""
        if v is not None:
            valid_templates = [
                "summary",
                "risks",
                "decisions",
                "pr_confidence",
                "life_of_ticket",
            ]
            if v.lower() not in valid_templates and v.strip():
                raise ValueError(
                    f'Invalid template "{v}". Supported templates: {", ".join(valid_templates)}'
                )
        return v

    @field_validator("format")
    @classmethod
    def validate_format(cls, v):
        """Validate output format is supported."""
        if v is not None:
            valid_formats = ["md", "txt", "json"]
            if v.lower() not in valid_formats:
                raise ValueError(
                    f'Invalid format "{v}". Supported formats: {", ".join(valid_formats)}'
                )
        return v

    @field_validator("model")
    @classmethod
    def validate_model(cls, v):
        """Validate model name length."""
        if v is not None and len(v) > 100:
            raise ValueError("Model name exceeds maximum length of 100 characters")
        return v

    @field_validator("region")
    @classmethod
    def validate_region(cls, v):
        """Validate region name length."""
        if v is not None and len(v) > 50:
            raise ValueError("Region name exceeds maximum length of 50 characters")
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """Validate title length."""
        if v is not None and len(v) > 200:
            raise ValueError("Title exceeds maximum length of 200 characters")
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
        **(req.params or {}),  # Unpack additional parameters
    )


if __name__ == "__main__":
    """Run the Bedrock Proxy service directly."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=DEFAULT_PORT, log_level="info")
