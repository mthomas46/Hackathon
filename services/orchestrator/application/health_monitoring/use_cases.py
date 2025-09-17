"""Use Cases for Health Monitoring"""

from typing import Dict, Any
from abc import ABC, abstractmethod

from .commands import *
from .queries import *
from ...domain.health_monitoring import (
    SystemHealth, ServiceHealth, HealthCheckService, SystemMonitoringService
)
from ...shared.domain import DomainResult


class UseCase(ABC):
    """Base class for all use cases."""

    @abstractmethod
    async def execute(self, *args, **kwargs):
        """Execute the use case."""
        pass


class CheckSystemHealthUseCase(UseCase):
    """Use case for checking overall system health."""

    def __init__(self, system_monitoring_service: SystemMonitoringService):
        self.system_monitoring_service = system_monitoring_service

    async def execute(self, command: CheckSystemHealthCommand) -> DomainResult[SystemHealth]:
        """Execute the check system health use case."""
        try:
            system_health = await self.system_monitoring_service.perform_system_health_check(
                timeout_seconds=command.timeout_seconds,
                include_metrics=command.include_metrics
            )
            return DomainResult.success_result(system_health, "System health check completed")
        except Exception as e:
            return DomainResult.single_error(f"Failed to check system health: {str(e)}")


class CheckServiceHealthUseCase(UseCase):
    """Use case for checking individual service health."""

    def __init__(self, health_check_service: HealthCheckService):
        self.health_check_service = health_check_service

    async def execute(self, command: CheckServiceHealthCommand) -> DomainResult[ServiceHealth]:
        """Execute the check service health use case."""
        try:
            service_health = await self.health_check_service.check_service_health(
                command.service_name,
                command.timeout_seconds
            )
            return DomainResult.success_result(service_health, f"Health check completed for {command.service_name}")
        except Exception as e:
            return DomainResult.single_error(f"Failed to check service health: {str(e)}")


class GetSystemHealthUseCase(UseCase):
    """Use case for getting system health information."""

    def __init__(self, system_monitoring_service: SystemMonitoringService):
        self.system_monitoring_service = system_monitoring_service

    async def execute(self, query: GetSystemHealthQuery) -> DomainResult[SystemHealth]:
        """Execute the get system health use case."""
        try:
            system_health = await self.system_monitoring_service.perform_system_health_check(
                timeout_seconds=query.timeout_seconds,
                include_metrics=query.include_metrics
            )
            return DomainResult.success_result(system_health, "System health retrieved successfully")
        except Exception as e:
            return DomainResult.single_error(f"Failed to get system health: {str(e)}")


class GetServiceHealthUseCase(UseCase):
    """Use case for getting individual service health."""

    def __init__(self, system_monitoring_service: SystemMonitoringService):
        self.system_monitoring_service = system_monitoring_service

    async def execute(self, query: GetServiceHealthQuery) -> DomainResult[ServiceHealth]:
        """Execute the get service health use case."""
        try:
            service_health = await self.system_monitoring_service.get_service_health_details(
                query.service_name,
                query.timeout_seconds
            )
            return DomainResult.success_result(service_health, f"Service health retrieved for {query.service_name}")
        except Exception as e:
            return DomainResult.single_error(f"Failed to get service health: {str(e)}")


class GetSystemInfoUseCase(UseCase):
    """Use case for getting system information."""

    def __init__(self, system_monitoring_service: SystemMonitoringService):
        self.system_monitoring_service = system_monitoring_service

    async def execute(self, query: GetSystemInfoQuery) -> DomainResult[Dict[str, Any]]:
        """Execute the get system info use case."""
        try:
            system_info = self.system_monitoring_service.get_system_info()
            return DomainResult.success_result(system_info, "System information retrieved successfully")
        except Exception as e:
            return DomainResult.single_error(f"Failed to get system info: {str(e)}")


class GetSystemMetricsUseCase(UseCase):
    """Use case for getting system metrics."""

    def __init__(self, system_monitoring_service: SystemMonitoringService):
        self.system_monitoring_service = system_monitoring_service

    async def execute(self, query: GetSystemMetricsQuery) -> DomainResult[Dict[str, Any]]:
        """Execute the get system metrics use case."""
        try:
            metrics = self.system_monitoring_service.get_system_metrics()
            return DomainResult.success_result(metrics, "System metrics retrieved successfully")
        except Exception as e:
            return DomainResult.single_error(f"Failed to get system metrics: {str(e)}")


class GetSystemConfigUseCase(UseCase):
    """Use case for getting system configuration."""

    def __init__(self, system_monitoring_service: SystemMonitoringService):
        self.system_monitoring_service = system_monitoring_service

    async def execute(self, query: GetSystemConfigQuery) -> DomainResult[Dict[str, Any]]:
        """Execute the get system config use case."""
        try:
            config = self.system_monitoring_service.get_system_config()
            return DomainResult.success_result(config, "System configuration retrieved successfully")
        except Exception as e:
            return DomainResult.single_error(f"Failed to get system config: {str(e)}")


class CheckSystemReadinessUseCase(UseCase):
    """Use case for checking system readiness."""

    def __init__(self, system_monitoring_service: SystemMonitoringService):
        self.system_monitoring_service = system_monitoring_service

    async def execute(self, query: CheckSystemReadinessQuery) -> DomainResult[Dict[str, Any]]:
        """Execute the check system readiness use case."""
        try:
            is_ready = self.system_monitoring_service.is_system_ready()
            result = {
                "status": "ready" if is_ready else "not_ready",
                "timestamp": "2024-01-01T00:00:00Z",  # Would use real timestamp
                "checks": {
                    "database": "ready",
                    "redis": "ready",
                    "services": "ready"
                }
            }
            return DomainResult.success_result(result, "Readiness check completed")
        except Exception as e:
            return DomainResult.single_error(f"Failed to check system readiness: {str(e)}")


class ListWorkflowsUseCase(UseCase):
    """Use case for listing available workflows (migrated from old health handlers)."""

    def __init__(self):
        # This would typically inject a workflow repository
        # For now, return static workflow definitions
        pass

    async def execute(self, query: ListWorkflowsQuery) -> DomainResult[Dict[str, Any]]:
        """Execute the list workflows use case."""
        try:
            workflows = [
                {
                    "id": "doc_ingestion",
                    "name": "Document Ingestion",
                    "description": "Ingest documents from various sources",
                    "steps": ["validate_source", "extract_content", "store_documents"],
                    "required_services": ["source-agent", "doc_store"],
                    "estimated_duration": 300
                },
                {
                    "id": "consistency_analysis",
                    "name": "Consistency Analysis",
                    "description": "Analyze documentation for consistency issues",
                    "steps": ["fetch_documents", "analyze_patterns", "generate_report"],
                    "required_services": ["doc_store", "analysis-service"],
                    "estimated_duration": 600
                },
                {
                    "id": "quality_assessment",
                    "name": "Quality Assessment",
                    "description": "Assess overall documentation quality",
                    "steps": ["collect_metrics", "analyze_quality", "generate_insights"],
                    "required_services": ["doc_store", "analysis-service"],
                    "estimated_duration": 450
                }
            ]

            # Apply pagination (simplified)
            start_idx = query.offset
            end_idx = start_idx + query.limit
            paginated_workflows = workflows[start_idx:end_idx]

            result = {"workflows": paginated_workflows}
            return DomainResult.success_result(result, "Workflows retrieved successfully")
        except Exception as e:
            return DomainResult.single_error(f"Failed to list workflows: {str(e)}")
