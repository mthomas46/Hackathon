"""Service: Log Collector

Endpoints:
- POST /logs: Store a single log entry
- POST /logs/batch: Store multiple log entries at once
- GET /logs: Retrieve logs with optional filtering by service/level
- GET /stats: Get aggregated statistics and analytics
- GET /health: Health check with current log count

Responsibilities:
- Receive structured log entries from various services
- Maintain bounded in-memory history for recent logs
- Provide basic aggregation and filtering capabilities
- Enable quick diagnostics through statistics endpoint
- Integrated with standardized logging and monitoring system

Dependencies: shared middlewares for request tracking and metrics.
"""
import asyncio
import time
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import threading
import os

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None

from services.shared.infrastructure.utilities.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore
from services.shared.infrastructure.logging.standardized_logger import StandardizedLogger, performance_monitor

try:
    from .modules.log_storage import log_storage
    from .modules.log_stats import calculate_log_statistics
except ImportError:
    # Fallback for when running as script
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from modules.log_storage import log_storage
    from modules.log_stats import calculate_log_statistics

# Service configuration constants
SERVICE_NAME = "log-collector"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = 5080

# Default limits and constraints
DEFAULT_MAX_LOGS = 5000
DEFAULT_QUERY_LIMIT = 100

# Initialize standardized logger and monitoring
logger = StandardizedLogger(SERVICE_NAME, {
    "log_level": "INFO",
    "structured_logging": True,
    "monitoring_enabled": True,
    "metrics_interval": 30,
    "console_logging": True,
    "log_file": f"/tmp/{SERVICE_NAME}.log",
    "max_log_size": 10485760,  # 10MB
    "backup_count": 5
})
logger.start_monitoring()

# Service health monitor will be initialized after app startup
service_health_monitor = None


