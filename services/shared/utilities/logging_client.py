"""
Centralized Logging Client for Log Collector Service Integration.

This module provides a unified logging client that all services can use to send
structured logs to the centralized log-collector service. It handles async
communication, batching, error handling, and automatic retries.

Features:
- Async log submission with automatic batching
- Connection pooling and error recovery
- Structured logging with service context
- Automatic log collector service discovery
- Fallback to local logging when collector unavailable
- Performance monitoring and metrics

Usage:
    from services.shared.utilities.logging_client import LogCollectorClient

    # Initialize (typically once per service)
    logger = LogCollectorClient(service_name="my-service")

    # Log events
    await logger.log_info("Operation completed", {"user_id": 123, "duration": 1.5})
    await logger.log_error("Database connection failed", {"error_code": "DB_001"})
    await logger.log_business_event("user_registered", {"user_id": 123, "plan": "premium"}).
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx


class LogCollectorClient:
    """
    Async client for sending logs to the centralized log-collector service.

    Provides a clean interface for services to submit structured logs
    with automatic batching, retries, and error handling.
    """

    def __init__(
        self,
        service_name: str,
        collector_url: Optional[str] = None,
        batch_size: int = 10,
        flush_interval: float = 5.0,
        max_retries: int = 3,
        timeout: float = 10.0,
    ):
        """
        Initialize the log collector client.

        Args:
            service_name: Name of the service sending logs
            collector_url: URL of log collector service (auto-discovered if None)
            batch_size: Number of logs to batch before sending
            flush_interval: Seconds between automatic batch flushes
            max_retries: Maximum retry attempts for failed sends
            timeout: HTTP request timeout in seconds
        """
        self.service_name = service_name
        self.collector_url = collector_url or "http://localhost:5080"
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        self.timeout = timeout

        # Async components
        self._session: Optional[httpx.AsyncClient] = None
        self._batch: List[Dict[str, Any]] = []
        self._batch_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

        # Local fallback logging
        self._local_logger = logging.getLogger(f"{service_name}_logs")
        if not self._local_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(f"[{service_name}] %(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self._local_logger.addHandler(handler)
            self._local_logger.setLevel(logging.INFO)

        # Stats for monitoring
        self.stats = {"logs_sent": 0, "batches_sent": 0, "errors": 0, "retries": 0, "last_flush": None}

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Start the logging client."""
        if self._running:
            return

        self._running = True
        self._session = httpx.AsyncClient(timeout=self.timeout)

        # Start periodic flush task
        self._flush_task = asyncio.create_task(self._periodic_flush())

        self._log_local(
            "info",
            "Log collector client started",
            {"collector_url": self.collector_url, "batch_size": self.batch_size, "flush_interval": self.flush_interval},
        )

    async def stop(self):
        """Stop the logging client and flush remaining logs."""
        if not self._running:
            return

        self._running = False

        # Cancel periodic flush
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self._flush_batch(force=True)

        # Close session
        if self._session:
            await self._session.aclose()
            self._session = None

        self._log_local("info", "Log collector client stopped", self.stats)

    async def log_info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log an info-level message."""
        await self._log("info", message, context)

    async def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log a warning-level message."""
        await self._log("warning", message, context)

    async def log_error(
        self, message: str, context: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None
    ):
        """Log an error-level message."""
        if error:
            context = context or {}
            context["error_type"] = type(error).__name__
            context["error_message"] = str(error)

        await self._log("error", message, context)

    async def log_business_event(self, event_type: str, data: Dict[str, Any]):
        """Log a business event."""
        await self._log("info", f"Business event: {event_type}", {"event_type": event_type, **data})

    async def log_performance_metric(self, operation: str, duration: float, metadata: Optional[Dict[str, Any]] = None):
        """Log a performance metric."""
        context = {"operation": operation, "duration_seconds": duration, "performance_metric": True}
        if metadata:
            context.update(metadata)

        await self._log("info", f"Performance: {operation}", context)

    async def _log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None):
        """Internal logging method."""
        log_entry = {
            "service": self.service_name,
            "level": level,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context or {},
        }

        async with self._batch_lock:
            self._batch.append(log_entry)

            # Flush if batch is full
            if len(self._batch) >= self.batch_size:
                await self._flush_batch()

    async def _periodic_flush(self):
        """Periodically flush the batch."""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log_local("error", f"Periodic flush failed: {e}")
                self.stats["errors"] += 1

    async def _flush_batch(self, force: bool = False):
        """Flush the current batch to the log collector."""
        async with self._batch_lock:
            if not self._batch:
                return

            batch_to_send = self._batch.copy()
            self._batch.clear()

        if not self._session:
            # Fallback to local logging
            for log_entry in batch_to_send:
                self._log_local(log_entry["level"], log_entry["message"], log_entry["context"])
            return

        # Send batch with retries
        success = False
        for attempt in range(self.max_retries):
            try:
                response = await self._session.post(
                    f"{self.collector_url}/logs/batch",
                    json={"items": batch_to_send},
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    success = True
                    self.stats["logs_sent"] += len(batch_to_send)
                    self.stats["batches_sent"] += 1
                    self.stats["last_flush"] = datetime.now(timezone.utc).isoformat()
                    break
                else:
                    self._log_local("warning", f"Log collector returned {response.status_code}: {response.text}")

            except Exception as e:
                self.stats["retries"] += 1
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.1 * (2**attempt))  # Exponential backoff
                else:
                    self._log_local("error", f"Failed to send logs after {self.max_retries} attempts: {e}")
                    # Fallback to local logging
                    for log_entry in batch_to_send:
                        self._log_local(log_entry["level"], log_entry["message"], log_entry["context"])

        if not success:
            self.stats["errors"] += 1

    def _log_local(self, level: str, message: str, context: Optional[Dict[str, Any]] = None):
        """Log to local logger as fallback."""
        context_str = f" {context}" if context else ""
        full_message = f"{message}{context_str}"

        if level == "debug":
            self._local_logger.debug(full_message)
        elif level == "info":
            self._local_logger.info(full_message)
        elif level == "warning":
            self._local_logger.warning(full_message)
        elif level == "error":
            self._local_logger.error(full_message)
        elif level == "fatal":
            self._local_logger.critical(full_message)
        else:
            self._local_logger.info(f"[{level}] {full_message}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self.stats,
            "batch_queue_size": len(self._batch),
            "is_running": self._running,
            "collector_url": self.collector_url,
        }


