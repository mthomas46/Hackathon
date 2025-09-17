"""System Monitoring Domain Service"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..value_objects.health_status import HealthStatus
from ..value_objects.system_health import SystemHealth
from ..value_objects.service_health import ServiceHealth
from .health_check_service import HealthCheckService


class SystemMonitoringService:
    """Domain service for monitoring overall system health."""

    def __init__(
        self,
        health_check_service: HealthCheckService,
        known_services: Optional[List[str]] = None
    ):
        self._health_check_service = health_check_service
        self._known_services = known_services or [
            "orchestrator", "prompt_store", "interpreter",
            "analysis_service", "doc_store", "source_agent"
        ]
        self._system_metrics: Dict[str, Any] = {}
        self._last_system_check: Optional[datetime] = None

    async def perform_system_health_check(
        self,
        timeout_seconds: float = 5.0,
        include_metrics: bool = True
    ) -> SystemHealth:
        """Perform a comprehensive system health check."""
        # Check all known services
        service_health_list = await self._health_check_service.check_multiple_services(
            self._known_services,
            timeout_seconds
        )

        # Collect additional system metrics if requested
        metadata = {}
        if include_metrics:
            metadata.update(self._collect_system_metrics())

        # Update last check timestamp
        self._last_system_check = datetime.utcnow()

        return SystemHealth.from_service_health_list(
            service_health_list,
            metadata=metadata
        )

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        return {
            "uptime_seconds": self._get_system_uptime(),
            "active_workflows": self._system_metrics.get("active_workflows", 0),
            "total_services": len(self._known_services),
            "routes_count": self._system_metrics.get("routes_count", 0),
            "last_check": self._last_system_check.isoformat() if self._last_system_check else None
        }

    def _get_system_uptime(self) -> float:
        """Get system uptime in seconds."""
        # This would typically read from system stats
        # For now, return a mock value
        return 3600.0  # 1 hour

    def update_system_metrics(self, metrics: Dict[str, Any]):
        """Update system metrics."""
        self._system_metrics.update(metrics)

    async def get_service_health_details(
        self,
        service_name: str,
        timeout_seconds: float = 5.0
    ) -> ServiceHealth:
        """Get detailed health information for a specific service."""
        return await self._health_check_service.check_service_health(
            service_name,
            timeout_seconds
        )

    def get_known_services(self) -> List[str]:
        """Get list of known services in the system."""
        return self._known_services.copy()

    def add_known_service(self, service_name: str):
        """Add a service to the known services list."""
        if service_name not in self._known_services:
            self._known_services.append(service_name)

    def remove_known_service(self, service_name: str):
        """Remove a service from the known services list."""
        if service_name in self._known_services:
            self._known_services.remove(service_name)

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            "service": "orchestrator",
            "version": "1.0.0",
            "description": "Central control plane and service coordinator",
            "capabilities": ["coordination", "health_monitoring", "query_processing", "workflow_execution"],
            "known_services": self._known_services,
            "routes_count": self._system_metrics.get("routes_count", 0),
            "uptime_seconds": self._get_system_uptime(),
            "last_system_check": self._last_system_check.isoformat() if self._last_system_check else None
        }

    def get_system_config(self) -> Dict[str, Any]:
        """Get effective system configuration."""
        # This would typically read from configuration service
        # For now, return mock configuration
        return {
            "redis_enabled": True,
            "peer_orchestrators": [],
            "service_discovery_enabled": True,
            "event_driven_enabled": True,
            "health_check_timeout": 5.0,
            "max_concurrent_workflows": 10
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        metrics = self._collect_system_metrics()
        metrics.update({
            "service": "orchestrator",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        })
        return metrics

    def is_system_ready(self) -> bool:
        """Check if system is ready to handle requests."""
        # System is ready if orchestrator itself is healthy
        # In a full implementation, this would check critical dependencies
        return True
