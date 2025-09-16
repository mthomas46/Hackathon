"""Health and system monitoring handlers for Orchestrator service.

Handles health check and system monitoring endpoints.
"""
from typing import Dict, Any

from services.shared.responses import create_success_response, create_error_response
from services.shared.constants_new import ErrorCodes
from services.shared.utilities import utc_now
from .shared_utils import get_orchestrator_service_client


class HealthHandlers:
    """Handles health and system monitoring operations."""

    @staticmethod
    async def handle_system_health() -> Dict[str, Any]:
        """Comprehensive system health check including all services."""
        try:
            service_client = get_orchestrator_service_client()
            system_health_data = await service_client.get_system_health()
            return create_success_response(
                "System health retrieved successfully",
                system_health_data
            )
        except Exception as e:
            return create_error_response(
                "System health check failed",
                error_code=ErrorCodes.HEALTH_CHECK_FAILED,
                details={
                    "overall_healthy": False,
                    "error": str(e),
                    "services": {},
                    "timestamp": utc_now().isoformat()
                }
            )

    @staticmethod
    async def handle_workflows_list() -> Dict[str, Any]:
        """List available workflow templates."""
        # This is a simple static response for now
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
        return create_success_response("Workflows retrieved successfully", {"workflows": workflows})

    @staticmethod
    async def handle_info() -> Dict[str, Any]:
        """Get orchestrator service information."""
        info_data = {
            "service": "orchestrator",
            "version": "1.0.0",
            "description": "Central control plane and service coordinator",
            "capabilities": ["coordination", "health_monitoring", "query_processing", "workflow_execution"],
            "routes_count": 27,  # Approximate count
            "uptime": "unknown"  # Could be enhanced with actual uptime tracking
        }
        return create_success_response("Service info retrieved successfully", info_data)

    @staticmethod
    async def handle_config_effective() -> Dict[str, Any]:
        """Get effective configuration."""
        from services.shared.config import get_config_value
        config_data = {
            "redis_enabled": True,  # Could check actual Redis status
            "peer_orchestrators": get_config_value("ORCHESTRATOR_PEERS", "", env_key="ORCHESTRATOR_PEERS").split(",") if get_config_value("ORCHESTRATOR_PEERS", "", env_key="ORCHESTRATOR_PEERS") else [],
            "service_discovery_enabled": True,
            "event_driven_enabled": True
        }
        return create_success_response("Configuration retrieved successfully", config_data)

    @staticmethod
    async def handle_metrics() -> Dict[str, Any]:
        """Get orchestrator metrics."""
        metrics_data = {
            "service": "orchestrator",
            "version": "1.0.0",
            "active_workflows": 0,  # Could be enhanced with actual workflow tracking
            "total_services": 10,  # Approximate count
            "uptime_seconds": 0,  # Could be enhanced with actual uptime tracking
            "routes_count": 27
        }
        return create_success_response("Metrics retrieved successfully", metrics_data)

    @staticmethod
    async def handle_ready() -> Dict[str, Any]:
        """Readiness check endpoint."""
        return create_success_response("Service is ready", {"status": "ready", "timestamp": utc_now().isoformat()})


# Create singleton instance
health_handlers = HealthHandlers()
