"""
Error Classification Engine

Classifies exceptions into categories for intelligent retry logic.

Features:
- Pattern matching on error messages
- Exception type analysis
- HTTP status code detection
- Transient vs permanent classification
- Suggested backoff calculation

Created: 2025-10-26
Phase: 1.2
"""

import logging
import re
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of error types."""
    # Transient errors (should retry)
    CONNECTIVITY = "connectivity"  # Network/connection issues
    TIMEOUT = "timeout"  # Processing timeouts
    RATE_LIMIT = "rate_limit"  # Rate limiting
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # Out of memory, connections, etc.
    SERVICE_UNAVAILABLE = "service_unavailable"  # 503, service down
    
    # Permanent errors (should NOT retry)
    INVALID_DATA = "invalid_data"  # Malformed, corrupt data
    PARSE_ERROR = "parse_error"  # Cannot parse file
    UNSUPPORTED_FORMAT = "unsupported_format"  # File type not supported
    PERMISSION_DENIED = "permission_denied"  # 403, auth issues
    NOT_FOUND = "not_found"  # 404, file missing
    
    # Unknown (retry once)
    UNKNOWN = "unknown"


class ErrorClassifier:
    """
    Classify exceptions for intelligent retry logic.
    
    Features:
    - Pattern matching on error messages
    - Exception type analysis
    - HTTP status code detection
    - Transient vs permanent classification
    """
    
    # Transient error patterns
    TRANSIENT_PATTERNS = {
        ErrorType.CONNECTIVITY: [
            r"connection.*(?:refused|reset|closed|timeout|lost)",
            r"network.*(?:unreachable|error|timeout)",
            r"socket.*(?:timeout|error)",
            r"broken pipe",
            r"connection pool exhausted",
            r"too many open files",
            r"temporarily unavailable",
            r"connect.*error",
            r"remote.*disconnect"
        ],
        ErrorType.TIMEOUT: [
            r"timeout",
            r"timed out",
            r"deadline exceeded",
            r"operation timed out",
            r"request.*timeout"
        ],
        ErrorType.RATE_LIMIT: [
            r"rate limit",
            r"too many requests",
            r"429",
            r"quota exceeded",
            r"throttled",
            r"slow down"
        ],
        ErrorType.RESOURCE_EXHAUSTION: [
            r"out of memory",
            r"memory error",
            r"resource exhausted",
            r"no space left",
            r"disk full",
            r"cannot allocate memory"
        ],
        ErrorType.SERVICE_UNAVAILABLE: [
            r"service unavailable",
            r"503",
            r"server error",
            r"5\d{2}",  # 5xx errors
            r"upstream.*(?:timeout|error)",
            r"502",
            r"504"
        ]
    }
    
    # Permanent error patterns
    PERMANENT_PATTERNS = {
        ErrorType.INVALID_DATA: [
            r"invalid.*(?:data|format|syntax)",
            r"malformed",
            r"corrupt",
            r"cannot decode",
            r"decode error",
            r"bad.*data"
        ],
        ErrorType.PARSE_ERROR: [
            r"parse error",
            r"parsing failed",
            r"syntax error",
            r"unexpected.*(?:token|character)",
            r"invalid syntax"
        ],
        ErrorType.UNSUPPORTED_FORMAT: [
            r"unsupported.*(?:format|type|extension)",
            r"unknown format",
            r"not supported",
            r"unsupported.*encoding"
        ],
        ErrorType.PERMISSION_DENIED: [
            r"permission denied",
            r"403",
            r"forbidden",
            r"unauthorized",
            r"401",
            r"access denied",
            r"authentication.*failed"
        ],
        ErrorType.NOT_FOUND: [
            r"not found",
            r"404",
            r"no such file",
            r"does not exist",
            r"file.*not.*found"
        ]
    }
    
    @classmethod
    def classify(cls, error: Exception) -> ErrorType:
        """
        Classify an exception.
        
        Args:
            error: Exception to classify
        
        Returns:
            ErrorType enum value
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # Compile full error context
        full_context = f"{error_type_name} {error_str}"
        
        # Check transient patterns first (more common)
        for error_type, patterns in cls.TRANSIENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, full_context, re.IGNORECASE):
                    logger.debug(
                        f"Classified as {error_type.value}: matched pattern '{pattern}'"
                    )
                    return error_type
        
        # Check permanent patterns
        for error_type, patterns in cls.PERMANENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, full_context, re.IGNORECASE):
                    logger.debug(
                        f"Classified as {error_type.value}: matched pattern '{pattern}'"
                    )
                    return error_type
        
        # Unknown - treat as transient (better to retry once than lose data)
        logger.warning(
            f"Could not classify error: {error_type_name}: {error_str[:100]}"
        )
        return ErrorType.UNKNOWN
    
    @classmethod
    def is_transient(cls, error_type: ErrorType) -> bool:
        """Check if error type is transient (should retry)."""
        return error_type in [
            ErrorType.CONNECTIVITY,
            ErrorType.TIMEOUT,
            ErrorType.RATE_LIMIT,
            ErrorType.RESOURCE_EXHAUSTION,
            ErrorType.SERVICE_UNAVAILABLE,
            ErrorType.UNKNOWN  # Retry unknown once
        ]
    
    @classmethod
    def is_permanent(cls, error_type: ErrorType) -> bool:
        """Check if error type is permanent (should not retry)."""
        return not cls.is_transient(error_type)
    
    @classmethod
    def get_suggested_backoff(cls, error_type: ErrorType, retry_count: int) -> int:
        """
        Get suggested backoff time in minutes.
        
        Args:
            error_type: Type of error
            retry_count: Current retry count
        
        Returns:
            Backoff time in minutes
        """
        # Rate limits need longer backoff
        if error_type == ErrorType.RATE_LIMIT:
            return 2 ** (retry_count + 2)  # 4, 8, 16, 32, 64 minutes
        
        # Service unavailable needs moderate backoff
        elif error_type == ErrorType.SERVICE_UNAVAILABLE:
            return 2 ** (retry_count + 1)  # 2, 4, 8, 16, 32 minutes
        
        # Others use standard exponential backoff
        else:
            return 2 ** retry_count  # 1, 2, 4, 8, 16 minutes