class ServiceHealthMonitor:
    """Monitors health status of all ecosystem services for logging safeguards."""

    def __init__(self, logger: StandardizedLogger):
        self.logger = logger
        self.service_endpoints = self._get_service_endpoints()
        self.health_status = {}
        self.monitoring_thread = None
        self.monitoring_active = False
        self.check_interval = int(os.environ.get("SERVICE_HEALTH_CHECK_INTERVAL", "30"))  # seconds
        self.enable_health_safeguards = os.environ.get("ENABLE_HEALTH_SAFEGUARDS", "true").lower() == "true"

    def _get_service_endpoints(self) -> Dict[str, str]:
        """Get all service health endpoints from environment or defaults."""
        # Core ecosystem services with their health endpoints
        services = {
            "orchestrator": os.environ.get("ORCHESTRATOR_URL", "http://orchestrator:5099") + "/health",
            "doc_store": os.environ.get("DOC_STORE_URL", "http://doc_store:5005") + "/health",
            "analysis-service": os.environ.get("ANALYSIS_SERVICE_URL", "http://analysis-service:5020") + "/health",
            "source-agent": os.environ.get("SOURCE_AGENT_URL", "http://source-agent:5085") + "/health",
            "summarizer-hub": os.environ.get("SUMMARIZER_HUB_URL", "http://summarizer-hub:5160") + "/health",
            "interpreter": os.environ.get("INTERPRETER_URL", "http://interpreter:5120") + "/health",
            "llm-gateway": os.environ.get("LLM_GATEWAY_URL", "http://llm-gateway:5055") + "/health",
            "memory-agent": os.environ.get("MEMORY_AGENT_URL", "http://memory-agent:5090") + "/health",
            "user-store": os.environ.get("USER_STORE_URL", "http://user-store:5150") + "/health",
            "external-service-store": os.environ.get("EXTERNAL_SERVICE_STORE_URL", "http://external-service-store:5140") + "/health",
            "project-simulation": os.environ.get("PROJECT_SIMULATION_URL", "http://project-simulation:5075") + "/health",
            "frontend": os.environ.get("FRONTEND_URL", "http://frontend:3000") + "/health",
            "notification-service": os.environ.get("NOTIFICATION_SERVICE_URL", "http://notification-service:5130") + "/health",
            "code-analyzer": os.environ.get("CODE_ANALYZER_URL", "http://code-analyzer:5025") + "/health",
            "secure-analyzer": os.environ.get("SECURE_ANALYZER_URL", "http://secure-analyzer:5100") + "/health",
            "architecture-digitizer": os.environ.get("ARCHITECTURE_DIGITIZER_URL", "http://architecture-digitizer:5105") + "/health",
            "discovery-agent": os.environ.get("DISCOVERY_AGENT_URL", "http://discovery-agent:5045") + "/health",
            "github-mcp": os.environ.get("GITHUB_MCP_URL", "http://github-mcp:5030") + "/health",
            "bedrock-proxy": os.environ.get("BEDROCK_PROXY_URL", "http://bedrock-proxy:5060") + "/health",
            "mock-data-generator": os.environ.get("MOCK_DATA_GENERATOR_URL", "http://mock-data-generator:5065") + "/health",
            "simulation-dashboard": os.environ.get("SIMULATION_DASHBOARD_URL", "http://simulation-dashboard:8501") + "/health",
            "unified-api-dashboard": os.environ.get("UNIFIED_API_DASHBOARD_URL", "http://unified-api-dashboard:8000") + "/health",
            "prompt_store": os.environ.get("PROMPT_STORE_URL", "http://prompt_store:5110") + "/health",
            "ollama": os.environ.get("OLLAMA_URL", "http://ollama:11434") + "/health",
            "redis": os.environ.get("REDIS_URL", "http://redis:6379") + "/ping"
        }
        return services

    def start_monitoring(self):
        """Start the health monitoring thread."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="service-health-monitor"
            )
            self.monitoring_thread.start()
            self.logger.info("🏥 Service health monitoring started", extra={
                "services_count": len(self.service_endpoints),
                "check_interval": self.check_interval
            })

    def stop_monitoring(self):
        """Stop the health monitoring thread."""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)
            self.logger.info("🏥 Service health monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop that checks service health periodically."""
        while self.monitoring_active:
            try:
                asyncio.run(self._check_all_services_health())
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                time.sleep(self.check_interval)

    async def _check_all_services_health(self):
        """Check health of all services concurrently."""
        tasks = []
        for service_name, health_url in self.service_endpoints.items():
            tasks.append(self._check_service_health(service_name, health_url))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_service_health(self, service_name: str, health_url: str):
        """Check health of a single service."""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                response_time = time.time() - start_time

                if response.status_code == 200:
                    health_data = response.json()
                    status = health_data.get("status", "unknown")

                    # Update health status
                    self.health_status[service_name] = {
                        "status": "healthy" if status == "healthy" else "unhealthy",
                        "response_time": response_time,
                        "last_check": time.time(),
                        "details": health_data
                    }

                    if status != "healthy":
                        self.logger.warning(f"Service {service_name} reported unhealthy status", extra={
                            "service": service_name,
                            "status": status,
                            "response_time": response_time,
                            "health_url": health_url
                        })
                else:
                    self._mark_service_unhealthy(service_name, f"HTTP {response.status_code}", response_time, health_url)

        except Exception as e:
            self._mark_service_unhealthy(service_name, str(e), time.time() - start_time, health_url)

    def _mark_service_unhealthy(self, service_name: str, error: str, response_time: float, health_url: str):
        """Mark a service as unhealthy."""
        self.health_status[service_name] = {
            "status": "unhealthy",
            "error": error,
            "response_time": response_time,
            "last_check": time.time()
        }

        self.logger.warning(f"Service {service_name} health check failed", extra={
            "service": service_name,
            "error": error,
            "response_time": response_time,
            "health_url": health_url
        })

    def get_service_health(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get health status of services."""
        if service_name:
            return self.health_status.get(service_name, {"status": "unknown"})

        # Return summary of all services
        healthy = sum(1 for status in self.health_status.values() if status.get("status") == "healthy")
        unhealthy = sum(1 for status in self.health_status.values() if status.get("status") == "unhealthy")
        unknown = len(self.service_endpoints) - healthy - unhealthy

        return {
            "total_services": len(self.service_endpoints),
            "healthy": healthy,
            "unhealthy": unhealthy,
            "unknown": unknown,
            "services": self.health_status,
            "last_updated": max((status.get("last_check", 0) for status in self.health_status.values()), default=0)
        }

    def is_service_healthy(self, service_name: str) -> bool:
        """Check if a specific service is healthy."""
        service_status = self.health_status.get(service_name, {})
        return service_status.get("status") == "healthy"


app = FastAPI(
    title="Log Collector",
    version=SERVICE_VERSION,
    description="Centralized log collection service for distributed systems with standardized logging"
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name=SERVICE_NAME)


async def startup_event():
    """Initialize service health monitor on startup."""
    global service_health_monitor
    if HTTPX_AVAILABLE:
        service_health_monitor = ServiceHealthMonitor(logger)
        service_health_monitor.start_monitoring()
        logger.info("🚀 Log Collector service health monitoring initialized")
    else:
        logger.warning("⚠️ httpx not available, service health monitoring disabled")
        service_health_monitor = None

# Add startup event handler
app.add_event_handler("startup", startup_event)

# Store logger instance for access in endpoints
app.state.logger = logger


class LogItem(BaseModel):
    """Structured log entry data model for consistent logging across services.

    All log entries follow this standard format to enable consistent
    storage, filtering, and analysis across the system.
    """
    service: str
    """Service name that generated the log entry (e.g., 'api-gateway', 'user-service')."""

    level: str
    """Log level: 'debug', 'info', 'warning', 'error', 'fatal', etc."""

    message: str
    """Human-readable log message describing the event."""

    timestamp: Optional[str] = None
    """ISO 8601 timestamp. Auto-generated if not provided."""

    context: Optional[Dict[str, Any]] = None
    """Additional structured context data (request_id, user_id, etc.)."""


@app.get("/health")
async def health(request: Request):
    """Health check endpoint returning service status and current log count.

    Provides comprehensive service health information including the current
    number of stored log entries and ecosystem service health monitoring.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Get basic health data
        health_data = {
            "status": "healthy",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "count": log_storage.get_count(),
            "description": "Log collection service is operational"
        }

        # Add monitoring data from standardized logger
        monitoring_health = logger_instance.get_health_status()
        health_data["monitoring"] = monitoring_health

        # Add service health monitoring data
        if service_health_monitor:
            service_health_summary = service_health_monitor.get_service_health()
            health_data["service_health"] = {
                "total_services": service_health_summary.get("total_services", 0),
                "healthy": service_health_summary.get("healthy", 0),
                "unhealthy": service_health_summary.get("unhealthy", 0),
                "unknown": service_health_summary.get("unknown", 0),
                "last_updated": service_health_summary.get("last_updated", 0)
            }

            # Determine overall health status
            if service_health_summary.get("unhealthy", 0) > 0:
                health_data["status"] = "degraded"
                health_data["description"] = f"Log collection operational but {service_health_summary['unhealthy']} services unhealthy"
        else:
            health_data["service_health"] = {
                "status": "disabled",
                "message": "Service health monitoring not available"
            }

        # Log successful health check
        response_time = time.time() - start_time
        logger_instance.log_request("GET", "/health", 200, response_time,
                                  extra={
                                      "log_count": health_data["count"],
                                      "services_healthy": health_data["service_health"]["healthy"],
                                      "services_unhealthy": health_data["service_health"]["unhealthy"]
                                  })

        return health_data

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {"endpoint": "/health"})

        # Return error health status
        return {
            "status": "unhealthy",
            "service": SERVICE_NAME,
            "error": str(e),
            "description": "Log collection service encountered an error"
        }


