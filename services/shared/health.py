"""Standardized health endpoint helpers and models.

Provides consistent health check patterns across all services.
Reduces code duplication and ensures uniform health reporting.
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from .clients import ServiceClients


class HealthStatus(BaseModel):
    """Standardized health status model."""
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Health check timestamp")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    environment: Optional[str] = Field(None, description="Deployment environment")


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
    last_checked: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SystemHealth(BaseModel):
    """Comprehensive system health status."""
    overall_healthy: bool
    services_checked: int
    services_healthy: int
    services_unhealthy: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
        self.health_checks.append(HealthCheck(
            name=name,
            description=description,
            critical=critical
        ))

    async def basic_health(self) -> HealthStatus:
        """Basic health check for the service."""
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        return HealthStatus(
            status="healthy",
            service=self.service_name,
            version=self.version,
            uptime_seconds=uptime,
            environment=os.environ.get("ENVIRONMENT", "development")
        )

    async def dependency_health(self, service_name: str, endpoint: str = "/health") -> DependencyHealth:
        """Check health of a service dependency."""
        import time

        start_time = time.time()
        try:
            response = await self.clients.get_json(endpoint)
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            if response.get("status") == "healthy":
                return DependencyHealth(
                    name=service_name,
                    status="healthy",
                    response_time_ms=response_time
                )
            else:
                return DependencyHealth(
                    name=service_name,
                    status="unhealthy",
                    response_time_ms=response_time,
                    error=f"Status: {response.get('status')}"
                )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return DependencyHealth(
                name=service_name,
                status="unhealthy",
                response_time_ms=response_time,
                error=str(e)
            )

    async def system_health(self) -> SystemHealth:
        """Check health of the entire system."""
        # Define core services to check
        core_services = {
            "orchestrator": "/health",
            "analysis-service": "/health",
            "doc-store": "/health",
            "source-agent": "/health",
            "prompt-store": "/health",
            "interpreter": "/health"
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
                "service": self.service_name
            }
        )

    async def run_custom_checks(self) -> Dict[str, Any]:
        """Run custom health checks."""
        results = {}
        for check in self.health_checks:
            # Placeholder for custom check logic
            # In practice, this would run actual health checks
            results[check.name] = {
                "status": "healthy",
                "description": check.description
            }
        return results


# ============================================================================
# FASTAPI ENDPOINT HELPERS
# ============================================================================

def create_health_endpoint(health_manager: HealthManager):
    """Create a standard health endpoint function."""
    async def health():
        """Standard health check endpoint."""
        return await health_manager.basic_health()
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
            "doc-store": "doc-store/health",
            "source-agent": "source-agent/health",
            "prompt-store": "prompt-store/health",
            "interpreter": "interpreter/health"
        }

        if service_name not in service_endpoints:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")

        return await health_manager.dependency_health(service_name, service_endpoints[service_name])
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
    app.get("/health/dependency/{service_name}")(create_dependency_health_endpoint(health_manager))

    return health_manager


# ============================================================================
# COMMON HEALTH RESPONSE HELPERS
# ============================================================================

def healthy_response(service_name: str, version: str = "1.0.0", **kwargs) -> Dict[str, Any]:
    """Create a standard healthy response."""
    return {
        "status": "healthy",
        "service": service_name,
        "version": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs
    }


def unhealthy_response(service_name: str, error: str, version: str = "1.0.0", **kwargs) -> Dict[str, Any]:
    """Create a standard unhealthy response."""
    return {
        "status": "unhealthy",
        "service": service_name,
        "version": version,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs
    }


def health_response(service_name: str, healthy: bool, version: str = "1.0.0",
                   error: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Create a health response based on health status."""
    if healthy:
        return healthy_response(service_name, version, **kwargs)
    else:
        return unhealthy_response(service_name, error or "Service unhealthy", version, **kwargs)


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
