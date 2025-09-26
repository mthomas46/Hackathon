"""AI domain exceptions."""

from ..common.error_utils import DomainException


class AIRequestException(DomainException):
    """Exception related to AI requests."""
    pass


class AIModelException(DomainException):
    """Exception related to AI models."""
    pass


class InvalidModelException(AIModelException):
    """Exception raised when a model is invalid or unsupported."""

    def __init__(self, model_name: str, reason: str = None):
        """Initialize invalid model exception."""
        message = f"Invalid model '{model_name}'"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"model_name": model_name, "reason": reason})


class ModelNotFoundException(AIModelException):
    """Exception raised when a requested model is not found."""

    def __init__(self, model_name: str):
        """Initialize model not found exception."""
        super().__init__(f"Model '{model_name}' not found", {"model_name": model_name})


class RequestValidationException(AIRequestException):
    """Exception raised when an AI request fails validation."""

    def __init__(self, field: str, value: str, reason: str = None):
        """Initialize request validation exception."""
        message = f"Request validation failed for {field}"
        if reason:
            message += f": {reason}"
        super().__init__(message, {
            "field": field,
            "value": value,
            "reason": reason
        })


class ProcessingException(AIRequestException):
    """Exception raised during AI request processing."""

    def __init__(self, request_id: str, operation: str, reason: str = None):
        """Initialize processing exception."""
        message = f"Processing failed for request {request_id} during {operation}"
        if reason:
            message += f": {reason}"
        super().__init__(message, {
            "request_id": request_id,
            "operation": operation,
            "reason": reason
        })
