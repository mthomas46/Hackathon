"""Data Store Interaction Tracker - Log all data store operations to log-collector.

This module provides comprehensive tracking and logging of all interactions with
data store services (doc_store, prompt_store, external-service-store, memory-agent).

Usage:
    from data_store_interaction_tracker import DataStoreTracker
    
    tracker = DataStoreTracker(
        workflow_id="my_workflow_123",
        log_collector_url="http://localhost:8104"
    )
    
    # Track an operation
    with tracker.track_operation("doc_store", "create_document") as op:
        result = await save_document(...)
        op.set_result(result, success=True)
"""

import httpx
import asyncio
import time
import json
import uuid
from typing import Any, Dict, Optional
from datetime import datetime
from contextlib import asynccontextmanager, contextmanager
from enum import Enum


class DataStoreType(Enum):
    """Supported data store types."""
    DOC_STORE = "doc_store"
    PROMPT_STORE = "prompt_store"
    EXTERNAL_SERVICE_STORE = "external-service-store"
    MEMORY_AGENT = "memory-agent"
    USER_STORE = "user-store"


class OperationType(Enum):
    """Common operation types for data stores."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    SEARCH = "search"
    BULK_CREATE = "bulk_create"
    BULK_UPDATE = "bulk_update"


class DataStoreTracker:
    """Track and log all data store interactions."""
    
    def __init__(
        self,
        workflow_id: str,
        log_collector_url: str = "http://localhost:8104",
        timeout_seconds: float = 2.0,
        fail_silently: bool = True
    ):
        """Initialize the tracker.
        
        Args:
            workflow_id: Unique identifier for the current workflow
            log_collector_url: URL of the log-collector service
            timeout_seconds: Timeout for log submission
            fail_silently: If True, logging failures won't raise exceptions
        """
        self.workflow_id = workflow_id
        self.log_collector_url = log_collector_url
        self.timeout_seconds = timeout_seconds
        self.fail_silently = fail_silently
        self.stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "operations_by_store": {},
            "operations_by_type": {},
            "total_duration_ms": 0.0
        }
    
    def _send_log_sync(self, level: str, message: str, context: Dict[str, Any]):
        """Send log synchronously to log-collector.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            context: Additional context data
        """
        try:
            log_data = {
                "service": "data_store_tracker",
                "workflow_id": self.workflow_id,
                "level": level,
                "message": message,
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = httpx.post(
                f"{self.log_collector_url}/api/v1/logs",
                json=log_data,
                timeout=self.timeout_seconds
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            if not self.fail_silently:
                raise
            return False
    
    async def _send_log_async(self, level: str, message: str, context: Dict[str, Any]):
        """Send log asynchronously to log-collector.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            context: Additional context data
        """
        try:
            log_data = {
                "service": "data_store_tracker",
                "workflow_id": self.workflow_id,
                "level": level,
                "message": message,
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.log_collector_url}/api/v1/logs",
                    json=log_data
                )
                
                return response.status_code in [200, 201]
        except Exception as e:
            if not self.fail_silently:
                raise
            return False
    
    @contextmanager
    def track_operation(
        self,
        store_name: str,
        operation: str,
        data_summary: Optional[Dict[str, Any]] = None
    ):
        """Context manager to track a synchronous data store operation.
        
        Args:
            store_name: Name of the data store (e.g., 'doc_store')
            operation: Operation being performed (e.g., 'create_document')
            data_summary: Optional summary of the data being operated on
            
        Yields:
            OperationContext: Context object to set result
            
        Example:
            with tracker.track_operation("doc_store", "create_document") as op:
                result = save_document(...)
                op.set_result(result, success=True)
        """
        operation_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Log operation start
        self._send_log_sync(
            "INFO",
            f"Data store operation started: {store_name}.{operation}",
            {
                "operation_id": operation_id,
                "store_name": store_name,
                "operation": operation,
                "data_summary": data_summary or {},
                "phase": "start"
            }
        )
        
        # Update stats
        self.stats["total_operations"] += 1
        self.stats["operations_by_store"][store_name] = \
            self.stats["operations_by_store"].get(store_name, 0) + 1
        self.stats["operations_by_type"][operation] = \
            self.stats["operations_by_type"].get(operation, 0) + 1
        
        context = OperationContext(
            operation_id=operation_id,
            store_name=store_name,
            operation=operation,
            tracker=self,
            start_time=start_time
        )
        
        try:
            yield context
        except Exception as e:
            # Log exception
            duration_ms = (time.time() - start_time) * 1000
            self.stats["failed_operations"] += 1
            self.stats["total_duration_ms"] += duration_ms
            
            self._send_log_sync(
                "ERROR",
                f"Data store operation failed: {store_name}.{operation}",
                {
                    "operation_id": operation_id,
                    "store_name": store_name,
                    "operation": operation,
                    "duration_ms": duration_ms,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "phase": "error"
                }
            )
            raise
        else:
            # Log completion if not already logged by context
            if not context._result_logged:
                duration_ms = (time.time() - start_time) * 1000
                self.stats["total_duration_ms"] += duration_ms
                
                self._send_log_sync(
                    "WARNING",
                    f"Data store operation completed without explicit result: {store_name}.{operation}",
                    {
                        "operation_id": operation_id,
                        "store_name": store_name,
                        "operation": operation,
                        "duration_ms": duration_ms,
                        "phase": "complete_no_result"
                    }
                )
    
    @asynccontextmanager
    async def track_operation_async(
        self,
        store_name: str,
        operation: str,
        data_summary: Optional[Dict[str, Any]] = None
    ):
        """Context manager to track an asynchronous data store operation.
        
        Args:
            store_name: Name of the data store
            operation: Operation being performed
            data_summary: Optional summary of the data
            
        Yields:
            OperationContext: Context object to set result
        """
        operation_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Log operation start
        await self._send_log_async(
            "INFO",
            f"Data store operation started: {store_name}.{operation}",
            {
                "operation_id": operation_id,
                "store_name": store_name,
                "operation": operation,
                "data_summary": data_summary or {},
                "phase": "start"
            }
        )
        
        # Update stats
        self.stats["total_operations"] += 1
        self.stats["operations_by_store"][store_name] = \
            self.stats["operations_by_store"].get(store_name, 0) + 1
        self.stats["operations_by_type"][operation] = \
            self.stats["operations_by_type"].get(operation, 0) + 1
        
        context = AsyncOperationContext(
            operation_id=operation_id,
            store_name=store_name,
            operation=operation,
            tracker=self,
            start_time=start_time
        )
        
        try:
            yield context
        except Exception as e:
            # Log exception
            duration_ms = (time.time() - start_time) * 1000
            self.stats["failed_operations"] += 1
            self.stats["total_duration_ms"] += duration_ms
            
            await self._send_log_async(
                "ERROR",
                f"Data store operation failed: {store_name}.{operation}",
                {
                    "operation_id": operation_id,
                    "store_name": store_name,
                    "operation": operation,
                    "duration_ms": duration_ms,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "phase": "error"
                }
            )
            raise
        else:
            # Log completion if not already logged
            if not context._result_logged:
                duration_ms = (time.time() - start_time) * 1000
                self.stats["total_duration_ms"] += duration_ms
                
                await self._send_log_async(
                    "WARNING",
                    f"Data store operation completed without explicit result: {store_name}.{operation}",
                    {
                        "operation_id": operation_id,
                        "store_name": store_name,
                        "operation": operation,
                        "duration_ms": duration_ms,
                        "phase": "complete_no_result"
                    }
                )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current tracking statistics.
        
        Returns:
            Dictionary with operation statistics
        """
        avg_duration = (
            self.stats["total_duration_ms"] / self.stats["total_operations"]
            if self.stats["total_operations"] > 0 else 0.0
        )
        
        return {
            **self.stats,
            "average_duration_ms": avg_duration,
            "success_rate": (
                self.stats["successful_operations"] / self.stats["total_operations"] * 100
                if self.stats["total_operations"] > 0 else 0.0
            )
        }
    
    def log_summary(self):
        """Log a summary of all tracked operations."""
        stats = self.get_statistics()
        
        self._send_log_sync(
            "INFO",
            "Data store tracking summary",
            {
                "workflow_id": self.workflow_id,
                "total_operations": stats["total_operations"],
                "successful_operations": stats["successful_operations"],
                "failed_operations": stats["failed_operations"],
                "success_rate": f"{stats['success_rate']:.1f}%",
                "average_duration_ms": f"{stats['average_duration_ms']:.2f}",
                "operations_by_store": stats["operations_by_store"],
                "operations_by_type": stats["operations_by_type"],
                "phase": "summary"
            }
        )


