"""Logging Client for sending logs to the log collector service."""

import asyncio
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class LogCollectorClient:
    """Client for sending logs to the log collector service."""

    def __init__(self, collector_url: str = "http://localhost:5080", batch_size: int = 10, flush_interval: float = 5.0):
        """Initialize the log collector client."""
        self.collector_url = collector_url.rstrip("/")
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._queue: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None

    def start(self):
        """Start the log collector client."""
        with self._lock:
            if self._running:
                return
            self._running = True
            logger.info(
                "Log collector client started",
                extra={
                    "collector_url": self.collector_url,
                    "batch_size": self.batch_size,
                    "flush_interval": self.flush_interval,
                },
            )

    def stop(self):
        """Stop the log collector client."""
        with self._lock:
            if not self._running:
                return
            self._running = False
            if self._flush_task:
                self._flush_task.cancel()
            # Flush remaining logs
            if self._queue:
                asyncio.create_task(self._flush_logs())

    def log(self, message: str, level: str = "INFO", extra: Optional[Dict[str, Any]] = None, service: str = "unknown"):
        """Log a message."""
        if not self._running:
            return

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "service": service,
            "extra": extra or {},
        }

        with self._lock:
            self._queue.append(log_entry)
            if len(self._queue) >= self.batch_size:
                asyncio.create_task(self._flush_logs())

    async def _flush_logs(self):
        """Flush logs to the collector."""
        if not self._queue:
            return

        with self._lock:
            logs_to_send = self._queue[:]
            self._queue.clear()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.collector_url}/logs/batch", json={"logs": logs_to_send})
                response.raise_for_status()
                logger.debug(f"Sent {len(logs_to_send)} logs to collector")
        except Exception as e:
            logger.error(f"Failed to send logs after 3 attempts: {e}")
            # Put logs back in queue for retry
            with self._lock:
                self._queue.extend(logs_to_send)


# Global instance
_log_collector_client: Optional[LogCollectorClient] = None


def get_log_collector_client() -> LogCollectorClient:
    """Get the global log collector client instance."""
    global _log_collector_client
    if _log_collector_client is None:
        _log_collector_client = LogCollectorClient()
    return _log_collector_client


def init_log_collector_client(
    collector_url: str = "http://localhost:5080", batch_size: int = 10, flush_interval: float = 5.0
):
    """Initialize the global log collector client."""
    global _log_collector_client
    _log_collector_client = LogCollectorClient(collector_url, batch_size, flush_interval)
    _log_collector_client.start()
    return _log_collector_client
