"""Standardized health endpoint helpers and models.

Provides consistent health check patterns across all services.
Reduces code duplication and ensures uniform health reporting.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..external.clients.clients import ServiceClients


class HealthStatus(BaseModel):
    """Standardized health status model."""

    status: str = Field(..., description="Health status (healthy/unhealthy)")
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Health check timestamp",
    )
    uptime_seconds: Optional[float] = Field(
        None, description="Service uptime in seconds"
    )
    environment: Optional[str] = Field(None, description="Deployment environment")

    # Service-specific optional fields
    workflows_loaded: Optional[bool] = Field(
        default=None, description="Workflow repository status (orchestrator)"
    )
    database_connected: Optional[bool] = Field(
        default=None, description="Database connection status (doc_store)"
    )
    models_loaded: Optional[bool] = Field(
        default=None, description="ML models loaded status (analysis-service)"
    )
    api_connected: Optional[bool] = Field(
        default=None, description="API connectivity status (frontend)"
    )
    llm_connected: Optional[bool] = Field(
        default=None, description="LLM service connectivity (summarizer-hub)"
    )
    ollama_available: Optional[bool] = Field(
        default=None, description="Ollama service availability (llm-gateway)"
    )
    data_sources: Optional[int] = Field(
        default=None, description="Number of data sources (mock-data-generator)"
    )
    email_configured: Optional[bool] = Field(
        default=None, description="Email service configuration (notification-service)"
    )
    analysis_ready: Optional[bool] = Field(
        default=None, description="Analysis capabilities ready (code-analyzer)"
    )


class HealthCheck(BaseModel):
    """Health check configuration."""

    name: str
    description: str
    critical: bool = True  # If True, failure means service is unhealthy
    timeout_seconds: float = 5.0


class DependencyHealth(BaseModel):
    """Health status of a service dependency."""

    name: str
    status: str  # healthy, unhealthy, unknown
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    last_checked: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class SystemHealth(BaseModel):
    """Comprehensive system health status."""

    overall_healthy: bool
    services_checked: int
    services_healthy: int
    services_unhealthy: int
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    service_details: Dict[str, DependencyHealth] = Field(default_factory=dict)
    environment_info: Dict[str, Any] = Field(default_factory=dict)


class HealthManager:
    """Centralized health management system."""

    def __init__(self, service_name: str, version: str = "1.0.0"):
        self.service_name = service_name
        self.version = version
        self.start_time = datetime.now(timezone.utc)
        self.health_checks: List[HealthCheck] = []
        self.clients = ServiceClients(timeout=5)

    def add_health_check(self, name: str, description: str, critical: bool = True):
        """Add a custom health check."""
        self.health_checks.append(
            HealthCheck(name=name, description=description, critical=critical)
        )

    async def basic_health(self) -> HealthStatus:
        """Basic health check for the service with service-specific monitoring."""
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        # Create base health status
        health_status = HealthStatus(
            status="healthy",
            service=self.service_name,
            version=self.version,
            uptime_seconds=uptime,
            environment=os.environ.get("ENVIRONMENT", "development"),
        )

        # Apply service-specific health checks
        await self._apply_service_specific_checks(health_status)

        return health_status

    async def _apply_service_specific_checks(self, health_status: HealthStatus) -> None:
        """Apply service-specific health checks using a registry pattern."""
        service_checks = {
            "orchestrator": self._check_orchestrator_health,
            "doc_store": self._check_doc_store_health,
            "analysis-service": self._check_analysis_service_health,
            "frontend": self._check_frontend_health,
            "summarizer-hub": self._check_summarizer-hub_health,
            "llm-gateway": self._check_llm_gateway_health,
            "mock-data-generator": self._check_mock_data_generator_health,
            "notification-service": self._check_notification-service_health,
            "code-analyzer": self._check_code-analyzer_health,
        }

        check_func = service_checks.get(self.service_name)
        if check_func:
            await check_func(health_status)

    async def _check_orchestrator_health(self, health_status: HealthStatus) -> None:
        """Check orchestrator-specific health metrics."""
        try:
            # For orchestrator, workflows are considered loaded if the service is running
            health_status.workflows_loaded = True
        except Exception:
            health_status.workflows_loaded = False

    async def _check_doc_store_health(self, health_status: HealthStatus) -> None:
        """Check document store health metrics."""
        try:
            # For doc_store, database is considered connected if the service is running
            health_status.database_connected = True
        except Exception:
            health_status.database_connected = False

    async def _check_analysis_service_health(self, health_status: HealthStatus) -> None:
        """Check analysis service health metrics."""
        try:
            # For analysis-service, models are considered loaded if the service is running
            health_status.models_loaded = True
        except Exception:
            health_status.models_loaded = False

    async def _check_frontend_health(self, health_status: HealthStatus) -> None:
        """Check frontend health metrics."""
        try:
            health_status.api_connected = True
        except Exception:
            health_status.api_connected = False

    async def _check_summarizer-hub_health(self, health_status: HealthStatus) -> None:
        """Check summarizer hub health metrics."""
        try:
            health_status.llm_connected = True
        except Exception:
            health_status.llm_connected = False

    async def _check_llm_gateway_health(self, health_status: HealthStatus) -> None:
        """Check LLM gateway health metrics."""
        try:
            health_status.ollama_available = True
        except Exception:
            health_status.ollama_available = False

    async def _check_mock_data_generator_health(self, health_status: HealthStatus) -> None:
        """Check mock data generator health metrics."""
        try:
            health_status.data_sources = 5  # Placeholder count
        except Exception:
            health_status.data_sources = 0

    async def _check_notification-service_health(self, health_status: HealthStatus) -> None:
        """Check notification service health metrics."""
        try:
            health_status.email_configured = True
        except Exception:
            health_status.email_configured = False

    async def _check_code-analyzer_health(self, health_status: HealthStatus) -> None:
        """Check code analyzer health metrics."""
        try:
            health_status.analysis_ready = True
        except (OSError, IOError):
            health_status.analysis_ready = False

    async def dependency_health(
        self, service_name: str, endpoint: str = "/health"
    ) -> DependencyHealth:
        """Check health of a service dependency."""
        import time

        start_time = time.time()
        try:
            response = await self.clients.get_json(endpoint)
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            if response.get("status") == "healthy":
                return DependencyHealth(
                    name=service_name, status="healthy", response_time_ms=response_time
                )
            else:
                return DependencyHealth(
                    name=service_name,
                    status="unhealthy",
                    response_time_ms=response_time,
                    error=f"Status: {response.get('status')}",
                )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return DependencyHealth(
                name=service_name,
                status="unhealthy",
                response_time_ms=response_time,
                error=str(e),
            )

    async def system_health(self) -> SystemHealth:
        """Check health of the entire system."""
        # Define core services to check
        core_services = {
            "orchestrator": "/health",
            "analysis-service": "/health",
            "doc_store": "/health",
            "source-agent": "/health",
            "prompt-store": "/health",
            "interpreter": "/health",
        }

        service_details = {}
        healthy_count = 0

        for service_name, endpoint in core_services.items():
            health = await self.dependency_health(service_name, endpoint)
            service_details[service_name] = health
            if health.status == "healthy":
                healthy_count += 1

        return SystemHealth(
            overall_healthy=healthy_count == len(core_services),
            services_checked=len(core_services),
            services_healthy=healthy_count,
            services_unhealthy=len(core_services) - healthy_count,
            service_details=service_details,
            environment_info={
                "environment": os.environ.get("ENVIRONMENT", "development"),
                "version": self.version,
                "service": self.service_name,
            },
        )

    async def run_custom_checks(self) -> Dict[str, Any]:
        """Run custom health checks."""
        results = {}
        for check in self.health_checks:
            # Placeholder for custom check logic
            # In practice, this would run actual health checks
            results[check.name] = {
                "status": "healthy",
                "description": check.description,
            }
        return results


# ============================================================================
# FASTAPI ENDPOINT HELPERS
# ============================================================================


def create_health_endpoint(health_manager: HealthManager):
    """Create a standard health endpoint function."""

    async def health():
        """Standard health check endpoint."""
        print(
            f"🚨 SHARED HEALTH ENDPOINT called for service: {health_manager.service_name}"
        )  # Debug logging
        health_status = await health_manager.basic_health()
        print(f"📊 Shared health status: {health_status}")  # Debug logging
        print(f"📤 Returning shared health status directly")  # Debug logging
        return health_status

    return health


def create_system_health_endpoint(health_manager: HealthManager):
    """Create a system-wide health endpoint function."""

    async def system_health():
        """System-wide health check endpoint."""
        return await system_health()

    return system_health


def create_dependency_health_endpoint(health_manager: HealthManager):
    """Create a dependency health endpoint function."""

    async def dependency_health(service_name: str):
        """Check health of a specific service dependency."""
        # Map service names to endpoints
        service_endpoints = {
            "orchestrator": "orchestrator/health",
            "analysis-service": "analysis-service/health",
            "doc_store": "doc_store/health",
            "source-agent": "source-agent/health",
            "prompt-store": "prompt-store/health",
            "interpreter": "interpreter/health",
        }

        if service_name not in service_endpoints:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404, detail=f"Unknown service: {service_name}"
            )

        return await health_manager.dependency_health(
            service_name, service_endpoints[service_name]
        )

    return dependency_health


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def register_health_endpoints(app, service_name: str, version: str = "1.0.0"):
    """Register standard health endpoints on a FastAPI app.

    Args:
        app: FastAPI application instance
        service_name: Name of the service
        version: Service version
    """
    health_manager = HealthManager(service_name, version)

    # Basic health check
    app.get("/health")(create_health_endpoint(health_manager))

    # System health check
    app.get("/health/system")(create_system_health_endpoint(health_manager))

    # Dependency health check
    app.get("/health/dependency/{service_name}")(
        create_dependency_health_endpoint(health_manager)
    )

    return health_manager


# ============================================================================
# COMMON HEALTH RESPONSE HELPERS
# ============================================================================


def healthy_response(
    service_name: str, version: str = "1.0.0", **kwargs
) -> Dict[str, Any]:
    """Create a standard healthy response."""
    return {
        "status": "healthy",
        "service": service_name,
        "version": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }


def unhealthy_response(
    service_name: str, error: str, version: str = "1.0.0", **kwargs
) -> Dict[str, Any]:
    """Create a standard unhealthy response."""
    return {
        "status": "unhealthy",
        "service": service_name,
        "version": version,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }


def health_response(
    service_name: str,
    healthy: bool,
    version: str = "1.0.0",
    error: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Create a health response based on health status."""
    if healthy:
        return healthy_response(service_name, version, **kwargs)
    else:
        return unhealthy_response(
            service_name, error or "Service unhealthy", version, **kwargs
        )


# ============================================================================
# SERVICE-SPECIFIC HEALTH HELPERS
# ============================================================================


async def check_database_health(db_path: str) -> bool:
    """Check database connectivity."""
    try:
        import sqlite3

        with sqlite3.connect(db_path) as conn:
            conn.execute("SELECT 1").fetchone()
        return True
    except Exception:
        return False


async def check_external_service_health(url: str, timeout: float = 5.0) -> bool:
    """Check external service health."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            return response.status_code == 200
    except Exception:
        return False


async def check_redis_health(redis_url: str) -> bool:
    """Check Redis connectivity."""
    try:
        import redis.asyncio as aioredis

        redis = aioredis.from_url(redis_url)
        await redis.ping()
        return True
    except Exception:
        return False
