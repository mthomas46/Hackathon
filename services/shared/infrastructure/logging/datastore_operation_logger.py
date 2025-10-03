"""
Normalized DataStore Operation Logger Middleware

This module provides a FastAPI middleware that automatically logs all datastore operations
to the log-collector service. Each datastore service should integrate this middleware
to provide centralized, traceable logging.

Architecture:
- Each datastore service (doc_store, prompt_store, etc.) includes this middleware
- All HTTP operations are automatically logged to log-collector
- Provides request/response tracking, timing, and error capture
- Log-collector becomes the centralized source of truth

Usage in a datastore service (e.g., doc_store/main.py):
    from services.shared.infrastructure.logging.datastore_operation_logger import (
        DataStoreOperationMiddleware,
        add_datastore_logging
    )
    
    app = FastAPI(title="Doc Store")
    
    # Add the middleware
    add_datastore_logging(
        app,
        service_name="doc_store",
        log_collector_url="http://localhost:8104"
    )
"""

import time
import uuid
import json
import httpx
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)


class DataStoreOperationMiddleware(BaseHTTPMiddleware):
    """Middleware to log all datastore operations to log-collector."""
    
    def __init__(
        self,
        app,
        service_name: str,
        log_collector_url: str = "http://localhost:8104",
        timeout_seconds: float = 1.0,
        log_paths: Optional[list] = None
    ):
        """Initialize the middleware.
        
        Args:
            app: FastAPI application
            service_name: Name of the datastore service
            log_collector_url: URL of the log-collector service
            timeout_seconds: Timeout for log submission
            log_paths: List of path patterns to log (None = log all)
        """
        super().__init__(app)
        self.service_name = service_name
        self.log_collector_url = log_collector_url
        self.timeout_seconds = timeout_seconds
        self.log_paths = log_paths or ["/api/", "/documents", "/prompts", "/services", "/memory"]
        self.client = httpx.Client(timeout=timeout_seconds)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process each request and log to collector."""
        
        # Check if this path should be logged
        should_log = any(pattern in request.url.path for pattern in self.log_paths)
        
        # Skip health checks and OpenAPI docs unless explicitly enabled
        if request.url.path in ["/health", "/openapi.json", "/docs", "/redoc"]:
            should_log = False
        
        if not should_log:
            return await call_next(request)
        
        # Generate operation ID
        operation_id = str(uuid.uuid4())[:12]
        workflow_id = request.headers.get("X-Workflow-ID", "unknown")
        
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        
        # Determine operation type from method and path
        operation_type = self._determine_operation_type(method, path)
        
        # Log operation start
        start_time = time.time()
        self._send_log(
            level="INFO",
            message=f"DataStore operation started: {method} {path}",
            context={
                "operation_id": operation_id,
                "workflow_id": workflow_id,
                "service": self.service_name,
                "method": method,
                "path": path,
                "operation_type": operation_type,
                "query_params": query_params,
                "phase": "start"
            }
        )
        
        # Process request
        response = None
        error = None
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful completion
            self._send_log(
                level="INFO" if response.status_code < 400 else "ERROR",
                message=f"DataStore operation completed: {method} {path}",
                context={
                    "operation_id": operation_id,
                    "workflow_id": workflow_id,
                    "service": self.service_name,
                    "method": method,
                    "path": path,
                    "operation_type": operation_type,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "success": response.status_code < 400,
                    "phase": "complete"
                }
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error = e
            
            # Log error
            self._send_log(
                level="ERROR",
                message=f"DataStore operation failed: {method} {path}",
                context={
                    "operation_id": operation_id,
                    "workflow_id": workflow_id,
                    "service": self.service_name,
                    "method": method,
                    "path": path,
                    "operation_type": operation_type,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "phase": "error"
                }
            )
            
            raise
    
    def _determine_operation_type(self, method: str, path: str) -> str:
        """Determine operation type from HTTP method and path.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: Request path
            
        Returns:
            Operation type string
        """
        # Normalize path
        path_lower = path.lower()
        
        # Map HTTP methods to CRUD operations
        if method == "POST":
            if "bulk" in path_lower:
                return "bulk_create"
            return "create"
        elif method == "GET":
            if "search" in path_lower:
                return "search"
            elif "{" in path or path_lower.endswith(('/', '/list')):
                return "list"
            return "read"
        elif method == "PUT" or method == "PATCH":
            if "bulk" in path_lower:
                return "bulk_update"
            return "update"
        elif method == "DELETE":
            if "bulk" in path_lower:
                return "bulk_delete"
            return "delete"
        else:
            return method.lower()
    
    def _send_log(self, level: str, message: str, context: Dict[str, Any]):
        """Send log to log-collector.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            context: Additional context data
        """
        try:
            log_data = {
                "service": self.service_name,
                "level": level,
                "message": message,
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send synchronously (non-blocking for the request)
            self.client.post(
                f"{self.log_collector_url}/logs",
                json=log_data
            )
        except Exception as e:
            # Don't fail the request if logging fails
            logger.warning(f"Failed to send log to collector: {e}")


def add_datastore_logging(
    app: FastAPI,
    service_name: str,
    log_collector_url: str = "http://localhost:8104",
    timeout_seconds: float = 1.0,
    log_paths: Optional[list] = None
) -> None:
    """Add datastore operation logging to a FastAPI app.
    
    This is a convenience function to add the middleware with sensible defaults.
    
    Args:
        app: FastAPI application instance
        service_name: Name of the datastore service
        log_collector_url: URL of the log-collector service
        timeout_seconds: Timeout for log submission
        log_paths: List of path patterns to log (None = sensible defaults)
        
    Example:
        app = FastAPI(title="Doc Store")
        add_datastore_logging(app, "doc_store")
    """
    app.add_middleware(
        DataStoreOperationMiddleware,
        service_name=service_name,
        log_collector_url=log_collector_url,
        timeout_seconds=timeout_seconds,
        log_paths=log_paths
    )
    
    logger.info(
        f"✅ DataStore operation logging enabled for '{service_name}' "
        f"→ {log_collector_url}"
    )


# Async version for services that need it
class AsyncDataStoreLogger:
    """Async logger for services that prefer async operations."""
    
    def __init__(
        self,
        service_name: str,
        log_collector_url: str = "http://localhost:8104",
        timeout_seconds: float = 1.0
    ):
        """Initialize async logger.
        
        Args:
            service_name: Name of the datastore service
            log_collector_url: URL of the log-collector service
            timeout_seconds: Timeout for log submission
        """
        self.service_name = service_name
        self.log_collector_url = log_collector_url
        self.timeout_seconds = timeout_seconds
    
    async def log_operation(
        self,
        operation_type: str,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        workflow_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a datastore operation.
        
        Args:
            operation_type: Type of operation (create, read, update, delete, etc.)
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Operation duration in milliseconds
            workflow_id: Workflow identifier
            metadata: Additional metadata
        """
        try:
            log_data = {
                "service": self.service_name,
                "level": "INFO" if status_code < 400 else "ERROR",
                "message": f"DataStore operation: {method} {path}",
                "context": {
                    "workflow_id": workflow_id,
                    "operation_type": operation_type,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                    "success": status_code < 400,
                    "metadata": metadata or {},
                    "phase": "complete"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                await client.post(
                    f"{self.log_collector_url}/logs",
                    json=log_data
                )
        except Exception as e:
            logger.warning(f"Failed to send async log to collector: {e}")

