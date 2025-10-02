"""API routes for Bedrock Proxy service."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, field_validator

from ...infrastructure.processor import process_invoke_request
from ...infrastructure.validation_utils.validation import (
    validate_model,
    validate_region,
    validate_template,
    validate_format,
    validate_title,
)

# Create router
router = APIRouter(prefix="/api/v1", tags=["bedrock-proxy"])

# Import shared response models
try:
    from services.shared.presentation.api.responses import (
        create_success_response,
        create_error_response,
        APIResponse,
    )
except ImportError:
    # Fallback implementations
    class APIResponse(BaseModel):
        success: bool
        message: Optional[str] = None
        data: Optional[Any] = None

    def create_success_response(data):
        return {"success": True, "data": data}

    def create_error_response(message, **kwargs):
        return {"success": False, "message": message, **kwargs}


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
    """Input prompt for AI processing."""

    template: Optional[str] = None
    """Response template to use (summary, risks, decisions, pr_confidence, life_of_ticket)."""

    format: Optional[str] = None
    """Output format (md, txt, json)."""

    title: Optional[str] = None
    """Custom title for the response."""

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v):
        """Validate that prompt is a string if provided."""
        try:
            from ...infrastructure.validation_utils.validation import validate_prompt
            return validate_prompt(v)
        except ImportError:
            # Fallback validation
            if v is not None and not isinstance(v, str):
                raise ValueError("Prompt must be a string value")
            return v

    @field_validator("model")
    @classmethod
    def validate_model_field(cls, v):
        """Validate model field."""
        return validate_model(v)

    @field_validator("region")
    @classmethod
    def validate_region_field(cls, v):
        """Validate region field."""
        return validate_region(v)

    @field_validator("template")
    @classmethod
    def validate_template_field(cls, v):
        """Validate template field."""
        return validate_template(v)

    @field_validator("format")
    @classmethod
    def validate_format_field(cls, v):
        """Validate format field."""
        return validate_format(v)

    @field_validator("title")
    @classmethod
    def validate_title_field(cls, v):
        """Validate title field."""
        return validate_title(v)


class InvokeResponse(BaseModel):
    """Response model for AI invoke endpoint."""

    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@router.post(
    "/invoke",
    response_model=InvokeResponse,
    summary="Process AI Invoke Request",
    description="Process an AI invoke request with template-based response generation. Supports structured output formatting for consistent AI responses.",
    responses={
        200: {"description": "Request processed successfully"},
        400: {"description": "Invalid request parameters"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)
async def invoke(request: InvokeRequest) -> Dict[str, Any]:
    """Process AI invoke request with structured response generation.

    This endpoint provides a local AI proxy that generates structured responses
    using predefined templates. Useful for testing and development scenarios
    where consistent, formatted AI outputs are required.

    Args:
        request: Invoke request with prompt and formatting options

    Returns:
        Structured response with formatted content

    Raises:
        HTTPException: For validation errors or processing failures
    """
    try:
        # Process the request using the infrastructure layer
        result = await process_invoke_request(
            prompt=request.prompt,
            model=request.model,
            region=request.region,
            template=request.template,
            format=request.format,
            title=request.title,
        )

        return create_success_response(result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.get(
    "/health",
    summary="Service Health Check",
    description="Returns the current health status of the Bedrock Proxy service including operational metrics and feature availability.",
    response_model=APIResponse,
    responses={
        200: {"description": "Service is healthy and operational"},
        500: {"description": "Service health check failed"}
    }
)
async def health():
    """Enhanced health check endpoint with standardized response."""
    try:
        return create_success_response(
            data={
                "status": "healthy",
                "service": "bedrock-proxy",
                "version": "1.0.0",
                "features": {
                    "ai_proxy": True,
                    "structured_responses": True,
                    "template_processing": True,
                    "stub_mode": True,
                }
            }
        )
    except Exception as e:
        return create_error_response(
            message=f"Health check failed: {str(e)}",
            error_code="HEALTH_CHECK_FAILED",
            details={"error": str(e)}
        )
