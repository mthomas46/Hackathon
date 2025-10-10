"""
Logging client for sending logs to log-collector service.

Provides a centralized logging interface that sends structured logs
to the log-collector service for ecosystem-wide observability.
"""

import httpx
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from .retry import with_retry


class LogCollectorClient:
    """
    Client for sending logs to log-collector service.
    
    Sends structured JSON logs to the centralized log-collector service.
    Failures to send logs are non-blocking and won't crash the dashboard.
    
    Example:
        logger = LogCollectorClient(url="http://log-collector:5060")
        logger.info("Dashboard started", version="1.0.0")
        logger.error("Failed to fetch logs", service="doc_store", error=str(e))
    """
    
    def __init__(
        self,
        url: str = "http://localhost:8104",
        service_name: str = "data-services-dashboard"
    ):
        """
        Initialize logging client.
        
        Args:
            url: Log-collector service URL (default: http://localhost:8104)
            service_name: Name of this service (default: data-services-dashboard)
        """
        self.url = url
        self.service_name = service_name
        self.client = httpx.Client(timeout=2.0)
        self.enabled = True  # Can be disabled if log-collector unavailable
    
    @with_retry(max_attempts=2, delay=0.5)
    def _send_log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Internal method to send log to log-collector.
        
        Args:
            level: Log level (INFO, WARNING, ERROR)
            message: Log message
            context: Additional context data
            
        Raises:
            httpx exceptions on failure (after retries)
        """
        if not self.enabled:
            return
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": self.service_name,
            "level": level,
            "message": message,
            "context": context or {}
        }
        
        response = self.client.post(
            f"{self.url}/api/v1/logs",
            json=log_entry
        )
        response.raise_for_status()
    
    def send_log(
        self,
        level: str,
        message: str,
        **context
    ):
        """
        Send log to log-collector (non-blocking).
        
        Args:
            level: Log level (INFO, WARNING, ERROR)
            message: Log message
            **context: Additional context as keyword arguments
            
        Example:
            logger.send_log("INFO", "Fetched logs", service="doc_store", count=100)
        """
        try:
            self._send_log(level, message, context)
        except Exception as e:
            # Logging failures shouldn't break the dashboard
            # Just print to console for debugging
            print(f"⚠️  Failed to send log to log-collector: {e}")
    
    def info(self, message: str, **context):
        """
        Log INFO level message.
        
        Args:
            message: Log message
            **context: Additional context as keyword arguments
            
        Example:
            logger.info("Dashboard started", version="1.0.0", port=8501)
        """
        self.send_log("INFO", message, **context)
    
    def warning(self, message: str, **context):
        """
        Log WARNING level message.
        
        Args:
            message: Log message
            **context: Additional context as keyword arguments
            
        Example:
            logger.warning("Connection timeout", service="log-collector", retry=True)
        """
        self.send_log("WARNING", message, **context)
    
    def error(self, message: str, **context):
        """
        Log ERROR level message.
        
        Args:
            message: Log message
            **context: Additional context as keyword arguments
            
        Example:
            logger.error("Failed to parse log", log_id=log_id, error=str(e))
        """
        self.send_log("ERROR", message, **context)
    
    def debug(self, message: str, **context):
        """
        Log DEBUG level message (usually for development).
        
        Args:
            message: Log message
            **context: Additional context as keyword arguments
        """
        self.send_log("DEBUG", message, **context)
    
    def disable(self):
        """Disable logging (useful if log-collector unavailable)."""
        self.enabled = False
        print("ℹ️  Logging to log-collector disabled")
    
    def enable(self):
        """Enable logging."""
        self.enabled = True
        print("ℹ️  Logging to log-collector enabled")


# Global logger instance (can be imported and used throughout the dashboard)
logger = LogCollectorClient()


# Standard log events for dashboards
class DashboardLogger:
    """
    Dashboard-specific logging helpers with standard event types.
    
    Provides convenience methods for common dashboard events.
    """
    
    def __init__(self, logger: LogCollectorClient):
        self.logger = logger
    
    def dashboard_started(self, version: str, port: int = 8501):
        """Log dashboard startup."""
        self.logger.info("dashboard_started", version=version, port=port)
    
    def dashboard_stopped(self):
        """Log dashboard shutdown."""
        self.logger.info("dashboard_stopped")
    
    def fetching_logs(self, service: Optional[str], limit: int):
        """Log start of log fetching."""
        self.logger.info("fetching_logs", service=service or "all", limit=limit)
    
    def logs_fetched(self, service: Optional[str], count: int, duration_ms: float):
        """Log successful log fetch."""
        self.logger.info(
            "logs_fetched",
            service=service or "all",
            count=count,
            duration_ms=duration_ms
        )
    
    def fetch_timeout(self, service: str, timeout: float):
        """Log fetch timeout."""
        self.logger.warning("fetch_timeout", service=service, timeout_seconds=timeout)
    
    def fetch_failed(self, service: str, error: str):
        """Log fetch failure."""
        self.logger.error("fetch_failed", service=service, error=error)
    
    def filter_applied(self, service: Optional[str], time_range: str):
        """Log filter application."""
        self.logger.info("filter_applied", service=service, time_range=time_range)
    
    def tab_changed(self, tab: str):
        """Log tab change."""
        self.logger.info("tab_changed", tab=tab)
    
    def data_exported(self, format: str, rows: int):
        """Log data export."""
        self.logger.info("data_exported", format=format, rows=rows)
    
    def parsing_error(self, log_id: Optional[str], error: str):
        """Log parsing error."""
        self.logger.error("parsing_error", log_id=log_id, error=error)
    
    def validation_error(self, field: str, value: Any, error: str):
        """Log validation error."""
        self.logger.error("validation_error", field=field, value=str(value), error=error)
    
    def unexpected_error(self, error: str, traceback: Optional[str] = None):
        """Log unexpected error."""
        self.logger.error("unexpected_error", error=error, traceback=traceback)


# Global dashboard logger instance
dashboard_logger = DashboardLogger(logger)

