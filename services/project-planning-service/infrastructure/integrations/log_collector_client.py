"""
Log Collector Integration Client
==================================

Client for sending logs and metrics to the log-collector service for
comprehensive observability and debugging capabilities.
"""

import httpx
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio


class LogCollectorClient:
    """Client for log-collector service integration."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize log collector client.
        
        Args:
            base_url: Log collector service URL (defaults to env var or localhost)
        """
        self.base_url = base_url or os.getenv("LOG_COLLECTOR_URL", "http://log-collector:5080")
        self.service_name = "project-planning-service"
        self.timeout = httpx.Timeout(5.0, connect=2.0)
    
    async def log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Send a log entry to log-collector service.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            context: Additional context data
            user_id: User ID associated with the log
            
        Returns:
            True if log was successfully sent, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                log_entry = {
                    "service": self.service_name,
                    "level": level.upper(),
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context": context or {},
                    "user_id": user_id
                }
                
                response = await client.post(
                    f"{self.base_url}/logs",
                    json=log_entry
                )
                
                return response.status_code == 200
                
        except Exception as e:
            # Fallback to console logging if log-collector is unavailable
            print(f"[{self.service_name}] Failed to send log to collector: {e}")
            print(f"[{self.service_name}] {level}: {message}")
            return False
    
    async def log_info(self, message: str, context: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
        """Log INFO level message."""
        await self.log("INFO", message, context, user_id)
    
    async def log_error(self, message: str, context: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
        """Log ERROR level message."""
        await self.log("ERROR", message, context, user_id)
    
    async def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
        """Log WARNING level message."""
        await self.log("WARNING", message, context, user_id)
    
    async def log_debug(self, message: str, context: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
        """Log DEBUG level message."""
        await self.log("DEBUG", message, context, user_id)
    
    async def log_business_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """
        Log a business event for analytics and auditing.
        
        Args:
            event_type: Type of business event (e.g., 'feature_created', 'roadmap_planned')
            event_data: Event-specific data
            user_id: User ID associated with the event
        """
        await self.log(
            "INFO",
            f"Business Event: {event_type}",
            context={
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": datetime.utcnow().isoformat()
            },
            user_id=user_id
        )
    
    async def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """
        Log API request for monitoring and debugging.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            user_id: User making the request
            additional_context: Additional context data
        """
        context = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            **(additional_context or {})
        }
        
        level = "ERROR" if status_code >= 500 else "WARNING" if status_code >= 400 else "INFO"
        
        await self.log(
            level,
            f"API Request: {method} {path} - {status_code} ({duration_ms}ms)",
            context=context,
            user_id=user_id
        )
    
    async def log_integration_call(
        self,
        service_name: str,
        operation: str,
        success: bool,
        duration_ms: float,
        error_message: Optional[str] = None
    ):
        """
        Log integration call to another service.
        
        Args:
            service_name: Name of the service being called
            operation: Operation being performed
            success: Whether the call was successful
            duration_ms: Call duration in milliseconds
            error_message: Error message if failed
        """
        context = {
            "service_name": service_name,
            "operation": operation,
            "success": success,
            "duration_ms": duration_ms
        }
        
        if error_message:
            context["error_message"] = error_message
        
        level = "ERROR" if not success else "INFO"
        message = f"Integration Call: {service_name}.{operation} - {'SUCCESS' if success else 'FAILED'} ({duration_ms}ms)"
        
        await self.log(level, message, context=context)
    
    async def log_feature_analysis(
        self,
        feature_id: str,
        analysis_type: str,
        result: Dict[str, Any],
        duration_ms: float
    ):
        """
        Log feature analysis results for tracking and debugging.
        
        Args:
            feature_id: ID of the feature being analyzed
            analysis_type: Type of analysis performed
            result: Analysis results
            duration_ms: Analysis duration
        """
        await self.log(
            "INFO",
            f"Feature Analysis: {analysis_type} for feature {feature_id}",
            context={
                "feature_id": feature_id,
                "analysis_type": analysis_type,
                "result_summary": result,
                "duration_ms": duration_ms
            }
        )
    
    async def batch_log(self, log_entries: list[Dict[str, Any]]) -> bool:
        """
        Send multiple log entries in batch.
        
        Args:
            log_entries: List of log entry dictionaries
            
        Returns:
            True if batch was successfully sent
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Add service name to all entries
                for entry in log_entries:
                    entry["service"] = self.service_name
                    if "timestamp" not in entry:
                        entry["timestamp"] = datetime.utcnow().isoformat()
                
                response = await client.post(
                    f"{self.base_url}/logs/batch",
                    json={"logs": log_entries}
                )
                
                return response.status_code == 200
                
        except Exception as e:
            print(f"[{self.service_name}] Failed to send batch logs: {e}")
            return False


# Global client instance
_log_client: Optional[LogCollectorClient] = None


def get_log_client() -> LogCollectorClient:
    """Get or create global log collector client instance."""
    global _log_client
    if _log_client is None:
        _log_client = LogCollectorClient()
    return _log_client

