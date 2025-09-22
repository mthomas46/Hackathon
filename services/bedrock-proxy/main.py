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

import time
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel, field_validator

from services.shared.core.constants_new import ServiceNames
from services.shared.utilities.logging_client import get_log_collector_client
from services.shared.utilities.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore

try:
    from .modules.processor import process_invoke_request
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from modules.processor import process_invoke_request

# Service configuration constants
SERVICE_NAME = "bedrock-proxy"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = 7090

# Initialize log collector client
logger_client = None

app = FastAPI(
    title="Bedrock Proxy Stub",
    version=SERVICE_VERSION,
    description="Local AI proxy service for structured response generation",
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name=SERVICE_NAME)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global logger_client
    try:
        logger_client = await get_log_collector_client(ServiceNames.BEDROCK_PROXY)
        if logger_client:
            await logger_client.log_business_event(
                "bedrock_proxy_startup",
                {
                    "version": SERVICE_VERSION,
                    "capabilities": [
                        "structured_response_generation",
                        "template_based_responses",
                        "invoke_processing",
                        "stub_mode",
                    ],
                    "integrations": ["log_collector"],
                    "features": ["predictable_responses", "testing_support", "template_engine", "structured_output"],
                },
            )
            await logger_client.log_info(
                "Bedrock Proxy service started",
                {"stub_mode": True, "template_based_responses": True, "structured_output": True},
            )
    except Exception as e:
        print(f"Failed to initialize log collector client: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if logger_client:
        try:
            await logger_client.log_info("Bedrock Proxy service shutting down")
        except Exception:
            pass


@app.get("/health")
async def health():
    """Health check endpoint returning service status and basic information."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "Bedrock proxy stub service is operational",
    }


class InvokeRequest(BaseModel):
    """
    Request model for AI invoke endpoint with structured response generation.

    Supports template-based response formatting for consistent AI
    outputs. All fields are optional to allow flexible usage patterns.
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
            valid_templates = ["summary", "risks", "decisions", "pr_confidence", "life_of_ticket"]
            if v.lower() not in valid_templates and v.strip():
                raise ValueError(f'Invalid template "{v}". Supported templates: {", ".join(valid_templates)}')
        return v

    @field_validator("format")
    @classmethod
    def validate_format(cls, v):
        """Validate output format is supported."""
        if v is not None:
            valid_formats = ["md", "txt", "json"]
            if v.lower() not in valid_formats:
                raise ValueError(f'Invalid format "{v}". Supported formats: {", ".join(valid_formats)}')
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
    """
    Process AI invoke request with template-based response generation.

    Accepts a prompt and optional template/format parameters to generate
    structured AI responses without external API calls. Supports
    multiple output formats and template types for consistent testing
    scenarios.
    """
    start_time = time.time()
    request_id = f"bedrock_invoke_{int(time.time() * 1000)}"

    try:
        # Log invoke request start
        if logger_client:
            await logger_client.log_business_event(
                "bedrock_invoke_started",
                {
                    "request_id": request_id,
                    "model": req.model,
                    "template": req.template,
                    "format": req.format,
                    "region": req.region,
                    "prompt_length": len(req.prompt) if req.prompt else 0,
                    "has_title": bool(req.title),
                    "has_params": bool(req.params),
                    "stub_mode": True,
                },
            )

            await logger_client.log_info(
                "Processing Bedrock invoke request",
                {
                    "request_id": request_id,
                    "template": req.template,
                    "format": req.format,
                    "model": req.model,
                    "prompt_preview": req.prompt[:100] + "..." if req.prompt and len(req.prompt) > 100 else req.prompt,
                },
            )

        result = process_invoke_request(
            prompt=req.prompt,
            template=req.template,
            format=req.format,
            title=req.title,
            model=req.model,
            region=req.region,
            **(req.params or {}),  # Unpack additional parameters
        )

        processing_time = time.time() - start_time

        # Calculate response metrics
        response_length = len(str(result)) if result else 0
        has_structured_output = isinstance(result, dict) and "content" in result

        # Log successful invoke completion
        if logger_client:
            await logger_client.log_business_event(
                "bedrock_invoke_completed",
                {
                    "request_id": request_id,
                    "model": req.model,
                    "template": req.template,
                    "format": req.format,
                    "response_length": response_length,
                    "processing_time_seconds": processing_time,
                    "structured_output": has_structured_output,
                    "success": True,
                },
            )

            await logger_client.log_performance_metric(
                "bedrock_invoke",
                processing_time,
                {
                    "request_id": request_id,
                    "model": req.model,
                    "template": req.template,
                    "format": req.format,
                    "invoke_success": True,
                    "stub_mode": True,
                },
            )

        return result

    except Exception as e:
        error_time = time.time() - start_time

        # Log invoke failure
        if logger_client:
            await logger_client.log_error(
                f"Bedrock invoke failed: {str(e)}",
                {
                    "request_id": request_id,
                    "model": req.model if "req" in locals() else None,
                    "template": req.template if "req" in locals() else None,
                    "format": req.format if "req" in locals() else None,
                    "error_type": type(e).__name__,
                    "processing_time_seconds": error_time,
                    "stub_mode": True,
                },
                error=e,
            )

            await logger_client.log_business_event(
                "bedrock_invoke_failed",
                {
                    "request_id": request_id,
                    "model": req.model if "req" in locals() else None,
                    "template": req.template if "req" in locals() else None,
                    "format": req.format if "req" in locals() else None,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_time_seconds": error_time,
                },
            )

        raise


if __name__ == "__main__":
    """Run the Bedrock Proxy service directly."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info")
