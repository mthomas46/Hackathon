"""Ecosystem Monitoring API Router.

This module provides REST API endpoints for ecosystem health monitoring,
service discovery, and cross-service analytics.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

# Initialize router
router = APIRouter(
    prefix="/ecosystem",
    tags=["ecosystem"],
    responses={
        500: {"description": "Internal server error"}
    }
)

# Pydantic models for ecosystem operations
class ServiceHealth(BaseModel):
    """Individual service health model."""

    name: str = Field(..., description="Service name")
    status: str = Field(..., enum=["healthy", "warning", "error"], description="Service health status")
    version: Optional[str] = Field(None, description="Service version")
    response_time: Optional[int] = Field(None, ge=0, description="Response time in milliseconds")
    uptime_percent: Optional[float] = Field(None, ge=0, le=100, description="Service uptime percentage")
    last_check: str = Field(..., description="Last health check timestamp")
    message: Optional[str] = Field(None, description="Status message or error details")


class EcosystemHealth(BaseModel):
    """Overall ecosystem health model."""

    overall_status: str = Field(..., enum=["healthy", "warning", "error"], description="Overall ecosystem status")
    total_services: int = Field(..., ge=0, description="Total number of services")
    healthy_services: int = Field(..., ge=0, description="Number of healthy services")
    warning_services: int = Field(..., ge=0, description="Number of services with warnings")
    error_services: int = Field(..., ge=0, description="Number of services with errors")
    services: Dict[str, ServiceHealth] = Field(..., description="Individual service health details")
    last_check: str = Field(..., description="Last ecosystem health check timestamp")
    check_duration_ms: int = Field(..., ge=0, description="Health check duration in milliseconds")


class ServiceDiscovery(BaseModel):
    """Service discovery information model."""

    name: str = Field(..., description="Service name")
    host: str = Field(..., description="Service host")
    port: int = Field(..., ge=1, le=65535, description="Service port")
    protocol: str = Field(..., enum=["http", "https", "grpc"], description="Service protocol")
    endpoints: List[str] = Field(..., description="Available service endpoints")
    capabilities: List[str] = Field(..., description="Service capabilities")
    dependencies: List[str] = Field(..., description="Service dependencies")
    discovered_at: str = Field(..., description="Service discovery timestamp")
    last_seen: str = Field(..., description="Last time service was seen")


class CrossServiceMetrics(BaseModel):
    """Cross-service analytics metrics."""

    service_interactions: Dict[str, Dict[str, int]] = Field(..., description="Service interaction counts")
    data_flow_volume: Dict[str, int] = Field(..., description="Data flow volumes between services")
    error_propagation: Dict[str, List[str]] = Field(..., description="Error propagation patterns")
    performance_correlations: Dict[str, Dict[str, float]] = Field(..., description="Performance correlations")
    bottleneck_analysis: List[Dict] = Field(..., description="Identified performance bottlenecks")


class EcosystemAlert(BaseModel):
    """Ecosystem alert model."""

    id: str = Field(..., description="Alert unique identifier")
    type: str = Field(..., enum=["error", "warning", "info"], description="Alert type")
    severity: str = Field(..., enum=["low", "medium", "high", "critical"], description="Alert severity")
    service: str = Field(..., description="Affected service")
    message: str = Field(..., description="Alert message")
    details: Optional[Dict] = Field(None, description="Additional alert details")
    created_at: str = Field(..., description="Alert creation timestamp")
    acknowledged: bool = Field(..., description="Whether alert has been acknowledged")
    resolved: bool = Field(..., description="Whether alert has been resolved")
    resolved_at: Optional[str] = Field(None, description="Alert resolution timestamp")


@router.get("/health", response_model=EcosystemHealth)
async def get_ecosystem_health():
    """Get comprehensive ecosystem health status."""
    try:
        import time
        start_time = time.time()

        # Mock ecosystem services health check
        # In production, this would check actual service endpoints
        mock_services = {
            "project-simulation": ServiceHealth(
                name="project-simulation",
                status="healthy",
                version="1.0.0",
                response_time=45,
                uptime_percent=99.8,
                last_check="2024-01-01T12:00:00Z"
            ),
            "llm-gateway": ServiceHealth(
                name="llm-gateway",
                status="healthy",
                version="1.0.0",
                response_time=120,
                uptime_percent=99.5,
                last_check="2024-01-01T12:00:00Z"
            ),
            "analysis-service": ServiceHealth(
                name="analysis-service",
                status="warning",
                version="1.0.0",
                response_time=89,
                uptime_percent=97.2,
                last_check="2024-01-01T12:00:00Z",
                message="High CPU usage detected - consider scaling"
            ),
            "log-collector": ServiceHealth(
                name="log-collector",
                status="healthy",
                version="1.0.0",
                response_time=23,
                uptime_percent=99.9,
                last_check="2024-01-01T12:00:00Z"
            ),
            "memory-agent": ServiceHealth(
                name="memory-agent",
                status="healthy",
                version="1.0.0",
                response_time=34,
                uptime_percent=99.7,
                last_check="2024-01-01T12:00:00Z"
            ),
            "prompt-store": ServiceHealth(
                name="prompt-store",
                status="healthy",
                version="1.0.0",
                response_time=67,
                uptime_percent=99.4,
                last_check="2024-01-01T12:00:00Z"
            ),
            "document-store": ServiceHealth(
                name="document-store",
                status="healthy",
                version="1.0.0",
                response_time=45,
                uptime_percent=99.6,
                last_check="2024-01-01T12:00:00Z"
            ),
            "orchestrator": ServiceHealth(
                name="orchestrator",
                status="healthy",
                version="1.0.0",
                response_time=78,
                uptime_percent=99.1,
                last_check="2024-01-01T12:00:00Z"
            ),
            "discovery-agent": ServiceHealth(
                name="discovery-agent",
                status="healthy",
                version="1.0.0",
                response_time=56,
                uptime_percent=99.3,
                last_check="2024-01-01T12:00:00Z"
            ),
            "notification-service": ServiceHealth(
                name="notification-service",
                status="error",
                version="1.0.0",
                response_time=None,
                uptime_percent=45.2,
                last_check="2024-01-01T12:00:00Z",
                message="Service is unreachable - network connectivity issue"
            ),
            "code-analyzer": ServiceHealth(
                name="code-analyzer",
                status="healthy",
                version="1.0.0",
                response_time=92,
                uptime_percent=98.7,
                last_check="2024-01-01T12:00:00Z"
            ),
            "bedrock-proxy": ServiceHealth(
                name="bedrock-proxy",
                status="healthy",
                version="1.0.0",
                response_time=134,
                uptime_percent=97.8,
                last_check="2024-01-01T12:00:00Z"
            ),
            "architecture-digitizer": ServiceHealth(
                name="architecture-digitizer",
                status="warning",
                version="1.0.0",
                response_time=156,
                uptime_percent=96.5,
                last_check="2024-01-01T12:00:00Z",
                message="High response times - performance degradation detected"
            ),
            "secure-analyzer": ServiceHealth(
                name="secure-analyzer",
                status="healthy",
                version="1.0.0",
                response_time=78,
                uptime_percent=99.2,
                last_check="2024-01-01T12:00:00Z"
            ),
            "source-agent": ServiceHealth(
                name="source-agent",
                status="healthy",
                version="1.0.0",
                response_time=89,
                uptime_percent=98.9,
                last_check="2024-01-01T12:00:00Z"
            ),
            "summarizer-hub": ServiceHealth(
                name="summarizer-hub",
                status="healthy",
                version="1.0.0",
                response_time=145,
                uptime_percent=97.4,
                last_check="2024-01-01T12:00:00Z"
            ),
            "cli": ServiceHealth(
                name="cli",
                status="healthy",
                version="1.0.0",
                response_time=23,
                uptime_percent=100.0,
                last_check="2024-01-01T12:00:00Z"
            ),
            "github-mcp": ServiceHealth(
                name="github-mcp",
                status="healthy",
                version="1.0.0",
                response_time=167,
                uptime_percent=96.8,
                last_check="2024-01-01T12:00:00Z"
            ),
            "mock-data-generator": ServiceHealth(
                name="mock-data-generator",
                status="healthy",
                version="1.0.0",
                response_time=34,
                uptime_percent=99.8,
                last_check="2024-01-01T12:00:00Z"
            ),
            "frontend": ServiceHealth(
                name="frontend",
                status="healthy",
                version="1.0.0",
                response_time=67,
                uptime_percent=99.5,
                last_check="2024-01-01T12:00:00Z"
            )
        }

        # Calculate summary statistics
        total_services = len(mock_services)
        healthy_services = sum(1 for s in mock_services.values() if s.status == "healthy")
        warning_services = sum(1 for s in mock_services.values() if s.status == "warning")
        error_services = sum(1 for s in mock_services.values() if s.status == "error")

        # Determine overall status
        if error_services > 0:
            overall_status = "error"
        elif warning_services > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        check_duration = int((time.time() - start_time) * 1000)

        return EcosystemHealth(
            overall_status=overall_status,
            total_services=total_services,
            healthy_services=healthy_services,
            warning_services=warning_services,
            error_services=error_services,
            services=mock_services,
            last_check="2024-01-01T12:00:00Z",
            check_duration_ms=check_duration
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ecosystem health: {str(e)}"
        )


@router.get("/services/{service_name}/health", response_model=ServiceHealth)
async def get_service_health(service_name: str):
    """Get health status of a specific service."""
    try:
        # Get ecosystem health and extract specific service
        ecosystem_health = await get_ecosystem_health()

        if service_name not in ecosystem_health.services:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service_name}' not found in ecosystem"
            )

        return ecosystem_health.services[service_name]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service health: {str(e)}"
        )


@router.get("/services", response_model=List[ServiceDiscovery])
async def discover_services(
    capability: Optional[str] = Query(None, description="Filter by service capability"),
    protocol: Optional[str] = Query(None, enum=["http", "https", "grpc"], description="Filter by protocol")
):
    """Discover available services in the ecosystem."""
    try:
        # Mock service discovery
        mock_services = [
            ServiceDiscovery(
                name="project-simulation",
                host="project-simulation",
                port=5075,
                protocol="http",
                endpoints=["/api/v1/simulations", "/api/v1/health", "/ws/simulations"],
                capabilities=["simulation_management", "real_time_monitoring", "websocket"],
                dependencies=["log-collector", "memory-agent"],
                discovered_at="2024-01-01T06:00:00Z",
                last_seen="2024-01-01T12:00:00Z"
            ),
            ServiceDiscovery(
                name="llm-gateway",
                host="llm-gateway",
                port=5020,
                protocol="http",
                endpoints=["/api/v1/query", "/api/v1/models", "/health"],
                capabilities=["ai_inference", "model_management", "text_generation"],
                dependencies=["log-collector"],
                discovered_at="2024-01-01T06:00:00Z",
                last_seen="2024-01-01T12:00:00Z"
            ),
            ServiceDiscovery(
                name="analysis-service",
                host="analysis-service",
                port=5080,
                protocol="http",
                endpoints=["/api/v1/analyze", "/api/v1/risk", "/health"],
                capabilities=["code_analysis", "risk_assessment", "quality_metrics"],
                dependencies=["log-collector", "document-store"],
                discovered_at="2024-01-01T06:00:00Z",
                last_seen="2024-01-01T12:00:00Z"
            ),
            ServiceDiscovery(
                name="log-collector",
                host="log-collector",
                port=5000,
                protocol="http",
                endpoints=["/api/v1/logs", "/api/v1/stats", "/health"],
                capabilities=["log_aggregation", "log_search", "metrics_collection"],
                dependencies=[],
                discovered_at="2024-01-01T06:00:00Z",
                last_seen="2024-01-01T12:00:00Z"
            ),
            ServiceDiscovery(
                name="memory-agent",
                host="memory-agent",
                port=5040,
                protocol="http",
                endpoints=["/memory/put", "/memory/list", "/health"],
                capabilities=["context_storage", "memory_management", "session_persistence"],
                dependencies=["redis"],
                discovered_at="2024-01-01T06:00:00Z",
                last_seen="2024-01-01T12:00:00Z"
            ),
            ServiceDiscovery(
                name="prompt-store",
                host="prompt-store",
                port=5110,
                protocol="http",
                endpoints=["/api/v1/prompts", "/api/v1/templates", "/health"],
                capabilities=["prompt_management", "template_library", "version_control"],
                dependencies=["log-collector", "document-store"],
                discovered_at="2024-01-01T06:00:00Z",
                last_seen="2024-01-01T12:00:00Z"
            ),
            ServiceDiscovery(
                name="document-store",
                host="document-store",
                port=5010,
                protocol="http",
                endpoints=["/api/v1/documents", "/api/v1/search", "/health"],
                capabilities=["document_storage", "search_indexing", "version_control"],
                dependencies=["log-collector"],
                discovered_at="2024-01-01T06:00:00Z",
                last_seen="2024-01-01T12:00:00Z"
            ),
            ServiceDiscovery(
                name="orchestrator",
                host="orchestrator",
                port=5050,
                protocol="http",
                endpoints=["/api/v1/workflows", "/api/v1/sagas", "/health"],
                capabilities=["workflow_orchestration", "saga_management", "event_streaming"],
                dependencies=["log-collector", "redis"],
                discovered_at="2024-01-01T06:00:00Z",
                last_seen="2024-01-01T12:00:00Z"
            ),
            ServiceDiscovery(
                name="discovery-agent",
                host="discovery-agent",
                port=5045,
                protocol="http",
                endpoints=["/api/v1/discover", "/api/v1/services", "/health"],
                capabilities=["service_discovery", "health_monitoring", "openapi_parsing"],
                dependencies=["log-collector"],
                discovered_at="2024-01-01T06:00:00Z",
                last_seen="2024-01-01T12:00:00Z"
            )
        ]

        # Apply filters
        if capability:
            mock_services = [
                service for service in mock_services
                if capability in service.capabilities
            ]

        if protocol:
            mock_services = [
                service for service in mock_services
                if service.protocol == protocol
            ]

        return mock_services

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover services: {str(e)}"
        )


@router.get("/metrics/cross-service", response_model=CrossServiceMetrics)
async def get_cross_service_metrics(
    timeframe: str = Query("1h", enum=["1h", "6h", "24h", "7d"], description="Metrics timeframe")
):
    """Get cross-service analytics and metrics."""
    try:
        # Mock cross-service metrics
        metrics = CrossServiceMetrics(
            service_interactions={
                "project-simulation": {
                    "llm-gateway": 1456,
                    "analysis-service": 892,
                    "log-collector": 2341
                },
                "llm-gateway": {
                    "log-collector": 1456,
                    "memory-agent": 567
                },
                "analysis-service": {
                    "document-store": 892,
                    "log-collector": 1203
                }
            },
            data_flow_volume={
                "project-simulation->llm-gateway": 1254300,  # tokens
                "analysis-service->document-store": 45678000,  # bytes
                "log-collector->all": 89234000  # log entries
            },
            error_propagation={
                "project-simulation": ["llm-gateway", "analysis-service"],
                "llm-gateway": ["project-simulation"],
                "analysis-service": ["document-store"]
            },
            performance_correlations={
                "response_time": {
                    "project-simulation": 0.87,
                    "llm-gateway": 0.92,
                    "analysis-service": 0.78
                },
                "error_rate": {
                    "project-simulation": -0.45,
                    "llm-gateway": -0.23,
                    "analysis-service": -0.67
                }
            },
            bottleneck_analysis=[
                {
                    "service": "llm-gateway",
                    "bottleneck_type": "rate_limiting",
                    "impact_score": 8.5,
                    "recommendation": "Increase API rate limits or implement request queuing"
                },
                {
                    "service": "analysis-service",
                    "bottleneck_type": "cpu_contention",
                    "impact_score": 6.2,
                    "recommendation": "Scale analysis service horizontally"
                }
            ]
        )

        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cross-service metrics: {str(e)}"
        )


@router.get("/alerts", response_model=List[EcosystemAlert])
async def get_ecosystem_alerts(
    status: Optional[str] = Query(None, enum=["active", "acknowledged", "resolved"], description="Filter by alert status"),
    severity: Optional[str] = Query(None, enum=["low", "medium", "high", "critical"], description="Filter by severity"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of alerts")
):
    """Get ecosystem alerts and notifications."""
    try:
        # Mock alerts
        mock_alerts = [
            EcosystemAlert(
                id=f"alert_{i:03d}",
                type=["error", "warning", "info"][i % 3],
                severity=["low", "medium", "high", "critical"][i % 4],
                service=["llm-gateway", "analysis-service", "notification-service", "document-store"][i % 4],
                message=f"Sample alert message {i}",
                details={"error_code": f"ERR_{i:03d}", "affected_components": ["api_handler", "database"]},
                created_at="2024-01-01T12:00:00Z",
                acknowledged=i % 3 != 0,  # Some acknowledged
                resolved=i % 5 == 0,     # Some resolved
                resolved_at="2024-01-01T12:30:00Z" if i % 5 == 0 else None
            )
            for i in range(min(limit, 100))
        ]

        # Apply filters
        if status:
            if status == "active":
                mock_alerts = [a for a in mock_alerts if not a.resolved]
            elif status == "acknowledged":
                mock_alerts = [a for a in mock_alerts if a.acknowledged and not a.resolved]
            elif status == "resolved":
                mock_alerts = [a for a in mock_alerts if a.resolved]

        if severity:
            mock_alerts = [a for a in mock_alerts if a.severity == severity]

        if service:
            mock_alerts = [a for a in mock_alerts if a.service == service]

        return mock_alerts

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ecosystem alerts: {str(e)}"
        )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an ecosystem alert."""
    try:
        # Mock alert acknowledgment
        return {
            "alert_id": alert_id,
            "status": "acknowledged",
            "acknowledged_at": "2024-01-01T12:00:00Z",
            "acknowledged_by": "dashboard_api"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.get("/topology", response_model=dict)
async def get_ecosystem_topology():
    """Get ecosystem service topology and dependencies."""
    try:
        # Mock service topology
        topology = {
            "services": {
                "project-simulation": {
                    "type": "core",
                    "dependencies": ["llm-gateway", "analysis-service", "log-collector"],
                    "dependents": ["frontend", "cli"]
                },
                "llm-gateway": {
                    "type": "ai",
                    "dependencies": ["log-collector"],
                    "dependents": ["project-simulation", "analysis-service", "summarizer-hub"]
                },
                "analysis-service": {
                    "type": "analysis",
                    "dependencies": ["document-store", "log-collector"],
                    "dependents": ["project-simulation", "code-analyzer"]
                },
                "log-collector": {
                    "type": "infrastructure",
                    "dependencies": [],
                    "dependents": ["all_services"]
                },
                "document-store": {
                    "type": "storage",
                    "dependencies": ["log-collector"],
                    "dependents": ["analysis-service", "prompt-store", "architecture-digitizer"]
                }
            },
            "data_flows": [
                {"from": "frontend", "to": "project-simulation", "type": "api_calls"},
                {"from": "project-simulation", "to": "llm-gateway", "type": "ai_requests"},
                {"from": "analysis-service", "to": "document-store", "type": "data_storage"},
                {"from": "all_services", "to": "log-collector", "type": "logs"}
            ],
            "generated_at": "2024-01-01T12:00:00Z"
        }

        return topology

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ecosystem topology: {str(e)}"
        )