@app.post("/logs")
async def put_log(item: LogItem, request: Request, response: Response):
    """Store a single log entry in the collection.

    Accepts a structured log entry and stores it with automatic timestamp
    generation if not provided. Returns the current total log count.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Health safeguard: Check if we're accepting logs from unhealthy services
        if service_health_monitor and service_health_monitor.enable_health_safeguards:
            source_service = item.service
            if source_service and not service_health_monitor.is_service_healthy(source_service):
                logger_instance.warning(f"Rejected log from unhealthy service: {source_service}", extra={
                    "rejected_service": source_service,
                    "log_level": item.level,
                    "reason": "service_unhealthy"
                })
                response.status_code = 503  # Service Unavailable
                return {
                    "status": "rejected",
                    "message": f"Service {source_service} is currently unhealthy",
                    "reason": "service_unhealthy"
                }

        # Add log entry
        count = log_storage.add_log(item.model_dump())

        # Log successful log storage
        response_time = time.time() - start_time
        logger_instance.log_request("POST", "/logs", 200, response_time,
                                  extra={
                                      "log_service": item.service,
                                      "log_level": item.level,
                                      "total_logs": count
                                  })

        # Log business event for log collection
        logger_instance.log_business_event("log_collected", {
            "service": item.service,
            "level": item.level,
            "message_length": len(item.message),
            "has_context": item.context is not None
        })

        return {"status": "ok", "count": count}

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {
            "endpoint": "/logs",
            "log_service": item.service if item else "unknown",
            "log_level": item.level if item else "unknown"
        })

        response.status_code = 500
        return {"status": "error", "message": "Failed to store log entry"}


class LogBatch(BaseModel):
    """Batch of multiple log entries for efficient bulk submission.

    Used when multiple log entries need to be submitted together,
    reducing the number of individual API calls.
    """
    items: List[LogItem]
    """List of log entries to store."""


@app.post("/logs/batch")
async def put_logs(batch: LogBatch, request: Request, response: Response):
    """Store multiple log entries in a single batch operation.

    This endpoint allows efficient bulk submission of multiple log entries,
    reducing network overhead compared to individual log submissions.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Health safeguard: Filter out logs from unhealthy services
        if service_health_monitor and service_health_monitor.enable_health_safeguards:
            filtered_items = []
            rejected_services = set()

            for item in batch.items:
                source_service = item.service
                if source_service and service_health_monitor.is_service_healthy(source_service):
                    filtered_items.append(item)
                else:
                    rejected_services.add(source_service or "unknown")

            if rejected_services:
                logger_instance.warning(f"Rejected logs from unhealthy services: {list(rejected_services)}", extra={
                    "rejected_services": list(rejected_services),
                    "original_batch_size": len(batch.items),
                    "filtered_batch_size": len(filtered_items),
                    "reason": "service_unhealthy"
                })

            # Update batch with filtered items
            batch.items = filtered_items

            # If no healthy services remain, reject the entire batch
            if not filtered_items:
                response.status_code = 503  # Service Unavailable
                return {
                    "status": "rejected",
                    "message": "All services in batch are currently unhealthy",
                    "reason": "all_services_unhealthy",
                    "rejected_services": list(rejected_services)
                }

        # Add batch log entries
        entries = [item.model_dump() for item in batch.items]
        count = log_storage.add_logs_batch(entries)

        # Log successful batch storage
        response_time = time.time() - start_time
        logger_instance.log_request("POST", "/logs/batch", 200, response_time,
                                  extra={
                                      "batch_size": len(batch.items),
                                      "total_logs": count
                                  })

        # Log business event for batch collection
        logger_instance.log_business_event("log_batch_collected", {
            "batch_size": len(batch.items),
            "total_logs": count,
            "services": list(set(item.service for item in batch.items)),
            "levels": list(set(item.level for item in batch.items))
        })

        return {"status": "ok", "count": count, "added": len(batch.items)}

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {
            "endpoint": "/logs/batch",
            "batch_size": len(batch.items) if batch else 0
        })

        response.status_code = 500
        return {"status": "error", "message": "Failed to store log batch"}


