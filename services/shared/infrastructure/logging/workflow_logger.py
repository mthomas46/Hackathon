"""Universal Workflow Logger - Phase 1 Implementation

This module provides a standardized logging interface for all services
in the Enhanced Roadmap v2.0 workflow, ensuring complete observability
and traceability across the entire ecosystem.

Usage:
    from services.shared.infrastructure.logging.workflow_logger import WorkflowLogger
    
    logger = WorkflowLogger(
        service_name="my-service",
        log_collector_url="http://log-collector:5040"
    )
    
    await logger.log_workflow_start("wf-123", "operation_name")
    await logger.log_workflow_step("wf-123", "step_1", {"data": "value"})
    await logger.log_workflow_complete("wf-123", 1234.5, True)
"""

import httpx
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import json
from enum import Enum


class LogLevel(Enum):
    """Log levels for workflow logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class WorkflowLogger:
    """Universal logging client for all ecosystem services.
    
    This logger integrates with the log-collector service to provide
    centralized, traceable logging for all workflow operations.
    
    Features:
    - Automatic workflow_id tracking
    - Service-specific context
    - Async/non-blocking logging
    - Graceful failure handling
    - Performance metrics tracking
    """
    
    def __init__(
        self,
        service_name: str,
        log_collector_url: str = "http://log-collector:5040",
        timeout_seconds: float = 5.0,
        fail_silently: bool = True
    ):
        """Initialize the workflow logger.
        
        Args:
            service_name: Name of the service using this logger
            log_collector_url: URL of the log-collector service
            timeout_seconds: Timeout for log submission
            fail_silently: If True, logging failures won't raise exceptions
        """
        self.service_name = service_name
        self.log_collector_url = log_collector_url
        self.timeout_seconds = timeout_seconds
        self.fail_silently = fail_silently
        self.client = httpx.AsyncClient(timeout=timeout_seconds)
        self._request_id = str(uuid.uuid4())[:8]
    
    async def log_workflow_start(
        self,
        workflow_id: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """Log the start of a workflow operation.
        
        Args:
            workflow_id: Unique identifier for the workflow
            operation: Name of the operation being started
            context: Additional context data
            user_id: User ID if applicable
            
        Returns:
            True if log was successfully sent, False otherwise
        """
        return await self._send_log(
            level=LogLevel.INFO,
            message=f"Workflow started: {operation}",
            context={
                "workflow_id": workflow_id,
                "operation": operation,
                "phase": "start",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                **(context or {})
            }
        )
    
    async def log_workflow_step(
        self,
        workflow_id: str,
        step_name: str,
        step_data: Dict[str, Any],
        level: LogLevel = LogLevel.DEBUG
    ) -> bool:
        """Log an individual workflow step.
        
        Args:
            workflow_id: Unique identifier for the workflow
            step_name: Name of the step being executed
            step_data: Data/metrics for this step
            level: Log level (default: DEBUG)
            
        Returns:
            True if log was successfully sent, False otherwise
        """
        return await self._send_log(
            level=level,
            message=f"Workflow step: {step_name}",
            context={
                "workflow_id": workflow_id,
                "step_name": step_name,
                "phase": "step",
                **step_data
            }
        )
    
    async def log_workflow_complete(
        self,
        workflow_id: str,
        duration_ms: float,
        success: bool,
        metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log workflow completion.
        
        Args:
            workflow_id: Unique identifier for the workflow
            duration_ms: Total duration in milliseconds
            success: Whether workflow completed successfully
            metrics: Additional performance metrics
            
        Returns:
            True if log was successfully sent, False otherwise
        """
        level = LogLevel.INFO if success else LogLevel.ERROR
        
        return await self._send_log(
            level=level,
            message=f"Workflow {'completed' if success else 'failed'}",
            context={
                "workflow_id": workflow_id,
                "duration_ms": duration_ms,
                "success": success,
                "phase": "complete",
                **(metrics or {})
            }
        )
    
    async def log_service_call(
        self,
        workflow_id: str,
        target_service: str,
        operation: str,
        duration_ms: Optional[float] = None,
        success: bool = True,
        response_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log a call to another service.
        
        Args:
            workflow_id: Unique identifier for the workflow
            target_service: Name of the service being called
            operation: Operation being performed
            duration_ms: Call duration in milliseconds
            success: Whether call was successful
            response_data: Response data from the service
            
        Returns:
            True if log was successfully sent, False otherwise
        """
        return await self._send_log(
            level=LogLevel.INFO,
            message=f"Service call: {target_service}.{operation}",
            context={
                "workflow_id": workflow_id,
                "target_service": target_service,
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                "phase": "service_call",
                "response_summary": self._summarize_response(response_data)
            }
        )
    
    async def log_error(
        self,
        workflow_id: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        include_traceback: bool = True
    ) -> bool:
        """Log an error with full context.
        
        Args:
            workflow_id: Unique identifier for the workflow
            error: The exception that occurred
            context: Additional context about the error
            include_traceback: Whether to include traceback
            
        Returns:
            True if log was successfully sent, False otherwise
        """
        import traceback
        
        error_context = {
            "workflow_id": workflow_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "phase": "error",
            **(context or {})
        }
        
        if include_traceback:
            error_context["traceback"] = traceback.format_exc()
        
        return await self._send_log(
            level=LogLevel.ERROR,
            message=f"Error: {str(error)}",
            context=error_context
        )
    
    async def log_performance_metric(
        self,
        workflow_id: str,
        metric_name: str,
        metric_value: float,
        metric_unit: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log a performance metric.
        
        Args:
            workflow_id: Unique identifier for the workflow
            metric_name: Name of the metric
            metric_value: Numeric value of the metric
            metric_unit: Unit of measurement (e.g., 'ms', 'MB', 'requests')
            additional_context: Additional context
            
        Returns:
            True if log was successfully sent, False otherwise
        """
        return await self._send_log(
            level=LogLevel.INFO,
            message=f"Performance metric: {metric_name}",
            context={
                "workflow_id": workflow_id,
                "metric_name": metric_name,
                "metric_value": metric_value,
                "metric_unit": metric_unit,
                "phase": "metric",
                **(additional_context or {})
            }
        )
    
    async def log_debug(
        self,
        workflow_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log a debug message.
        
        Args:
            workflow_id: Unique identifier for the workflow
            message: Debug message
            context: Additional context
            
        Returns:
            True if log was successfully sent, False otherwise
        """
        return await self._send_log(
            level=LogLevel.DEBUG,
            message=message,
            context={
                "workflow_id": workflow_id,
                **(context or {})
            }
        )
    
    async def log_warning(
        self,
        workflow_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log a warning message.
        
        Args:
            workflow_id: Unique identifier for the workflow
            message: Warning message
            context: Additional context
            
        Returns:
            True if log was successfully sent, False otherwise
        """
        return await self._send_log(
            level=LogLevel.WARNING,
            message=message,
            context={
                "workflow_id": workflow_id,
                **(context or {})
            }
        )
    
    async def _send_log(
        self,
        level: LogLevel,
        message: str,
        context: Dict[str, Any]
    ) -> bool:
        """Internal method to send log to collector.
        
        Args:
            level: Log level
            message: Log message
            context: Context data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            log_entry = {
                "level": level.value,
                "service": self.service_name,
                "message": message,
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "request_id": self._request_id
            }
            
            response = await self.client.post(
                f"{self.log_collector_url}/logs",
                json=log_entry
            )
            
            return response.status_code == 200
            
        except Exception as e:
            if not self.fail_silently:
                raise
            # Fail silently - print to console but don't break workflow
            print(f"[WorkflowLogger] Failed to send log: {e}")
            return False
    
    def _summarize_response(self, response_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a summary of response data to avoid logging huge payloads.
        
        Args:
            response_data: Response data to summarize
            
        Returns:
            Summarized response data
        """
        if not response_data:
            return None
        
        # Limit response data to avoid huge log entries
        summary = {}
        for key, value in response_data.items():
            if isinstance(value, (list, dict)):
                summary[key] = f"<{type(value).__name__} with {len(value)} items>"
            elif isinstance(value, str) and len(value) > 100:
                summary[key] = value[:100] + "..."
            else:
                summary[key] = value
        
        return summary
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Convenience function for quick logging
async def quick_log(
    service_name: str,
    workflow_id: str,
    message: str,
    level: LogLevel = LogLevel.INFO,
    context: Optional[Dict[str, Any]] = None
):
    """Quick one-off logging without creating a logger instance.
    
    Args:
        service_name: Name of the service
        workflow_id: Workflow identifier
        message: Log message
        level: Log level
        context: Additional context
    """
    async with WorkflowLogger(service_name) as logger:
        await logger._send_log(
            level=level,
            message=message,
            context={"workflow_id": workflow_id, **(context or {})}
        )