# Global client instances (lazy-loaded)
_clients: Dict[str, LogCollectorClient] = {}
_clients_lock = asyncio.Lock()


async def get_log_collector_client(service_name: str) -> LogCollectorClient:
    """
    Get or create a log collector client for the specified service.

    This function provides a centralized way to get logging clients and
    ensures only one client per service is created.
    """
    async with _clients_lock:
        if service_name not in _clients:
            client = LogCollectorClient(service_name)
            await client.start()
            _clients[service_name] = client

        return _clients[service_name]


async def shutdown_all_clients():
    """Shutdown all active log collector clients."""
    async with _clients_lock:
        shutdown_tasks = []
        for client in _clients.values():
            shutdown_tasks.append(client.stop())

        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks)

        _clients.clear()


# Convenience functions for easy logging
async def log_service_event(service_name: str, level: str, message: str, context: Optional[Dict[str, Any]] = None):
    """Log an event for a service."""
    client = await get_log_collector_client(service_name)

    if level == "info":
        await client.log_info(message, context)
    elif level == "warning":
        await client.log_warning(message, context)
    elif level == "error":
        await client.log_error(message, context)
    else:
        await client.log_info(f"[{level}] {message}", context)


async def log_business_event(service_name: str, event_type: str, data: Dict[str, Any]):
    """Log a business event for a service."""
    client = await get_log_collector_client(service_name)
    await client.log_business_event(event_type, data)


async def log_performance_metric(
    service_name: str, operation: str, duration: float, metadata: Optional[Dict[str, Any]] = None
):
    """Log a performance metric for a service."""
    client = await get_log_collector_client(service_name)
    await client.log_performance_metric(operation, duration, metadata)