@app.get("/logs")
async def list_logs(request: Request, service: Optional[str] = None, level: Optional[str] = None,
                   limit: int = 100):
    """Retrieve logs with optional filtering by service and/or log level.

    Supports filtering logs by service name, log level, and limiting the number
    of results. Returns the most recent logs matching the criteria.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Get logs with filtering
        logs = log_storage.get_logs(service=service, level=level, limit=limit)

        # Log successful query
        response_time = time.time() - start_time
        logger_instance.log_request("GET", "/logs", 200, response_time,
                                  extra={
                                      "service_filter": service,
                                      "level_filter": level,
                                      "limit": limit,
                                      "results_count": len(logs)
                                  })

        return {"items": logs}

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {
            "endpoint": "/logs",
            "service_filter": service,
            "level_filter": level
        })

        return {"error": "Failed to retrieve logs", "message": str(e)}


@app.get("/stats")
async def stats(request: Request):
    """Get comprehensive log statistics and aggregations.

    Returns aggregated statistics including counts by level, service,
    error rates, and top services by log volume for system monitoring.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Get all logs and calculate statistics
        all_logs = log_storage.get_all_logs()
        stats_data = calculate_log_statistics(all_logs)

        # Log successful stats query
        response_time = time.time() - start_time
        logger_instance.log_request("GET", "/stats", 200, response_time,
                                  extra={
                                      "total_logs": stats_data.get("total_logs", 0),
                                      "services_count": len(stats_data.get("by_service", {})),
                                      "error_rate": stats_data.get("error_rate", 0)
                                  })

        # Log business event for stats access
        logger_instance.log_business_event("log_stats_accessed", {
            "total_logs": stats_data.get("total_logs", 0),
            "unique_services": len(stats_data.get("by_service", {})),
            "time_range": stats_data.get("time_range", "unknown")
        })

        return stats_data

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {"endpoint": "/stats"})

        return {"error": "Failed to calculate statistics", "message": str(e)}