class OperationContext:
    """Context for a tracked operation (synchronous)."""
    
    def __init__(
        self,
        operation_id: str,
        store_name: str,
        operation: str,
        tracker: DataStoreTracker,
        start_time: float
    ):
        self.operation_id = operation_id
        self.store_name = store_name
        self.operation = operation
        self.tracker = tracker
        self.start_time = start_time
        self._result_logged = False
    
    def set_result(
        self,
        result: Any,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Set the operation result and log completion.
        
        Args:
            result: Operation result
            success: Whether operation was successful
            metadata: Additional metadata to log
        """
        duration_ms = (time.time() - self.start_time) * 1000
        
        if success:
            self.tracker.stats["successful_operations"] += 1
            level = "INFO"
            message = f"Data store operation succeeded: {self.store_name}.{self.operation}"
        else:
            self.tracker.stats["failed_operations"] += 1
            level = "ERROR"
            message = f"Data store operation failed: {self.store_name}.{self.operation}"
        
        self.tracker.stats["total_duration_ms"] += duration_ms
        
        # Prepare result summary (avoid logging large data)
        result_summary = {
            "type": type(result).__name__,
            "has_data": result is not None
        }
        
        if isinstance(result, dict):
            result_summary["keys"] = list(result.keys())[:10]
        elif isinstance(result, list):
            result_summary["count"] = len(result)
        
        self.tracker._send_log_sync(
            level,
            message,
            {
                "operation_id": self.operation_id,
                "store_name": self.store_name,
                "operation": self.operation,
                "duration_ms": duration_ms,
                "success": success,
                "result_summary": result_summary,
                "metadata": metadata or {},
                "phase": "complete"
            }
        )
        
        self._result_logged = True


class AsyncOperationContext:
    """Context for a tracked operation (asynchronous)."""
    
    def __init__(
        self,
        operation_id: str,
        store_name: str,
        operation: str,
        tracker: DataStoreTracker,
        start_time: float
    ):
        self.operation_id = operation_id
        self.store_name = store_name
        self.operation = operation
        self.tracker = tracker
        self.start_time = start_time
        self._result_logged = False
    
    async def set_result(
        self,
        result: Any,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Set the operation result and log completion.
        
        Args:
            result: Operation result
            success: Whether operation was successful
            metadata: Additional metadata to log
        """
        duration_ms = (time.time() - self.start_time) * 1000
        
        if success:
            self.tracker.stats["successful_operations"] += 1
            level = "INFO"
            message = f"Data store operation succeeded: {self.store_name}.{self.operation}"
        else:
            self.tracker.stats["failed_operations"] += 1
            level = "ERROR"
            message = f"Data store operation failed: {self.store_name}.{self.operation}"
        
        self.tracker.stats["total_duration_ms"] += duration_ms
        
        # Prepare result summary
        result_summary = {
            "type": type(result).__name__,
            "has_data": result is not None
        }
        
        if isinstance(result, dict):
            result_summary["keys"] = list(result.keys())[:10]
        elif isinstance(result, list):
            result_summary["count"] = len(result)
        
        await self.tracker._send_log_async(
            level,
            message,
            {
                "operation_id": self.operation_id,
                "store_name": self.store_name,
                "operation": self.operation,
                "duration_ms": duration_ms,
                "success": success,
                "result_summary": result_summary,
                "metadata": metadata or {},
                "phase": "complete"
            }
        )
        
        self._result_logged = True

