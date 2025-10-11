"""
Standardized error response models.

Provides consistent error responses across all API endpoints.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """
    Detailed error information.
    
    Provides specific information about an error occurrence.
    """
    field: Optional[str] = Field(None, description="Field name if error is field-specific")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")
    

class ErrorResponse(BaseModel):
    """
    Standardized error response model.
    
    All API errors should return this format for consistency.
    """
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="High-level error message")
    error_code: str = Field(..., description="Machine-readable error code")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    path: Optional[str] = Field(None, description="Request path where error occurred")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "status_code": 422,
                "details": [
                    {
                        "field": "query",
                        "message": "Query must be at least 3 characters",
                        "code": "MIN_LENGTH"
                    }
                ],
                "request_id": "abc123",
                "timestamp": "2025-10-11T12:00:00",
                "path": "/api/v1/search"
            }
        }


class ErrorCode:
    """
    Standardized error codes.
    
    Machine-readable error codes for programmatic handling.
    """
    # Generic errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Database errors
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    
    # Storage errors
    STORAGE_ERROR = "STORAGE_ERROR"
    REDIS_ERROR = "REDIS_ERROR"
    CHROMADB_ERROR = "CHROMADB_ERROR"
    
    # AI/Model errors
    MODEL_ERROR = "MODEL_ERROR"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    EMBEDDING_GENERATION_FAILED = "EMBEDDING_GENERATION_FAILED"
    
    # Ingestion errors
    INGESTION_ERROR = "INGESTION_ERROR"
    DOCUMENT_PARSING_ERROR = "DOCUMENT_PARSING_ERROR"
    
    # Validation errors
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Configuration errors
    CONFIG_ERROR = "CONFIG_ERROR"
    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"


def create_error_response(
    error_message: str,
    error_code: str,
    status_code: int,
    details: Optional[List[ErrorDetail]] = None,
    request_id: Optional[str] = None,
    path: Optional[str] = None
) -> ErrorResponse:
    """
    Create a standardized error response.
    
    Args:
        error_message: Human-readable error message
        error_code: Machine-readable error code
        status_code: HTTP status code
        details: Optional detailed error information
        request_id: Optional request ID for tracing
        path: Optional request path
    
    Returns:
        ErrorResponse object
    """
    return ErrorResponse(
        error=error_message,
        error_code=error_code,
        status_code=status_code,
        details=details,
        request_id=request_id,
        path=path
    )