@app.get("/health/services")
async def get_services_health(request: Request, service: Optional[str] = None):
    """Get health status of all ecosystem services.

    Returns comprehensive health information for all services that the
    log collector monitors, including response times and last check times.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Check if service health monitor is available
        if not service_health_monitor:
            return {"error": "Service health monitoring not available", "message": "httpx not available or monitoring disabled"}

        # Get service health data
        health_data = service_health_monitor.get_service_health(service)

        # Log successful health query
        response_time = time.time() - start_time
        logger_instance.log_request("GET", "/health/services", 200, response_time,
                                  extra={
                                      "service_filter": service,
                                      "total_services": health_data.get("total_services", 0),
                                      "healthy_count": health_data.get("healthy", 0),
                                      "unhealthy_count": health_data.get("unhealthy", 0)
                                  })

        return health_data

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {"endpoint": "/health/services"})

        return {"error": "Failed to get service health", "message": str(e)}


@app.get("/health/services/{service_name}")
async def get_service_health(request: Request, service_name: str):
    """Get health status of a specific service.

    Returns detailed health information for a single service including
    response times, error details, and last check timestamp.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Check if service health monitor is available
        if not service_health_monitor:
            return {"error": f"Service health monitoring not available for {service_name}", "message": "httpx not available or monitoring disabled"}

        # Get specific service health data
        health_data = service_health_monitor.get_service_health(service_name)

        # Log successful health query
        response_time = time.time() - start_time
        logger_instance.log_request("GET", f"/health/services/{service_name}", 200, response_time,
                                  extra={
                                      "service": service_name,
                                      "status": health_data.get("status", "unknown")
                                  })

        return health_data

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {
            "endpoint": f"/health/services/{service_name}",
            "service": service_name
        })

        return {"error": f"Failed to get health for service {service_name}", "message": str(e)}


if __name__ == "__main__":
    """Run the Log Collector service directly."""
    import uvicorn
    import atexit

    # Log service startup
    logger.info("Starting Log Collector service", port=DEFAULT_PORT, version=SERVICE_VERSION)

    # Register cleanup function
    @atexit.register
    def cleanup():
        logger.info("Shutting down Log Collector service")
        logger.stop_monitoring()
        service_health_monitor.stop_monitoring()

    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=DEFAULT_PORT,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service failed to start: {e}")
        raise


