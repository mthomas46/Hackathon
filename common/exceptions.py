"""
Custom Exceptions for MCP System.

Provides consistent exception hierarchy for error handling.
"""

from typing import Any, Dict, Optional


# ============================================================================
# Base Exception
# ============================================================================

class MCPException(Exception):
    """Base exception for MCP system."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize MCP exception.
        
        Args:
            message: Error message
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "MCP_ERROR"
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


# ============================================================================
# Configuration Exceptions
# ============================================================================

class ConfigurationError(MCPException):
    """Configuration error."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            details=details
        )


# ============================================================================
# Data Exceptions
# ============================================================================

class DataNotFoundError(MCPException):
    """Data not found error."""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )


class DataValidationError(MCPException):
    """Data validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )


class DataIntegrityError(MCPException):
    """Data integrity error."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="INTEGRITY_ERROR"
        )


# ============================================================================
# Service Exceptions
# ============================================================================

class ServiceUnavailableError(MCPException):
    """Service unavailable error."""
    
    def __init__(self, service: str, reason: Optional[str] = None):
        message = f"Service unavailable: {service}"
        if reason:
            message += f" - {reason}"
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service, "reason": reason}
        )


class ServiceTimeoutError(MCPException):
    """Service timeout error."""
    
    def __init__(self, service: str, timeout_seconds: float):
        super().__init__(
            message=f"Service timeout: {service} ({timeout_seconds}s)",
            error_code="TIMEOUT",
            details={"service": service, "timeout_seconds": timeout_seconds}
        )


# ============================================================================
# Authorization Exceptions
# ============================================================================

class AuthorizationError(MCPException):
    """Authorization error."""
    
    def __init__(self, message: str = "Authorization required"):
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED"
        )


class ForbiddenError(MCPException):
    """Forbidden error."""
    
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            message=message,
            error_code="FORBIDDEN"
        )


# ============================================================================
# Rate Limiting Exceptions
# ============================================================================

class RateLimitError(MCPException):
    """Rate limit exceeded error."""
    
    def __init__(self, limit: int, window_seconds: int):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window_seconds}s",
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window_seconds": window_seconds}
        )


# ============================================================================
# Context Exceptions
# ============================================================================

class ContextError(MCPException):
    """Context-related error."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="CONTEXT_ERROR"
        )


class ContextTooLargeError(ContextError):
    """Context exceeds maximum size."""
    
    def __init__(self, size: int, max_size: int):
        super().__init__(
            message=f"Context too large: {size} tokens (max: {max_size})"
        )
        self.details = {"size": size, "max_size": max_size}


# ============================================================================
# Pattern Exceptions
# ============================================================================

class PatternError(MCPException):
    """Pattern execution error."""
    
    def __init__(self, pattern_name: str, message: str):
        super().__init__(
            message=f"Pattern '{pattern_name}' error: {message}",
            error_code="PATTERN_ERROR",
            details={"pattern": pattern_name}
        )


# ============================================================================
# Storage Exceptions
# ============================================================================

class StorageError(MCPException):
    """Storage error."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR"
        )


class StorageQuotaExceededError(StorageError):
    """Storage quota exceeded."""
    
    def __init__(self, used: int, quota: int):
        super().__init__(
            message=f"Storage quota exceeded: {used} bytes used (quota: {quota})"
        )
        self.details = {"used": used, "quota": quota}

