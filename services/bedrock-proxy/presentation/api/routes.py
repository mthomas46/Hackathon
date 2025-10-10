"""API routes for Bedrock Proxy service."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...infrastructure.processor import process_invoke_request
from .models import InvokeRequest

# Create router
router = APIRouter(prefix="/api/v1", tags=["bedrock-proxy"])

# Simple response helpers
class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None


def create_success_response(data):
    """Create a success response."""
    return {"success": True, "data": data}


def create_error_response(message, **kwargs):
    """Create an error response."""
    return {"success": False, "message": message, **kwargs}


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
