"""
Structured Logger with Correlation IDs (Week 2, Day 7)

Provides JSON-formatted structured logging with:
- Correlation IDs for request tracing
- Structured fields for easy parsing
- Integration with existing Python logging
- Support for log aggregation (ELK, Splunk, etc.)
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
from functools import wraps

# Context variables for correlation IDs
_request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
_job_id_var: ContextVar[Optional[str]] = ContextVar('job_id', default=None)
_user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredLogger:
    """
    JSON-structured logger with correlation IDs.
    
    Features:
    - JSON-formatted log entries
    - Automatic correlation ID injection
    - Structured fields
    - Compatible with standard Python logging
    - Easy integration with log aggregation
    """
    
    def __init__(
        self,
        name: str,
        request_id: Optional[str] = None,
        job_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (usually __name__)
            request_id: Optional request ID (auto-generated if None)
            job_id: Optional job ID
            user_id: Optional user ID
        """
        self.logger = logging.getLogger(name)
        self.request_id = request_id or self._get_or_create_request_id()
        self.job_id = job_id
        self.user_id = user_id
        
        # Set context vars
        if request_id:
            _request_id_var.set(request_id)
        if job_id:
            _job_id_var.set(job_id)
        if user_id:
            _user_id_var.set(user_id)
    
    def _get_or_create_request_id(self) -> str:
        """Get existing request ID from context or create new one."""
        existing = _request_id_var.get()
        if existing:
            return existing
        
        new_id = str(uuid.uuid4())
        _request_id_var.set(new_id)
        return new_id
    
    def _build_log_entry(
        self,
        level: str,
        event: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build structured log entry.
        
        Args:
            level: Log level (INFO, ERROR, etc.)
            event: Event name/description
            **kwargs: Additional structured fields
        
        Returns:
            Dict with structured log entry
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.upper(),
            "event": event,
            "logger": self.logger.name,
            "request_id": self.request_id,
        }
        
        # Add optional IDs if present
        if self.job_id:
            entry["job_id"] = self.job_id
        if self.user_id:
            entry["user_id"] = self.user_id
        
        # Add custom fields
        entry.update(kwargs)
        
        return entry
    
    def _log(self, level: str, event: str, **kwargs):
        """
        Log structured message.
        
        Args:
            level: Log level
            event: Event description
            **kwargs: Additional structured fields
        """
        entry = self._build_log_entry(level, event, **kwargs)
        log_message = json.dumps(entry)
        
        # Use appropriate logging method
        log_method = getattr(self.logger, level.lower())
        log_method(log_message)
    
    def debug(self, event: str, **kwargs):
        """Log debug message."""
        self._log("DEBUG", event, **kwargs)
    
    def info(self, event: str, **kwargs):
        """Log info message."""
        self._log("INFO", event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        """Log warning message."""
        self._log("WARNING", event, **kwargs)
    
    def error(self, event: str, **kwargs):
        """Log error message."""
        self._log("ERROR", event, **kwargs)
    
    def critical(self, event: str, **kwargs):
        """Log critical message."""
        self._log("CRITICAL", event, **kwargs)
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ):
        """
        Log HTTP request.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            **kwargs: Additional fields
        """
        self.info(
            "http_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def log_job_event(
        self,
        event: str,
        status: str,
        progress: Optional[float] = None,
        **kwargs
    ):
        """
        Log job processing event.
        
        Args:
            event: Event type
            status: Job status
            progress: Optional progress (0.0-1.0)
            **kwargs: Additional fields
        """
        self.info(
            event,
            job_id=self.job_id,
            status=status,
            progress=progress,
            **kwargs
        )
    
    def log_error_with_trace(
        self,
        event: str,
        error: Exception,
        **kwargs
    ):
        """
        Log error with stack trace.
        
        Args:
            event: Error event description
            error: Exception object
            **kwargs: Additional fields
        """
        import traceback
        
        self.error(
            event,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            **kwargs
        )


# Correlation ID management
def set_request_id(request_id: str):
    """Set request ID in context."""
    _request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return _request_id_var.get()


def set_job_id(job_id: str):
    """Set job ID in context."""
    _job_id_var.set(job_id)


def get_job_id() -> Optional[str]:
    """Get current job ID from context."""
    return _job_id_var.get()


def set_user_id(user_id: str):
    """Set user ID in context."""
    _user_id_var.set(user_id)


def get_user_id() -> Optional[str]:
    """Get current user ID from context."""
    return _user_id_var.get()


def clear_correlation_ids():
    """Clear all correlation IDs from context."""
    _request_id_var.set(None)
    _job_id_var.set(None)
    _user_id_var.set(None)


# Decorator for automatic request ID injection
def with_request_id(func):
    """
    Decorator to automatically inject request ID.
    
    For FastAPI endpoints, extracts request ID from header or creates new one.
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Try to extract from FastAPI request
        request_id = None
        for arg in args:
            if hasattr(arg, 'headers') and 'X-Request-ID' in arg.headers:
                request_id = arg.headers['X-Request-ID']
                break
        
        # Create new if not found
        if not request_id:
            request_id = str(uuid.uuid4())
        
        set_request_id(request_id)
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            # Don't clear - may be used by background tasks
            pass
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Create new request ID
        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Don't clear - may be used by background tasks
            pass
    
    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


# Decorator for logging function calls
def log_function_call(event_name: Optional[str] = None):
    """
    Decorator to log function entry/exit.
    
    Args:
        event_name: Optional event name (defaults to function name)
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = StructuredLogger(func.__module__)
            event = event_name or func.__name__
            
            logger.debug(f"{event}_start", function=func.__name__)
            
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"{event}_complete", function=func.__name__)
                return result
            except Exception as e:
                logger.log_error_with_trace(f"{event}_error", e, function=func.__name__)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = StructuredLogger(func.__module__)
            event = event_name or func.__name__
            
            logger.debug(f"{event}_start", function=func.__name__)
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{event}_complete", function=func.__name__)
                return result
            except Exception as e:
                logger.log_error_with_trace(f"{event}_error", e, function=func.__name__)
                raise
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Factory function
def get_structured_logger(
    name: str,
    **kwargs
) -> StructuredLogger:
    """
    Get structured logger instance.
    
    Args:
        name: Logger name
        **kwargs: Optional request_id, job_id, user_id
    
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, **kwargs)

