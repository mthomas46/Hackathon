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

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel, field_validator

# Add shared infrastructure to path
project_root = Path(__file__).parent.parent.parent
shared_path = project_root / "services" / "shared"
sys.path.insert(0, str(shared_path))

try:
    from services.shared.utilities.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore
except ImportError:
    # Fallback middleware classes
    class RequestIdMiddleware:
        def __init__(self, app): pass
        def __call__(self, scope, receive, send): pass

    class RequestMetricsMiddleware:
        def __init__(self, app): pass
        def __call__(self, scope, receive, send): pass

try:
    from .modules.processor import process_invoke_request
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from infrastructure.processor import process_invoke_request

# ============================================================================
# STANDARDIZED CONFIGURATION
# ============================================================================
try:
    from services.shared.infrastructure.config import load_service_config
    from services.shared.utilities import setup_common_middleware
    from services.shared.presentation.responses import create_error_response, create_success_response
    from services.shared.presentation.api.responses import APIResponse
    from services.shared.monitoring.health import register_health_endpoints
except ImportError:
    # Fallback implementations
    def load_service_config(**kwargs):
        return type('Config', (), {
            'service_name': 'bedrock-proxy',
            'service_description': 'Bedrock Proxy Service',
            'service_version': '1.0.0',
            'server': type('Server', (), {'host': '0.0.0.0', 'port': 5002})(),
            'port': 5002,
        })()

    def setup_common_middleware(app, **kwargs):
        pass

    def create_error_response(message, **kwargs):
        return {"success": False, "message": message, **kwargs}

    def create_success_response(data):
        return {"success": True, "data": data}

    class APIResponse(BaseModel):
        success: bool
        message: Optional[str] = None
        data: Optional[Any] = None

    def register_health_endpoints(app, *args, **kwargs):
        pass

# Load standardized configuration
config = load_service_config(
    service_type="bedrock-proxy",
    config_file="./config.yaml"  # Optional config file override
)

# Service configuration from standardized config
SERVICE_NAME = config.service_name
SERVICE_TITLE = config.service_description or "Bedrock Proxy Stub"
SERVICE_VERSION = config.service_version
DEFAULT_API_PORT = config.port

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

# Include presentation layer routes
try:
    from .presentation import api_router
    app.include_router(api_router)
except ImportError:
    # Fallback: include routes directly if presentation layer not available
    from .presentation.api.routes import router as api_router
    app.include_router(api_router)

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
        try:
            from .modules.validation import validate_prompt
            return validate_prompt(v)
        except ImportError:
            # Fallback validation
            if v is not None and not isinstance(v, str):
                raise ValueError("Prompt must be a string value")
            return v

    @field_validator("template")
    @classmethod
    def validate_template(cls, v):
        """Validate template is one of the supported types."""
        try:
            from .modules.validation import validate_template
            return validate_template(v)
        except ImportError:
            # Fallback validation
            if v is not None:
                valid_templates = [
                    "summary", "risks", "decisions",
                    "pr_confidence", "life_of_ticket",
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
        try:
            from .modules.validation import validate_format
            return validate_format(v)
        except ImportError:
            # Fallback validation
            if v is not None:
                valid_formats = ["md", "txt", "json"]
                if v.lower() not in valid_formats:
                    raise ValueError(
                        f'Invalid format "{v}". Supported formats: {", ".join(valid_formats)}'
                    )
            return (v or "md").lower()

    @field_validator("model")
    @classmethod
    def validate_model(cls, v):
        """Validate model name length."""
        try:
            from .modules.validation import validate_model
            return validate_model(v)
        except ImportError:
            # Fallback validation
            if v is not None and len(v) > 100:
                raise ValueError("Model name exceeds maximum length of 100 characters")
            return v

    @field_validator("region")
    @classmethod
    def validate_region(cls, v):
        """Validate region name length."""
        try:
            from .modules.validation import validate_region
            return validate_region(v)
        except ImportError:
            # Fallback validation
            if v is not None and len(v) > 50:
                raise ValueError("Region name exceeds maximum length of 50 characters")
            return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """Validate title length."""
        try:
            from .modules.validation import validate_title
            return validate_title(v)
        except ImportError:
            # Fallback validation
            if v is not None and len(v) > 200:
                raise ValueError("Title exceeds maximum length of 200 characters")
            return v


if __name__ == "__main__":
    """Run the Bedrock Proxy service directly."""
    import uvicorn

    uvicorn.run(app, host=config.server.host, port=config.server.port)
