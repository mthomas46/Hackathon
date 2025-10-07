"""MCP Log Client - Async client for sending logs to mcp-logs service."""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logging.warning("httpx not available - MCPLogClient will use local logging only")


class MCPLogClient:
    """
    Client for sending logs to mcp-logs service.
    
    Features:
    - Async HTTP transport to mcp-logs
    - Automatic correlation ID tracking
    - Structured log entries
    - Graceful degradation (local logging if remote fails)
    - Batch processing support
    """
    
    def __init__(
        self,
        service_name: str,
        mcp_logs_url: str = "http://mcp-logs:8016",
        timeout: float = 5.0,
        batch_size: int = 100,
        flush_interval: float = 10.0,
    ):
        """
        Initialize MCP Log Client.
        
        Args:
            service_name: Name of the service sending logs
            mcp_logs_url: URL of mcp-logs service
            timeout: HTTP request timeout in seconds
            batch_size: Number of logs to batch before sending
            flush_interval: Interval in seconds to flush batched logs
        """
        self.service_name = service_name
        self.mcp_logs_url = mcp_logs_url
        self.timeout = timeout
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Initialize local logger as fallback
        self.local_logger = logging.getLogger(f"mcp.{service_name}")
        
        # Initialize HTTP client if available
        self.client = None
        if HTTPX_AVAILABLE:
            self.client = httpx.AsyncClient(timeout=timeout)
        
        # Batching
        self.log_batch = []
        self.batch_lock = asyncio.Lock()
        self.flush_task = None
        
        self.local_logger.info(
            f"MCPLogClient initialized for {service_name} "
            f"(remote: {HTTPX_AVAILABLE})"
        )
    
    async def start(self):
        """Start background flush task."""
        if self.flush_task is None:
            self.flush_task = asyncio.create_task(self._flush_periodically())
    
    async def stop(self):
        """Stop background flush task and flush remaining logs."""
        if self.flush_task:
            self.flush_task.cancel()
            try:
                await self.flush_task
            except asyncio.CancelledError:
                pass
        
        await self.flush()
        
        if self.client:
            await self.client.aclose()
    
    async def log(
        self,
        message: str,
        level: str = "INFO",
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        tags: Optional[list] = None,
        exc_info: Optional[Exception] = None,
    ):
        """
        Send log entry to mcp-logs service.
        
        Args:
            message: Log message
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            source: Source of the log (e.g., class name, function)
            correlation_id: Correlation ID for request tracking
            request_id: Request ID
            user_id: User ID
            session_id: Session ID
            fields: Additional custom fields
            tags: List of tags
            exc_info: Exception information
        """
        log_entry = {
            "entry_id": str(uuid.uuid4()),
            "message": message,
            "level": level.upper(),
            "service": self.service_name,
            "source": source or "unknown",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            
            # Context
            "correlation_id": correlation_id,
            "request_id": request_id,
            "user_id": user_id,
            "session_id": session_id,
            
            # Custom fields
            "fields": fields or {},
            
            # Tags
            "tags": tags or [],
        }
        
        # Add exception info if provided
        if exc_info:
            log_entry["fields"]["exception_type"] = type(exc_info).__name__
            log_entry["fields"]["exception_message"] = str(exc_info)
        
        # Try to send to remote service
        if self.client:
            async with self.batch_lock:
                self.log_batch.append(log_entry)
                
                if len(self.log_batch) >= self.batch_size:
                    await self._flush_batch()
        
        # Always log locally as fallback
        self._log_locally(level, message, fields)
    
    async def flush(self):
        """Flush all pending logs."""
        async with self.batch_lock:
            await self._flush_batch()
    
    async def _flush_batch(self):
        """Internal method to flush current batch."""
        if not self.log_batch:
            return
        
        batch = self.log_batch.copy()
        self.log_batch.clear()
        
        try:
            response = await self.client.post(
                f"{self.mcp_logs_url}/api/v1/logs/batch",
                json={"entries": batch}
            )
            response.raise_for_status()
            
            self.local_logger.debug(
                f"Flushed {len(batch)} logs to mcp-logs"
            )
        except Exception as e:
            self.local_logger.error(
                f"Failed to send log batch to mcp-logs: {e}"
            )
            # Logs are already in local logger, so no data loss
    
    async def _flush_periodically(self):
        """Background task to flush logs periodically."""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.local_logger.error(f"Error in periodic flush: {e}")
    
    def _log_locally(
        self,
        level: str,
        message: str,
        fields: Optional[Dict[str, Any]] = None
    ):
        """Log message to local logger as fallback."""
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        if fields:
            message = f"{message} | {fields}"
        
        self.local_logger.log(log_level, message)
    
    # Convenience methods
    
    async def debug(self, message: str, **kwargs):
        """Log debug message."""
        await self.log(message, level="DEBUG", **kwargs)
    
    async def info(self, message: str, **kwargs):
        """Log info message."""
        await self.log(message, level="INFO", **kwargs)
    
    async def warning(self, message: str, **kwargs):
        """Log warning message."""
        await self.log(message, level="WARNING", **kwargs)
    
    async def error(self, message: str, **kwargs):
        """Log error message."""
        await self.log(message, level="ERROR", **kwargs)
    
    async def critical(self, message: str, **kwargs):
        """Log critical message."""
        await self.log(message, level="CRITICAL", **kwargs)


class MCPLogHandler(logging.Handler):
    """
    Python logging handler that sends logs to MCPLogClient.
    
    Usage:
        log_client = MCPLogClient("my-service")
        handler = MCPLogHandler(log_client)
        logger = logging.getLogger()
        logger.addHandler(handler)
    """
    
    def __init__(self, log_client: MCPLogClient):
        """
        Initialize handler.
        
        Args:
            log_client: MCPLogClient instance
        """
        super().__init__()
        self.log_client = log_client
    
    def emit(self, record: logging.LogRecord):
        """
        Emit a log record.
        
        Args:
            record: Log record to emit
        """
        try:
            # Extract fields from record
            fields = {}
            if hasattr(record, "fields"):
                fields = record.fields
            
            # Create async task to send log
            asyncio.create_task(
                self.log_client.log(
                    message=record.getMessage(),
                    level=record.levelname,
                    source=record.name,
                    fields=fields,
                    exc_info=record.exc_info,
                )
            )
        except Exception:
            self.handleError(record)

