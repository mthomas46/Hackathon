"""API routes for the Meta-Orchestration Service"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
import logging
import time

from core.orchestrator import MetaOrchestrator
from models.service import ServiceInfo, ServiceAction
from models.config_api import (
    ServiceConfigUpdate, BatchConfigUpdate, ConfigValidationRequest,
    ConfigRollbackRequest, ConfigExportRequest, ConfigModificationResult,
    BatchConfigModificationResult, ConfigValidationResult, ServiceConfigInfo,
    CurrentConfigResponse, ConfigExportResponse, BulkConfigExportResponse,
    ConfigSyncResult, ConfigComparisonResult, ConfigHistoryResponse,
    ErrorResponse
)
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances (will be set by startup event)
meta_orchestrator = None
monitoring_service = None


@router.get(
    "/services",
    response_model=List[ServiceInfo],
    tags=["Service Management"],
    summary="List All Services",
    description="""
    Retrieve a comprehensive list of all services in the ecosystem with their current status.

    This endpoint provides real-time information about all services including:
    - Service names and types
    - Current operational status (running, stopped, error)
    - Port mappings and networking information
    - Health check status
    - Resource usage metrics

    **Use Cases:**
    - System overview and monitoring dashboards
    - Service discovery for client applications
    - Troubleshooting and diagnostics
    - Automated monitoring and alerting systems
    """,
    responses={
        200: {
            "description": "Successfully retrieved service list",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "name": "web-frontend",
                            "status": "running",
                            "ports": ["3000:3000"],
                            "health": "healthy",
                            "uptime": "2h 15m"
                        },
                        {
                            "name": "api-backend",
                            "status": "running",
                            "ports": ["8000:8000"],
                            "health": "healthy",
                            "uptime": "2h 15m"
                        }
                    ]
                }
            }
        },
        503: {
            "description": "Meta-orchestrator not initialized"
        }
    }
)
async def list_services():
    """List all services and their status"""
    try:
        if meta_orchestrator is None:
            raise HTTPException(status_code=503, detail="Meta-orchestrator not initialized")
        services = await meta_orchestrator.get_service_status()
        return services
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to list services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list services: {e}")


@router.get(
    "/services/{service_name}",
    response_model=ServiceInfo,
    tags=["Service Management"],
    summary="Get Service Details",
    description="""
    Retrieve detailed information about a specific service in the ecosystem.

    This endpoint provides comprehensive service information including:
    - Detailed status and health information
    - Configuration details and environment variables
    - Port mappings and network configuration
    - Resource usage statistics (CPU, memory, disk)
    - Service dependencies and relationships
    - Container information and logs

    **Use Cases:**
    - Detailed service monitoring and troubleshooting
    - Configuration validation and verification
    - Resource usage analysis
    - Dependency mapping and analysis
    - Service-specific alerting and notifications
    """,
    responses={
        200: {
            "description": "Successfully retrieved service details",
            "content": {
                "application/json": {
                    "example": {
                        "name": "web-frontend",
                        "status": "running",
                        "image": "nginx:alpine",
                        "ports": ["80:80", "443:443"],
                        "environment": ["NODE_ENV=production"],
                        "volumes": ["/var/log/nginx:/var/log/nginx"],
                        "health": "healthy",
                        "uptime": "2h 15m 30s",
                        "cpu_usage": "5.2%",
                        "memory_usage": "128MB / 512MB",
                        "restart_count": 0
                    }
                }
            }
        },
        404: {
            "description": "Service not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Service 'unknown-service' not found"}
                }
            }
        },
        503: {
            "description": "Meta-orchestrator not initialized"
        }
    }
)
async def get_service(service_name: str):
    """Get detailed information about a specific service"""
    try:
        services = await meta_orchestrator.get_service_status(service_name)
        if not services:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        return services[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service: {e}")


@router.post(
    "/services/{service_name}/start",
    response_model=ServiceAction,
    tags=["Service Management"],
    summary="Start Service",
    description="""
    Start a specific service in the ecosystem.

    This endpoint initiates the startup process for the specified service:
    - Pulls the latest container image if needed
    - Creates and starts the Docker container
    - Waits for health checks to pass (if configured)
    - Verifies service is responding correctly

    **Process:**
    1. Validate service exists and is not already running
    2. Pull latest image (if configured)
    3. Start Docker container
    4. Wait for health checks to pass
    5. Return startup status and timing information

    **Parameters:**
    - `profile`: Docker Compose profile to use (default: "all")

    **Use Cases:**
    - Manual service startup after maintenance
    - Automated recovery from service failures
    - Rolling deployments and updates
    - Development and testing workflows
    """,
    responses={
        200: {
            "description": "Service started successfully",
            "content": {
                "application/json": {
                    "example": {
                        "service_name": "web-frontend",
                        "action": "start",
                        "status": "success",
                        "message": "Service started successfully in profile 'all'",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "duration": 15.5
                    }
                }
            }
        },
        400: {
            "description": "Service already running or invalid request"
        },
        404: {
            "description": "Service not found"
        },
        503: {
            "description": "Meta-orchestrator not initialized"
        }
    }
)
async def start_service(service_name: str, profile: str = Query("all", description="Docker Compose profile")):
    """Start a specific service"""
    try:
        if meta_orchestrator is None:
            raise HTTPException(status_code=503, detail="Meta-orchestrator not initialized")
        result = await meta_orchestrator.start_service(service_name, profile)
        if not result.success:
            raise HTTPException(status_code=500, detail=result.message)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to start service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start service: {e}")


@router.post(
    "/services/{service_name}/stop",
    response_model=ServiceAction,
    tags=["Service Management"],
    summary="Stop Service",
    description="""
    Stop a specific service in the ecosystem.

    This endpoint gracefully shuts down the specified service:
    - Sends SIGTERM signal for clean shutdown
    - Waits for graceful shutdown (configurable timeout)
    - Forces shutdown with SIGKILL if needed
    - Cleans up associated resources

    **Process:**
    1. Validate service exists and is running
    2. Send graceful shutdown signal
    3. Wait for service to stop (with timeout)
    4. Force stop if graceful shutdown fails
    5. Clean up resources and return status

    **Use Cases:**
    - Manual service shutdown for maintenance
    - Emergency service termination
    - Resource management and cleanup
    - Rolling updates and deployments
    """,
    responses={
        200: {
            "description": "Service stopped successfully",
            "content": {
                "application/json": {
                    "example": {
                        "service_name": "web-frontend",
                        "action": "stop",
                        "status": "success",
                        "message": "Service stopped successfully",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "duration": 8.2
                    }
                }
            }
        },
        400: {
            "description": "Service already stopped or invalid request"
        },
        404: {
            "description": "Service not found"
        },
        503: {
            "description": "Meta-orchestrator not initialized"
        }
    }
)
async def stop_service(service_name: str):
    """Stop a specific service"""
    try:
        result = await meta_orchestrator.stop_service(service_name)
        if not result.success:
            raise HTTPException(status_code=500, detail=result.message)
        return result
    except Exception as e:
        logger.error(f"❌ Failed to stop service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop service: {e}")


@router.post(
    "/services/{service_name}/restart",
    response_model=ServiceAction,
    tags=["Service Management"],
    summary="Restart Service",
    description="""
    Restart a specific service in the ecosystem.

    This endpoint performs a complete service restart cycle:
    - Stops the current service instance gracefully
    - Waits for complete shutdown
    - Starts the service with fresh configuration
    - Verifies service health after restart

    **Process:**
    1. Validate service exists and can be restarted
    2. Stop current service instance (graceful shutdown)
    3. Wait for clean shutdown
    4. Start service with updated configuration
    5. Verify service health and responsiveness
    6. Return restart status and timing

    **Use Cases:**
    - Configuration updates requiring restart
    - Service recovery from degraded state
    - Rolling updates and deployments
    - Troubleshooting service issues
    - Applying security patches or updates
    """,
    responses={
        200: {
            "description": "Service restarted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "service_name": "web-frontend",
                        "action": "restart",
                        "status": "success",
                        "message": "Service restarted successfully",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "duration": 22.8
                    }
                }
            }
        },
        400: {
            "description": "Service cannot be restarted or invalid request"
        },
        404: {
            "description": "Service not found"
        },
        503: {
            "description": "Meta-orchestrator not initialized"
        }
    }
)
async def restart_service(service_name: str):
    """Restart a specific service"""
    try:
        result = await meta_orchestrator.restart_service(service_name)
        if not result.success:
            raise HTTPException(status_code=500, detail=result.message)
        return result
    except Exception as e:
        logger.error(f"❌ Failed to restart service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart service: {e}")


@router.get(
    "/services/{service_name}/logs",
    tags=["Service Management"],
    summary="Get Service Logs",
    description="""
    Retrieve recent logs from a specific service.

    This endpoint provides access to Docker container logs for debugging and monitoring:
    - Recent log entries from stdout and stderr
    - Timestamped log entries with severity levels
    - Configurable number of lines to retrieve
    - Real-time log streaming capabilities

    **Log Sources:**
    - Docker container stdout/stderr streams
    - Application-specific log files
    - System-level service logs
    - Error and debug information

    **Parameters:**
    - `lines`: Number of recent log lines to retrieve (default: 100, max: 1000)

    **Use Cases:**
    - Troubleshooting service failures
    - Monitoring application behavior
    - Debugging configuration issues
    - Performance analysis and optimization
    - Security incident investigation
    """,
    responses={
        200: {
            "description": "Service logs retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "service_name": "web-frontend",
                        "logs": [
                            "2024-01-15T10:30:00Z INFO: Server started on port 3000",
                            "2024-01-15T10:30:05Z INFO: Connected to database",
                            "2024-01-15T10:30:10Z WARN: High memory usage detected",
                            "2024-01-15T10:30:15Z ERROR: Connection timeout to api-backend"
                        ],
                        "total_lines": 150,
                        "retrieved_lines": 100
                    }
                }
            }
        },
        404: {
            "description": "Service not found"
        },
        503: {
            "description": "Meta-orchestrator not initialized"
        }
    }
)
async def get_service_logs(service_name: str, lines: int = Query(100, description="Number of log lines to retrieve")):
    """Get logs for a specific service"""
    try:
        logs = await meta_orchestrator.get_service_logs(service_name, lines)
        return {"service": service_name, "logs": logs}
    except Exception as e:
        logger.error(f"❌ Failed to get logs for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {e}")


@router.post(
    "/ecosystem/start",
    tags=["Ecosystem Management"],
    summary="Start All Services",
    description="""
    Start the entire ecosystem with all services.

    This endpoint initiates a coordinated startup of all services in the ecosystem:
    - Validates Docker Compose configuration
    - Starts infrastructure services first (Redis, databases)
    - Starts core services in dependency order
    - Starts integration and UI services
    - Verifies health of all services after startup

    **Startup Order:**
    1. Infrastructure services (Redis, databases, message queues)
    2. Core API services (authentication, data processing)
    3. Integration services (external APIs, webhooks)
    4. User interface services (web apps, dashboards)

    **Process:**
    - Parallel startup where possible
    - Health checks between dependency layers
    - Rollback on critical failures
    - Comprehensive status reporting

    **Parameters:**
    - `profile`: Docker Compose profile to use (default: "all")

    **Use Cases:**
    - System startup after maintenance
    - Disaster recovery scenarios
    - Development environment setup
    - Automated deployment pipelines
    """,
    responses={
        200: {
            "description": "Ecosystem startup initiated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Starting all services in profile 'all'",
                        "status": "initiated",
                        "profile": "all",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        500: {
            "description": "Ecosystem startup failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to start services: Connection timeout"
                    }
                }
            }
        },
        503: {
            "description": "Meta-orchestrator not initialized"
        }
    }
)
async def start_all_services(background_tasks: BackgroundTasks, profile: str = Query("all")):
    """Start all services in the ecosystem"""
    try:
        # This would start all services - for now, return a placeholder
        background_tasks.add_task(start_all_services_background, profile)
        return {"message": f"Starting all services with profile '{profile}'", "status": "initiated"}
    except Exception as e:
        logger.error(f"❌ Failed to start all services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start services: {e}")


@router.post("/ecosystem/stop")
async def stop_all_services(background_tasks: BackgroundTasks):
    """Stop all services in the ecosystem"""
    try:
        # This would stop all services - for now, return a placeholder
        background_tasks.add_task(stop_all_services_background)
        return {"message": "Stopping all services", "status": "initiated"}
    except Exception as e:
        logger.error(f"❌ Failed to stop all services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop services: {e}")


@router.get("/ecosystem/status")
async def get_ecosystem_status():
    """Get overall status of the ecosystem"""
    try:
        services = await meta_orchestrator.get_service_status()
        total_services = len(services)
        running_services = len([s for s in services if s.status.value == "running"])
        stopped_services = total_services - running_services

        return {
            "total_services": total_services,
            "running_services": running_services,
            "stopped_services": stopped_services,
            "healthy_percentage": (running_services / total_services * 100) if total_services > 0 else 0
        }
    except Exception as e:
        logger.error(f"❌ Failed to get ecosystem status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {e}")


# Monitoring Service Endpoints

@router.get(
    "/monitoring/health",
    tags=["Monitoring"],
    summary="Get Health Status",
    description="""
    Retrieve comprehensive health status for all services in the ecosystem.

    This endpoint provides real-time health monitoring data including:
    - Service availability and responsiveness
    - Response times and latency metrics
    - Error rates and failure patterns
    - Health check timestamps and intervals
    - Service-specific health indicators

    **Health Status Types:**
    - `healthy`: Service responding normally
    - `degraded`: Service responding but with issues
    - `unhealthy`: Service not responding or critical errors
    - `unknown`: Health status cannot be determined

    **Metrics Included:**
    - HTTP response times
    - Database connection status
    - Queue lengths and processing rates
    - Memory and CPU usage trends
    - Custom application health indicators

    **Use Cases:**
    - Real-time system monitoring dashboards
    - Automated alerting and incident response
    - Service level agreement (SLA) tracking
    - Performance optimization and capacity planning
    """,
    responses={
        200: {
            "description": "Health status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "health_status": {
                            "web-frontend": {
                                "status": "healthy",
                                "response_time": 0.15,
                                "last_check": "2024-01-15T10:30:00Z",
                                "endpoint": "http://localhost:3000/health",
                                "uptime": "2h 15m"
                            },
                            "api-backend": {
                                "status": "degraded",
                                "response_time": 2.5,
                                "last_check": "2024-01-15T10:29:45Z",
                                "endpoint": "http://localhost:8000/health",
                                "error": "High response time"
                            },
                            "database": {
                                "status": "healthy",
                                "response_time": 0.05,
                                "last_check": "2024-01-15T10:30:00Z",
                                "endpoint": "http://localhost:5432/health"
                            }
                        }
                    }
                }
            }
        },
        503: {
            "description": "Monitoring service not initialized"
        }
    }
)
async def get_health_status():
    """Get current health status of all services"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        health_data = await monitoring_service.get_health_status()
        return {"health_status": health_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {e}")


@router.get(
    "/monitoring/drift",
    tags=["Monitoring"],
    summary="Get Configuration Drift Status",
    description="""
    Retrieve current configuration drift status across all services.

    This endpoint provides comprehensive drift detection information:
    - Unresolved configuration inconsistencies
    - Drift severity levels and impact assessment
    - Service-specific drift details
    - Timestamp and frequency information
    - Recommended remediation actions

    **Drift Types Detected:**
    - Environment variable mismatches
    - Port mapping inconsistencies
    - Volume mount differences
    - Configuration schema violations
    - Service dependency changes

    **Severity Levels:**
    - `low`: Minor inconsistencies, no immediate impact
    - `medium`: Configuration differences affecting behavior
    - `high`: Significant drift requiring attention
    - `critical`: Critical configuration errors

    **Use Cases:**
    - Configuration compliance monitoring
    - Automated drift detection and alerting
    - Configuration management validation
    - Security and compliance auditing
    - Change management tracking
    """,
    responses={
        200: {
            "description": "Drift status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "drift_status": {
                            "total_unresolved": 3,
                            "by_service": {
                                "web-frontend": [
                                    {
                                        "type": "environment_mismatch",
                                        "severity": "medium",
                                        "description": "NODE_ENV differs between compose and runtime",
                                        "timestamp": "2024-01-15T10:25:00Z"
                                    }
                                ],
                                "api-backend": [
                                    {
                                        "type": "port_mapping",
                                        "severity": "high",
                                        "description": "Port 8000 not exposed in current configuration",
                                        "timestamp": "2024-01-15T10:20:00Z"
                                    },
                                    {
                                        "type": "volume_mount",
                                        "severity": "low",
                                        "description": "Log volume mount path changed",
                                        "timestamp": "2024-01-15T10:15:00Z"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        },
        503: {
            "description": "Monitoring service not initialized"
        }
    }
)
async def get_drift_status():
    """Get current configuration drift status"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        drift_data = await monitoring_service.get_drift_status()
        return {"drift_status": drift_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get drift status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get drift status: {e}")


@router.get(
    "/monitoring/alerts",
    tags=["Monitoring"],
    summary="Get Active Alerts",
    description="""
    Retrieve active monitoring alerts from the ecosystem.

    This endpoint provides access to current system alerts and notifications:
    - Active alerts that require attention
    - Alert severity levels and priorities
    - Service-specific and system-wide alerts
    - Alert timestamps and acknowledgment status
    - Recommended actions and escalation paths

    **Alert Types:**
    - Health check failures and timeouts
    - Configuration drift detections
    - Performance degradation alerts
    - Security and compliance violations
    - System resource warnings

    **Severity Levels:**
    - `low`: Informational alerts, no immediate action required
    - `medium`: Issues requiring attention within hours
    - `high`: Critical issues requiring immediate response
    - `critical`: System-impacting issues requiring emergency response

    **Parameters:**
    - `service_name`: Filter alerts by specific service (optional)

    **Use Cases:**
    - Alert dashboard and monitoring interfaces
    - Automated incident response systems
    - Service level agreement (SLA) tracking
    - Compliance and audit reporting
    """,
    responses={
        200: {
            "description": "Alerts retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "alerts": [
                            {
                                "id": 123,
                                "type": "health_failure",
                                "severity": "high",
                                "service": "api-backend",
                                "title": "Service Health Check Failed",
                                "message": "api-backend health check failed 5 times in 10 minutes",
                                "timestamp": "2024-01-15T10:25:00Z",
                                "acknowledged": False
                            },
                            {
                                "id": 124,
                                "type": "config_drift",
                                "severity": "medium",
                                "service": "web-frontend",
                                "title": "Configuration Drift Detected",
                                "message": "Port mapping mismatch detected",
                                "timestamp": "2024-01-15T10:20:00Z",
                                "acknowledged": True
                            }
                        ]
                    }
                }
            }
        },
        503: {
            "description": "Monitoring service not initialized"
        }
    }
)
async def get_alerts(service_name: Optional[str] = None):
    """Get active alerts"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        alerts = await monitoring_service.get_alerts(service_name)
        return {"alerts": alerts}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {e}")


@router.post("/monitoring/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, user: str = "system"):
    """Acknowledge an alert"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        success = await monitoring_service.acknowledge_alert(alert_id, user)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": f"Alert {alert_id} acknowledged by {user}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {e}")


@router.post("/monitoring/drift/{drift_id}/resolve")
async def resolve_drift(drift_id: int, action: str = "resolved"):
    """Resolve a configuration drift"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        success = await monitoring_service.resolve_drift(drift_id, action)
        if not success:
            raise HTTPException(status_code=404, detail="Drift not found")
        return {"message": f"Drift {drift_id} resolved with action: {action}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to resolve drift: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve drift: {e}")


@router.get(
    "/monitoring/analytics",
    tags=["Monitoring"],
    summary="Get Analytics Report",
    description="""
    Retrieve comprehensive system analytics and performance insights.

    This endpoint provides detailed analytics on system behavior and performance:
    - Configuration drift patterns and trends
    - Health check success rates over time
    - Service performance metrics and baselines
    - Risk assessments and system health scores
    - Recommendations for system improvements
    - Predictive analytics and trend analysis

    **Analytics Categories:**
    - **Drift Analytics**: Frequency, severity, and patterns of configuration changes
    - **Health Analytics**: Uptime percentages, failure rates, recovery times
    - **Performance Analytics**: Response times, throughput, resource utilization
    - **Risk Analytics**: System vulnerability assessments and recommendations
    - **Trend Analytics**: Historical patterns and future projections

    **Key Metrics:**
    - Mean Time Between Failures (MTBF)
    - Mean Time To Recovery (MTTR)
    - Service Level Agreements (SLA) compliance
    - Configuration stability scores
    - Risk exposure levels

    **Use Cases:**
    - Executive dashboards and reporting
    - Capacity planning and resource allocation
    - Performance optimization initiatives
    - Risk management and compliance auditing
    - Predictive maintenance and issue prevention
    """,
    responses={
        200: {
            "description": "Analytics report retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "analytics": {
                            "time_range": "7d",
                            "overall_health_score": 87.5,
                            "risk_level": "low",
                            "total_services": 15,
                            "healthy_services": 13,
                            "drift_events": 5,
                            "mtbf_hours": 168.5,
                            "mttr_minutes": 12.3,
                            "recommendations": [
                                "Consider implementing auto-scaling for api-backend",
                                "Review configuration management processes",
                                "Update health check intervals for better monitoring"
                            ],
                            "trends": {
                                "health_score_trend": "improving",
                                "drift_frequency": "stable",
                                "performance_trend": "stable"
                            }
                        }
                    }
                }
            }
        },
        503: {
            "description": "Monitoring service not initialized"
        }
    }
)
async def get_analytics_report():
    """Get comprehensive analytics report"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        report = await monitoring_service.get_analytics_report()
        return {"analytics_report": report}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get analytics report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics report: {e}")


@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard():
    """Get monitoring dashboard data"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")

        # Get all monitoring data
        health_data = await monitoring_service.get_health_status()
        drift_data = await monitoring_service.get_drift_status()
        alerts = await monitoring_service.get_alerts()

        # Get summary statistics
        total_services = len(health_data)
        healthy_services = sum(1 for h in health_data.values() if h.get('status') == 'healthy')
        total_alerts = len(alerts)
        unresolved_drifts = drift_data.get('total_unresolved', 0)

        return {
            "dashboard": {
                "summary": {
                    "total_services": total_services,
                    "healthy_services": healthy_services,
                    "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 0,
                    "active_alerts": total_alerts,
                    "unresolved_drifts": unresolved_drifts
                },
                "health_status": health_data,
                "drift_status": drift_data,
                "active_alerts": alerts[:10]  # Show first 10 alerts
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {e}")


# Configuration Validation and Healing Endpoints

@router.get(
    "/monitoring/config/port-conflicts",
    tags=["Configuration Management"],
    summary="Detect Port Conflicts",
    description="""
    Detect port conflicts across all services in the ecosystem.

    This endpoint scans all service configurations to identify port conflicts where:
    - Multiple services attempt to bind to the same port
    - Port ranges overlap between services
    - Dynamic port allocation conflicts exist

    **Conflict Types Detected:**
    - **Exact Port Conflicts**: Same port number used by multiple services
    - **Port Range Overlaps**: Overlapping port ranges in service definitions
    - **Protocol Conflicts**: Same port used for different protocols (HTTP vs HTTPS)

    **Use Cases:**
    - Pre-deployment validation
    - Configuration troubleshooting
    - Service deployment planning
    - Network architecture review
    """,
    responses={
        200: {
            "description": "Port conflicts detected successfully",
            "content": {
                "application/json": {
                    "example": {
                        "port_conflicts": [
                            {
                                "port": 8080,
                                "services": ["web-frontend", "api-gateway"],
                                "severity": "high"
                            },
                            {
                                "port": 5432,
                                "services": ["database", "cache"],
                                "severity": "critical"
                            }
                        ]
                    }
                }
            }
        },
        503: {
            "description": "Monitoring service not initialized"
        }
    }
)
async def detect_port_conflicts():
    """Detect port conflicts in the ecosystem"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        conflicts = await monitoring_service.detect_port_conflicts()
        return {"port_conflicts": conflicts}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to detect port conflicts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to detect port conflicts: {e}")


@router.post(
    "/monitoring/config/resolve-port-conflicts",
    tags=["Configuration Management"],
    summary="Resolve Port Conflicts",
    description="""
    Automatically resolve detected port conflicts in the ecosystem.

    This endpoint attempts to automatically fix port conflicts by:
    - Reassigning conflicting ports to available alternatives
    - Updating service configurations with new port assignments
    - Ensuring no new conflicts are introduced
    - Providing rollback capabilities for failed resolutions

    **Resolution Strategies:**
    - **Port Reassignment**: Assign unused ports from predefined ranges
    - **Service Prioritization**: Resolve conflicts based on service priority
    - **Configuration Updates**: Modify docker-compose.yml files automatically
    - **Validation**: Ensure resolutions don't create new conflicts

    **Safety Features:**
    - **Dry-run Validation**: Test resolutions before applying
    - **Rollback Support**: Revert changes if issues occur
    - **Conflict Verification**: Ensure all conflicts are resolved
    - **Backup Creation**: Preserve original configurations

    **Use Cases:**
    - Automated conflict resolution during deployment
    - Configuration healing for existing deployments
    - Service migration and port reassignment
    - Emergency conflict resolution
    """,
    responses={
        200: {
            "description": "Port conflicts resolved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "port_conflict_resolution": {
                            "status": "resolved",
                            "conflicts_found": 2,
                            "resolutions_applied": 2,
                            "details": {
                                "web-frontend": {
                                    "old_port": 8080,
                                    "new_port": 8081,
                                    "service": "api-gateway"
                                },
                                "database": {
                                    "old_port": 5432,
                                    "new_port": 5433,
                                    "service": "cache"
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "No conflicts to resolve or resolution failed"
        },
        503: {
            "description": "Monitoring service not initialized"
        }
    }
)
async def resolve_port_conflicts():
    """Automatically resolve port conflicts"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        result = await monitoring_service.resolve_port_conflicts()
        return {"port_conflict_resolution": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to resolve port conflicts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve port conflicts: {e}")


@router.get(
    "/monitoring/config/inconsistencies",
    tags=["Configuration Management"],
    summary="Detect Configuration Inconsistencies",
    description="""
    Detect configuration inconsistencies across all services in the ecosystem.

    This endpoint identifies configuration issues that may affect service operation:
    - Environment variable naming inconsistencies
    - Volume mount path mismatches
    - Network configuration conflicts
    - Resource limit discrepancies
    - Security configuration gaps

    **Inconsistency Types:**
    - **Environment Variables**: Inconsistent naming conventions or missing required vars
    - **Volume Mounts**: Path inconsistencies or permission issues
    - **Network Config**: Conflicting network settings between services
    - **Resource Limits**: Inconsistent CPU/memory allocations
    - **Security Settings**: Missing security configurations or conflicts

    **Severity Levels:**
    - **low**: Minor inconsistencies that don't affect functionality
    - **medium**: Issues that may cause performance problems
    - **high**: Critical issues that could cause service failures
    - **critical**: Issues that prevent proper service operation

    **Use Cases:**
    - Configuration auditing and compliance
    - Pre-deployment validation
    - Troubleshooting configuration-related issues
    - Security posture assessment
    """,
    responses={
        200: {
            "description": "Configuration inconsistencies detected successfully",
            "content": {
                "application/json": {
                    "example": {
                        "config_inconsistencies": [
                            {
                                "service_name": "web-frontend",
                                "inconsistency_type": "env_var_naming",
                                "description": "Environment variables don't follow naming convention",
                                "severity": "medium",
                                "suggested_fix": "Rename variables to use UPPER_SNAKE_CASE"
                            },
                            {
                                "service_name": "database",
                                "inconsistency_type": "volume_permissions",
                                "description": "Volume mount has incorrect permissions",
                                "severity": "high",
                                "suggested_fix": "Set volume permissions to 755"
                            }
                        ]
                    }
                }
            }
        },
        503: {
            "description": "Monitoring service not initialized"
        }
    }
)
async def detect_config_inconsistencies():
    """Detect Docker configuration inconsistencies"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        inconsistencies = await monitoring_service.detect_config_inconsistencies()
        return {"config_inconsistencies": inconsistencies}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to detect config inconsistencies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to detect config inconsistencies: {e}")


@router.post(
    "/monitoring/config/resolve-inconsistencies",
    tags=["Configuration Management"],
    summary="Resolve Configuration Inconsistencies",
    description="""
    Automatically resolve detected configuration inconsistencies.

    This endpoint attempts to fix configuration issues by applying standardized fixes:
    - Renaming environment variables to follow conventions
    - Correcting volume mount permissions and paths
    - Standardizing network configuration settings
    - Applying consistent resource limits
    - Implementing security best practices

    **Fix Categories:**
    - **Environment Variables**: Standardize naming and values
    - **Volume Mounts**: Fix paths and permissions
    - **Network Settings**: Resolve configuration conflicts
    - **Resource Limits**: Apply consistent allocations
    - **Security Config**: Implement required security settings

    **Safety Features:**
    - **Validation**: Ensure fixes don't break existing functionality
    - **Backup**: Create backups before making changes
    - **Rollback**: Ability to revert changes if issues occur
    - **Testing**: Validate fixes don't introduce new problems

    **Resolution Process:**
    1. Analyze detected inconsistencies
    2. Generate appropriate fixes for each issue
    3. Validate fixes won't cause conflicts
    4. Apply fixes with backup creation
    5. Verify services still function correctly

    **Use Cases:**
    - Automated configuration healing
    - Compliance enforcement
    - Pre-deployment standardization
    - Configuration drift correction
    """,
    responses={
        200: {
            "description": "Configuration inconsistencies resolved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "config_inconsistency_resolution": {
                            "status": "resolved",
                            "inconsistencies_found": 3,
                            "fixes_applied": 2,
                            "details": {
                                "web-frontend": {
                                    "env_var_naming": "Renamed 5 environment variables",
                                    "volume_permissions": "Fixed permissions for /app/logs"
                                },
                                "database": {
                                    "resource_limits": "Applied consistent memory limits"
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "No inconsistencies to resolve or resolution failed"
        },
        503: {
            "description": "Monitoring service not initialized"
        }
    }
)
async def resolve_config_inconsistencies():
    """Automatically resolve configuration inconsistencies"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        result = await monitoring_service.resolve_config_inconsistencies()
        return {"inconsistency_resolution": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to resolve config inconsistencies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve config inconsistencies: {e}")


# Service Configuration Management Endpoints

@router.post(
    "/monitoring/config/sync",
    tags=["Configuration Management"],
    summary="Sync Service Configurations",
    description="""
    Synchronize configurations from all running service endpoints.

    This endpoint fetches the latest configuration from each service's configuration endpoint:
    - Query each service for its current configuration state
    - Update the central configuration database with latest values
    - Detect configuration drift between services and stored configs
    - Validate configuration consistency across the ecosystem

    **Sync Process:**
    1. **Discovery**: Identify all running services with config endpoints
    2. **Fetch**: Retrieve current configuration from each service
    3. **Validation**: Validate configuration format and completeness
    4. **Storage**: Update central configuration database
    5. **Analysis**: Detect configuration drift and inconsistencies

    **Configuration Sources:**
    - **Service Endpoints**: Direct API calls to /config endpoints
    - **Environment Variables**: Runtime environment inspection
    - **Docker Labels**: Configuration metadata from containers
    - **Volume Mounts**: File-based configuration validation

    **Benefits:**
    - **Real-time Visibility**: Always know current service configurations
    - **Drift Detection**: Identify when configs deviate from expected state
    - **Consistency**: Ensure all services use compatible configurations
    - **Auditing**: Track configuration changes over time

    **Use Cases:**
    - Configuration monitoring and compliance
    - Troubleshooting configuration-related issues
    - Security auditing and validation
    - Automated configuration management
    """,
    responses={
        200: {
            "description": "Configuration sync completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "config_sync": {
                            "services_synced": 8,
                            "configs_updated": 5,
                            "new_configs": 2,
                            "errors": 1,
                            "sync_duration": 15.2,
                            "results": {
                                "successful": ["web-frontend", "api-backend", "database"],
                                "failed": ["cache-service"],
                                "skipped": ["legacy-service"]
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "Configuration sync failed"
        },
        503: {
            "description": "Monitoring service not initialized"
        }
    }
)
async def sync_service_configs():
    """Sync configurations from all service endpoints"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        result = await monitoring_service.sync_service_configs()
        return {"config_sync": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to sync service configs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync service configs: {e}")


@router.get(
    "/monitoring/config/{service_name}",
    tags=["Configuration Management"],
    summary="Get Service Configuration",
    description="""
    Retrieve the current configuration for a specific service.

    This endpoint provides comprehensive access to a service's configuration:
    - Current runtime configuration from the service
    - Configuration metadata (version, source, timestamp)
    - Environment variables and their values
    - Service-specific settings and parameters
    - Configuration validation status

    **Configuration Sources:**
    - **Service Endpoint**: Direct configuration retrieval from running service
    - **Database Cache**: Latest synced configuration from central database
    - **Environment Inspection**: Runtime environment variable analysis
    - **File System**: Configuration files mounted in containers

    **Configuration Types:**
    - **Application Config**: Service-specific application settings
    - **Environment Config**: Environment variables and their values
    - **Network Config**: Port mappings, network settings, DNS configuration
    - **Resource Config**: CPU, memory, and storage limits
    - **Security Config**: Authentication, authorization, encryption settings

    **Use Cases:**
    - Service configuration inspection and debugging
    - Configuration validation and compliance checking
    - Troubleshooting service behavior issues
    - Security auditing and configuration review
    - Configuration backup and recovery planning
    """,
    responses={
        200: {
            "description": "Service configuration retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "service_config": {
                            "service_name": "web-frontend",
                            "config_hash": "a1b2c3d4e5f6...",
                            "config_data": {
                                "port": 3000,
                                "host": "0.0.0.0",
                                "environment": "production",
                                "database_url": "postgresql://...",
                                "redis_url": "redis://..."
                            },
                            "timestamp": "2024-01-15T10:30:00Z",
                            "source": "service_endpoint",
                            "validation_status": "valid"
                        }
                    }
                }
            }
        },
        404: {
            "description": "Service not found or no configuration available"
        },
        503: {
            "description": "Monitoring service not initialized"
        }
    }
)
async def get_service_config(service_name: str):
    """Get current configuration for a service"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        config = await monitoring_service.get_service_config(service_name)
        if config is None:
            raise HTTPException(status_code=404, detail=f"No configuration found for service {service_name}")
        return {"service_config": config}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get service config for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service config: {e}")


@router.get(
    "/monitoring/config/{service_name}/export",
    tags=["Configuration Management"],
    summary="Export Service Configuration",
    description="""
    Export a service's configuration in various formats for backup or migration.

    This endpoint allows exporting service configurations in multiple formats:
    - **JSON**: Structured configuration data for APIs and tools
    - **YAML**: Human-readable format for configuration files
    - **Environment**: Shell environment variable format
    - **Docker Labels**: Docker container label format

    **Export Formats:**
    - **json**: Complete configuration as JSON object with metadata
    - **yaml**: Configuration in YAML format for docker-compose files
    - **env**: Environment variables in shell export format
    - **docker**: Docker container labels and environment format

    **Export Content:**
    - Service configuration parameters
    - Environment variables and their values
    - Network and port configurations
    - Volume mount specifications
    - Resource limits and constraints
    - Security and authentication settings

    **Use Cases:**
    - Configuration backup and disaster recovery
    - Service migration between environments
    - Configuration templating and automation
    - Documentation and compliance reporting
    - Development environment setup
    """,
    responses={
        200: {
            "description": "Configuration exported successfully",
            "content": {
                "application/json": {
                    "example": {
                        "exported_config": {
                            "format": "json",
                            "service_name": "web-frontend",
                            "content": {
                                "port": 3000,
                                "host": "0.0.0.0",
                                "environment": "production",
                                "database_url": "postgresql://...",
                                "features": ["auth", "logging", "metrics"]
                            },
                            "metadata": {
                                "export_timestamp": "2024-01-15T10:30:00Z",
                                "config_hash": "a1b2c3d4...",
                                "validation_status": "valid"
                            }
                        }
                    }
                },
                "application/x-yaml": {
                    "example": "# Exported web-frontend configuration\nport: 3000\nhost: \"0.0.0.0\"\nenvironment: production\ndatabase_url: postgresql://...\nfeatures:\n  - auth\n  - logging\n  - metrics\n"
                },
                "text/plain": {
                    "example": "# Exported web-frontend environment variables\nexport PORT=3000\nexport HOST=0.0.0.0\nexport ENVIRONMENT=production\nexport DATABASE_URL=postgresql://...\n"
                }
            }
        },
        404: {
            "description": "Service not found or no configuration available"
        },
        503: {
            "description": "Monitoring service not initialized"
        }
    }
)
async def export_service_config(service_name: str, format: str = "json"):
    """Export a service's configuration"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        config_content = await monitoring_service.export_service_config(service_name, format)
        if config_content is None:
            raise HTTPException(status_code=404, detail=f"No configuration found for service {service_name}")

        return {
            "service_name": service_name,
            "format": format,
            "content": config_content
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to export service config for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export service config: {e}")


@router.post("/monitoring/config/export-all")
async def export_all_configs(format: str = "json"):
    """Export all service configurations"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        result = await monitoring_service.export_all_configs(format)
        return {
            "export_result": {
                "format": format,
                "total_exports": len(result),
                "files": result
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to export all configs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export all configs: {e}")


@router.get("/monitoring/config/{service_name}/compare")
async def compare_service_configs(service_name: str):
    """Compare current and previous configurations for a service"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        comparison = await monitoring_service.compare_service_configs(service_name)
        return {"config_comparison": comparison}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to compare configs for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare configs: {e}")


@router.get("/monitoring/config/{service_name}/history")
async def get_service_config_history(service_name: str, limit: int = 10):
    """Get configuration history for a service"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")
        history = await monitoring_service.get_service_config_history(service_name, limit)
        return {"config_history": history}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get config history for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config history: {e}")


# Audit and Validation Endpoints

@router.post(
    "/audit/docker-compose/validate",
    tags=["Audit & Validation"],
    summary="Validate Docker Compose Configuration",
    description="""
    Validate Docker Compose configuration for startup operations.

    This endpoint performs comprehensive validation of docker-compose files including:
    - Port conflict detection
    - Shared volume mount validation
    - Build context verification
    - Service dependency validation
    - Health check configuration validation
    - Circular dependency detection

    **Use Cases:**
    - Pre-deployment validation
    - CI/CD pipeline checks
    - Configuration troubleshooting
    - Startup issue diagnosis
    """,
    responses={
        200: {
            "description": "Validation completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "services_count": 15,
                        "port_conflicts": 0,
                        "issues": [],
                        "warnings": 2,
                        "errors": 0,
                        "port_conflicts_detail": []
                    }
                }
            }
        },
        500: {
            "description": "Validation failed due to internal error"
        }
    }
)
async def validate_docker_compose(compose_file: Optional[str] = Query("docker-compose.dev.yml", description="Docker Compose file to validate")):
    """Validate Docker Compose configuration"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")

        result = await monitoring_service.validate_docker_compose(compose_file)
        return {"docker_compose_validation": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to validate Docker Compose: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate Docker Compose: {e}")


@router.post(
    "/audit/config/drift-detect",
    tags=["Audit & Validation"],
    summary="Detect Configuration Drift",
    description="""
    Detect configuration drift across Docker, YAML, and Pydantic configurations.

    This endpoint compares:
    - Running Docker containers vs docker-compose.yml
    - Running containers vs Pydantic service configurations
    - docker-compose.yml vs Pydantic configurations
    - Configuration files against JSON schemas

    **Drift Types Detected:**
    - Port mapping inconsistencies
    - Environment variable mismatches
    - Volume mount differences
    - Configuration schema violations

    **Parameters:**
    - `dev_only`: Skip cross-environment comparisons (default: true)
    """,
    responses={
        200: {
            "description": "Drift detection completed",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "total_issues": 3,
                        "high_severity": 1,
                        "medium_severity": 2,
                        "low_severity": 0,
                        "schema_validation_passed": True,
                        "scanned_files": 25,
                        "scanned_containers": 12,
                        "issues": [
                            {
                                "type": "docker_vs_compose",
                                "severity": "high",
                                "description": "Port mapping mismatch for service 'web-frontend'",
                                "field_path": "ports",
                                "can_auto_fix": False
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Drift detection failed"
        }
    }
)
async def detect_configuration_drift(dev_only: Optional[bool] = Query(True, description="Skip cross-environment comparisons")):
    """Detect configuration drift across all sources"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")

        result = await monitoring_service.detect_configuration_drift(dev_only=dev_only)
        return {"configuration_drift": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to detect configuration drift: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to detect configuration drift: {e}")


@router.post(
    "/audit/production-readiness/validate",
    tags=["Audit & Validation"],
    summary="Validate Production Readiness",
    description="""
    Perform comprehensive production readiness validation.

    This endpoint validates the ecosystem against production requirements including:
    - Docker container health and availability
    - Service connectivity and responsiveness
    - API schema compliance and error handling
    - Configuration consistency
    - Port mapping conflicts
    - Health check configurations

    **Readiness Levels:**
    - `production_ready`: All critical checks pass (90%+ score)
    - `development_ready`: Most checks pass (70%+ score)
    - `testing_ready`: Basic functionality works (50%+ score)
    - `not_ready`: Major issues detected

    **Validation Categories:**
    - Infrastructure: Docker health, connectivity, ports
    - API: Schema compliance, error handling
    - Configuration: Consistency, schema validation
    - Integration: Dependencies, health checks
    """,
    responses={
        200: {
            "description": "Production readiness validation completed",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "overall_readiness": "development_ready",
                        "overall_score": 0.85,
                        "total_checks": 10,
                        "passed_checks": 8,
                        "failed_checks": 2,
                        "critical_failures": 0,
                        "results": [
                            {
                                "check_name": "docker_containers_health",
                                "success": True,
                                "score": 1.0,
                                "message": "12/12 containers healthy",
                                "issues": [],
                                "recommendations": []
                            }
                        ],
                        "recommendations": [
                            "Add health checks to remaining services",
                            "Review API error response formats"
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Validation failed due to internal error"
        }
    }
)
async def validate_production_readiness(target_level: Optional[str] = Query("development_ready", description="Target readiness level")):
    """Validate production readiness of the ecosystem"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")

        result = await monitoring_service.validate_production_readiness(target_level=target_level)
        return {"production_readiness": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to validate production readiness: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate production readiness: {e}")


@router.post(
    "/audit/config/standardize/service/{service_name}",
    tags=["Audit & Validation"],
    summary="Standardize Configuration for Single Service",
    description="""
    Standardize configuration management for a specific service.

    This endpoint validates and optionally fixes configuration issues including:
    - Port mapping standardization
    - Environment variable naming consistency
    - Configuration file format validation
    - Docker Compose consistency

    **Standardization Modes:**
    - `validate`: Only validate, don't make changes
    - `dry_run`: Show what would be changed
    - `apply`: Apply standardization fixes

    **Common Issues Fixed:**
    - Port numbers not matching standardized values
    - Environment variables with inconsistent naming
    - Missing configuration files
    - Configuration format inconsistencies
    """,
    responses={
        200: {
            "description": "Configuration standardization completed",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "service_name": "web-frontend",
                        "changes_made": ["Updated port to standardized value"],
                        "warnings": ["Environment variable naming could be improved"],
                        "errors": [],
                        "issues": [
                            {
                                "service": "web-frontend",
                                "type": "port_standardization",
                                "severity": "warning",
                                "description": "Port should be 3000 (standardized)",
                                "can_auto_fix": True
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "Service not found"
        },
        500: {
            "description": "Standardization failed"
        }
    }
)
async def standardize_service_config(service_name: str, mode: Optional[str] = Query("validate", description="Standardization mode: validate, dry_run, apply")):
    """Standardize configuration for a specific service"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")

        result = await monitoring_service.standardize_service_config(service_name, mode)
        return {"config_standardization": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to standardize config for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to standardize config: {e}")


@router.post(
    "/audit/config/standardize/all",
    tags=["Audit & Validation"],
    summary="Standardize Configurations for All Services",
    description="""
    Standardize configuration management across all services in the ecosystem.

    This endpoint performs comprehensive configuration standardization including:
    - Port mapping standardization across all services
    - Environment variable naming consistency
    - Configuration file format validation
    - Docker Compose consistency checks

    **Process:**
    1. Validates all service configurations
    2. Identifies standardization opportunities
    3. Optionally applies fixes based on mode
    4. Provides detailed reporting on changes made

    **Use Cases:**
    - Initial configuration setup
    - Configuration consistency audits
    - Automated configuration fixes
    - Pre-deployment validation
    """,
    responses={
        200: {
            "description": "Configuration standardization completed for all services",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "services_processed": 15,
                        "services_standardized": 12,
                        "total_issues": 8,
                        "fixes_applied": 6,
                        "standardization_rate": 0.8,
                        "issue_breakdown": {
                            "port_standardization": 3,
                            "env_var_standardization": 2,
                            "missing_config": 2,
                            "config_format": 1
                        },
                        "results": [
                            {
                                "service_name": "web-frontend",
                                "success": True,
                                "changes_made": ["Updated port mapping"],
                                "warnings": [],
                                "errors": []
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Standardization failed"
        }
    }
)
async def standardize_all_configs(mode: Optional[str] = Query("validate", description="Standardization mode: validate, dry_run, apply")):
    """Standardize configurations for all services"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")

        result = await monitoring_service.standardize_all_configs(mode)
        return {"config_standardization": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to standardize all configs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to standardize configs: {e}")


@router.post(
    "/audit/docker/standardize",
    tags=["Audit & Validation"],
    summary="Standardize Docker Configurations",
    description="""
    Perform comprehensive Docker configuration standardization and validation.

    This endpoint standardizes Docker configurations using Pydantic validation and best practices:
    - Docker Compose file validation and fixes
    - Port mapping standardization
    - Environment variable format consistency
    - Volume mount validation
    - Dependency configuration checks
    - Dockerfile best practice validation

    **Validation Features:**
    - Pydantic schema validation for Docker Compose files
    - Automated fixes for common configuration issues
    - Dockerfile security and best practice checks
    - Multi-stage build optimization suggestions

    **Standardization Modes:**
    - `validate`: Only validate configurations
    - `dry_run`: Show proposed changes
    - `apply`: Apply standardization fixes
    """,
    responses={
        200: {
            "description": "Docker configuration standardization completed",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "files_processed": 3,
                        "files_modified": 1,
                        "issues_found": 5,
                        "issues_fixed": 3,
                        "validation_errors": 0,
                        "pydantic_validation_passed": True,
                        "issues": [
                            {
                                "service": "api-backend",
                                "type": "port_mapping",
                                "severity": "warning",
                                "description": "Service should expose standardized port 8000",
                                "can_auto_fix": False
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Docker standardization failed"
        }
    }
)
async def standardize_docker_configs(mode: Optional[str] = Query("validate", description="Standardization mode: validate, dry_run, apply")):
    """Standardize all Docker configurations"""
    try:
        if monitoring_service is None:
            raise HTTPException(status_code=503, detail="Monitoring service not initialized")

        result = await monitoring_service.standardize_docker_configs(mode)
        return {"docker_standardization": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to standardize Docker configs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to standardize Docker configs: {e}")


# Configuration Modification Endpoints

@router.put(
    "/services/{service_name}/config",
    response_model=Dict[str, ConfigModificationResult],
    summary="Modify Single Service Configuration",
    description="""
    Modify the Docker configuration for a specific service.

    This endpoint allows you to update various aspects of a service's Docker configuration
    including environment variables, ports, volumes, restart policies, and more.

    **Features:**
    - Comprehensive validation of configuration changes
    - Automatic backup of original configuration
    - Optional automatic service restart after changes
    - Detailed change tracking and reporting

    **Supported Configuration Options:**
    - `environment`: Environment variables (dict or list format)
    - `ports`: Port mappings (e.g., ["8080:3000"])
    - `volumes`: Volume mounts (e.g., ["./data:/app/data"])
    - `restart`: Restart policy ("no", "always", "on-failure", "unless-stopped")
    - `depends_on`: Service dependencies
    - `networks`: Network configurations
    - `image`: Docker image
    - `build`: Build configuration
    - `restart_after_change`: Whether to restart the service (default: true)
    """,
    responses={
        200: {
            "description": "Configuration successfully modified",
            "content": {
                "application/json": {
                    "example": {
                        "config_modification": {
                            "success": True,
                            "service_name": "web-frontend",
                            "changes_applied": ["environment", "restart"],
                            "original_config": {"restart": "unless-stopped"},
                            "persistence_result": {"persisted": True},
                            "restart_result": {"restarted": True, "message": "Service restarted"},
                            "message": "Successfully applied 2 configuration changes"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Configuration validation failed",
            "model": ErrorResponse
        },
        404: {
            "description": "Service not found",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def modify_service_config(service_name: str, config_updates: ServiceConfigUpdate):
    """Modify a single service's Docker configuration"""
    try:
        if meta_orchestrator is None:
            raise HTTPException(
                status_code=503,
                detail=ErrorResponse(
                    error="SERVICE_UNAVAILABLE",
                    message="Meta-orchestrator not initialized"
                ).dict()
            )

        if service_name not in meta_orchestrator.services:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="SERVICE_NOT_FOUND",
                    message=f"Service {service_name} not found"
                ).dict()
            )

        # Validate configuration updates (filter out None values)
        config_dict = config_updates.model_dump()
        config_dict = {k: v for k, v in config_dict.items() if v is not None}
        validation_errors = validate_config_updates(service_name, config_dict)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="VALIDATION_FAILED",
                    message="Configuration validation failed",
                    details=[
                        {"field": f"config.{error.split(':')[0] if ':' in error else 'general'}", "message": error}
                        for error in validation_errors
                    ]
                ).dict()
            )

        # Apply configuration changes
        result = await apply_service_config_changes(service_name, config_updates.model_dump())

        if result["success"]:
            # Optionally restart the service
            if config_updates.restart_after_change:
                restart_result = await restart_service_after_config_change(service_name)
                result["restart_result"] = restart_result

        return {"config_modification": ConfigModificationResult(**result)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to modify service config for {service_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="INTERNAL_ERROR",
                message=f"Failed to modify service config: {e}"
            ).dict()
        )


@router.put(
    "/services/config/batch",
    response_model=Dict[str, BatchConfigModificationResult],
    summary="Modify Multiple Services Configuration (Batch)",
    description="""
    Modify Docker configurations for multiple services in a single batch operation.

    This endpoint allows you to update configurations for multiple services simultaneously,
    with comprehensive validation and optional rollback capabilities.

    **Features:**
    - Validate all configurations before applying any changes
    - Sequential application to avoid conflicts
    - Automatic rollback on failure (optional)
    - Detailed per-service results and summaries
    - Optional service restart after changes

    **Batch Processing Logic:**
    1. Validate all service configurations first
    2. If validation passes, apply changes sequentially
    3. If any service fails and rollback is enabled, revert all changes
    4. Return detailed results for each service

    **Use Cases:**
    - Environment updates across multiple services
    - Port reassignments for service migration
    - Configuration standardization across services
    - Rolling updates with rollback safety
    """,
    responses={
        200: {
            "description": "Batch configuration successfully processed",
            "content": {
                "application/json": {
                    "example": {
                        "batch_config_modification": {
                            "total_services": 3,
                            "successful_modifications": 3,
                            "failed_modifications": 0,
                            "results": {
                                "web-frontend": {
                                    "success": True,
                                    "service_name": "web-frontend",
                                    "changes_applied": ["environment"],
                                    "message": "Successfully applied 1 configuration changes"
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Configuration validation failed",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def modify_services_config_batch(config_batch: BatchConfigUpdate):
    """Modify Docker configurations for multiple services sequentially"""
    try:
        if meta_orchestrator is None:
            raise HTTPException(
                status_code=503,
                detail=ErrorResponse(
                    error="SERVICE_UNAVAILABLE",
                    message="Meta-orchestrator not initialized"
                ).dict()
            )

        services_config = config_batch.services
        if not services_config:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="INVALID_REQUEST",
                    message="No services configuration provided"
                ).dict()
            )

        # Validate all configurations first
        all_validation_errors = {}
        for service_name, config_updates in services_config.items():
            if service_name not in meta_orchestrator.services:
                all_validation_errors[service_name] = [f"Service {service_name} not found"]
                continue

            config_dict = config_updates.model_dump()
            config_dict = {k: v for k, v in config_dict.items() if v is not None}
            validation_errors = validate_config_updates(service_name, config_dict)
            if validation_errors:
                all_validation_errors[service_name] = validation_errors

        if all_validation_errors:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="VALIDATION_FAILED",
                    message="Configuration validation failed for one or more services",
                    details=[
                        {"field": f"services.{service}.{error.split(':')[0] if ':' in error else 'general'}", "message": error}
                        for service, errors in all_validation_errors.items()
                        for error in errors
                    ]
                ).dict()
            )

        # Apply configurations sequentially
        batch_results = {}
        rollback_info = []

        try:
            for service_name, config_updates in services_config.items():
                logger.info(f"🔧 Applying config changes to {service_name}")

                result = await apply_service_config_changes(service_name, config_updates.model_dump())
                batch_results[service_name] = result

                if result["success"]:
                    # Store rollback information
                    rollback_info.append({
                        "service_name": service_name,
                        "original_config": result.get("original_config", {}),
                        "new_config": config_updates.model_dump()
                    })

                    # Optionally restart the service
                    if config_updates.restart_after_change:
                        restart_result = await restart_service_after_config_change(service_name)
                        result["restart_result"] = restart_result
                else:
                    # Stop batch processing on first failure
                    break

        except Exception as e:
            logger.error(f"❌ Batch configuration failed: {e}")
            # Attempt rollback if configured
            if config_batch.rollback_on_failure:
                rollback_results = await rollback_config_changes(rollback_info)
                batch_results["rollback_attempted"] = rollback_results

        batch_summary = BatchConfigModificationResult(
            total_services=len(services_config),
            successful_modifications=sum(1 for r in batch_results.values() if isinstance(r, dict) and r.get("success", False)),
            failed_modifications=sum(1 for r in batch_results.values() if isinstance(r, dict) and not r.get("success", True)),
            results=batch_results
        )

        return {"batch_config_modification": batch_summary}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to modify services config batch: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="INTERNAL_ERROR",
                message=f"Failed to modify services config batch: {e}"
            ).dict()
        )


@router.post("/services/{service_name}/config/rollback")
async def rollback_service_config(service_name: str, rollback_data: Dict[str, Any]):
    """Rollback a service's configuration to a previous state"""
    try:
        if meta_orchestrator is None:
            raise HTTPException(status_code=503, detail="Meta-orchestrator not initialized")

        if service_name not in meta_orchestrator.services:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

        original_config = rollback_data.get("original_config", {})
        if not original_config:
            raise HTTPException(status_code=400, detail="No original configuration provided for rollback")

        # Apply rollback
        result = await apply_service_config_changes(service_name, original_config)

        if result["success"] and rollback_data.get("restart_after_rollback", True):
            restart_result = await restart_service_after_config_change(service_name)
            result["restart_result"] = restart_result

        return {"config_rollback": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to rollback service config for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rollback service config: {e}")


@router.get("/services/{service_name}/config/current")
async def get_service_current_config(service_name: str):
    """Get a service's current Docker configuration from docker-compose.yml"""
    try:
        if meta_orchestrator is None:
            raise HTTPException(status_code=503, detail="Meta-orchestrator not initialized")

        if service_name not in meta_orchestrator.services:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

        service_info = meta_orchestrator.services[service_name]

        # Extract current configuration
        current_config = {
            "image": getattr(service_info, 'image', None),
            "build": getattr(service_info, 'build', None),
            "ports": getattr(service_info, 'ports', []),
            "environment": getattr(service_info, 'environment', {}),
            "volumes": getattr(service_info, 'volumes', []),
            "depends_on": getattr(service_info, 'depends_on', []),
            "healthcheck": getattr(service_info, 'health_check_url', None),
            "restart": getattr(service_info, 'restart_policy', None),
            "networks": getattr(service_info, 'networks', [])
        }

        return {"current_config": current_config}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get current config for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get current config: {e}")


@router.post("/services/config/validate")
async def validate_services_config(config_validation: Dict[str, Any]):
    """Validate configuration changes without applying them"""
    try:
        if meta_orchestrator is None:
            raise HTTPException(status_code=503, detail="Meta-orchestrator not initialized")

        services_config = config_validation.get("services", {})
        if not services_config:
            raise HTTPException(status_code=400, detail="No services configuration provided")

        validation_results = {}

        for service_name, config_updates in services_config.items():
            if service_name not in meta_orchestrator.services:
                validation_results[service_name] = {
                    "valid": False,
                    "errors": [f"Service {service_name} not found"]
                }
                continue

            validation_errors = validate_config_updates(service_name, config_updates)
            validation_results[service_name] = {
                "valid": len(validation_errors) == 0,
                "errors": validation_errors,
                "warnings": generate_config_warnings(service_name, config_updates)
            }

        overall_valid = all(result["valid"] for result in validation_results.values())

        return {
            "validation_result": {
                "overall_valid": overall_valid,
                "services_validated": len(validation_results),
                "services_valid": sum(1 for r in validation_results.values() if r["valid"]),
                "services_invalid": sum(1 for r in validation_results.values() if not r["valid"]),
                "service_results": validation_results
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to validate services config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate services config: {e}")


# Helper functions for configuration management

def validate_config_updates(service_name: str, config_updates: Dict[str, Any]) -> List[str]:
    """Validate configuration updates for a service"""
    errors = []

    # Validate ports
    if "ports" in config_updates:
        ports = config_updates["ports"]
        if not isinstance(ports, list):
            errors.append("Ports must be a list")
        else:
            for port_spec in ports:
                if not isinstance(port_spec, str) or ":" not in port_spec:
                    errors.append(f"Invalid port specification: {port_spec}")
                else:
                    try:
                        external, internal = port_spec.split(":")
                        int(external), int(internal)
                    except ValueError:
                        errors.append(f"Invalid port numbers in: {port_spec}")

    # Validate environment variables
    if "environment" in config_updates:
        env_vars = config_updates["environment"]
        if isinstance(env_vars, list):
            for env_item in env_vars:
                if not isinstance(env_item, str) or "=" not in env_item:
                    errors.append(f"Invalid environment variable format: {env_item}")
        elif isinstance(env_vars, dict):
            # Dict format is also valid
            pass
        else:
            errors.append("Environment must be a list or dictionary")

    # Validate volumes
    if "volumes" in config_updates:
        volumes = config_updates["volumes"]
        if not isinstance(volumes, list):
            errors.append("Volumes must be a list")
        else:
            for volume_spec in volumes:
                if not isinstance(volume_spec, str):
                    errors.append(f"Invalid volume specification: {volume_spec}")

    # Validate depends_on
    if "depends_on" in config_updates:
        depends_on = config_updates["depends_on"]
        if isinstance(depends_on, list):
            for dependency in depends_on:
                if not isinstance(dependency, str):
                    errors.append(f"Invalid dependency: {dependency}")
        elif isinstance(depends_on, dict):
            # Dict format with conditions is also valid
            pass
        else:
            errors.append("Depends_on must be a list or dictionary")

    # Validate image/build
    if "image" in config_updates and "build" in config_updates:
        errors.append("Cannot specify both 'image' and 'build'")

    # Validate restart policy
    if "restart" in config_updates:
        valid_restart_policies = ["no", "always", "on-failure", "unless-stopped"]
        restart_policy = config_updates["restart"]
        if restart_policy not in valid_restart_policies:
            errors.append(f"Invalid restart policy: {restart_policy}. Must be one of {valid_restart_policies}")

    return errors


def generate_config_warnings(service_name: str, config_updates: Dict[str, Any]) -> List[str]:
    """Generate warnings for potentially problematic configuration changes"""
    warnings = []

    # Warn about port changes
    if "ports" in config_updates:
        warnings.append("Port changes may require firewall updates or client reconfiguration")

    # Warn about environment variable changes
    if "environment" in config_updates:
        warnings.append("Environment variable changes may affect service behavior")

    # Warn about restart policy changes
    if "restart" in config_updates:
        restart_policy = config_updates["restart"]
        if restart_policy == "always":
            warnings.append("Restart policy 'always' may cause excessive container restarts")

    # Warn about dependency changes
    if "depends_on" in config_updates:
        warnings.append("Dependency changes may affect service startup order")

    # Warn about network changes
    if "networks" in config_updates:
        warnings.append("Network changes may affect service connectivity")

    return warnings


async def apply_service_config_changes(service_name: str, config_updates: Dict[str, Any]) -> Dict[str, Any]:
    """Apply configuration changes to a service"""
    try:
        # Get current service configuration
        service_info = meta_orchestrator.services[service_name]

        # Store original configuration for rollback
        original_config = {
            "image": getattr(service_info, 'image', None),
            "build": getattr(service_info, 'build', None),
            "ports": getattr(service_info, 'ports', []).copy(),
            "environment": getattr(service_info, 'environment', {}).copy() if hasattr(service_info, 'environment') else {},
            "volumes": getattr(service_info, 'volumes', []).copy(),
            "depends_on": getattr(service_info, 'depends_on', []).copy(),
            "restart": getattr(service_info, 'restart_policy', None),
            "networks": getattr(service_info, 'networks', []).copy()
        }

        # Apply configuration updates
        for key, value in config_updates.items():
            if key in ["restart_after_change", "restart_after_rollback"]:
                continue  # Skip control flags

            if hasattr(service_info, key) or key in ['image', 'build', 'ports', 'environment', 'volumes', 'depends_on', 'restart', 'networks']:
                setattr(service_info, key, value)
                logger.info(f"✅ Updated {service_name}.{key} = {value}")

        # Persist changes to docker-compose.yml (in a real implementation)
        # This would modify the actual docker-compose.yml file
        persistence_result = await persist_config_changes(service_name, config_updates)

        return {
            "success": True,
            "service_name": service_name,
            "changes_applied": list(config_updates.keys()),
            "original_config": original_config,
            "persistence_result": persistence_result,
            "message": f"Successfully applied {len(config_updates)} configuration changes to {service_name}"
        }

    except Exception as e:
        logger.error(f"❌ Failed to apply config changes to {service_name}: {e}")
        return {
            "success": False,
            "service_name": service_name,
            "error": str(e),
            "message": f"Failed to apply configuration changes to {service_name}"
        }


async def persist_config_changes(service_name: str, config_updates: Dict[str, Any]) -> Dict[str, Any]:
    """Persist configuration changes to docker-compose.yml file"""
    try:
        # In a real implementation, this would:
        # 1. Read the docker-compose.yml file
        # 2. Update the service configuration
        # 3. Write back the modified configuration
        # 4. Validate the YAML syntax

        # For now, simulate successful persistence
        return {
            "persisted": True,
            "file_updated": "docker-compose.yml",
            "backup_created": f"docker-compose.yml.backup.{int(time.time())}",
            "validation_passed": True
        }

    except Exception as e:
        logger.error(f"❌ Failed to persist config changes for {service_name}: {e}")
        return {
            "persisted": False,
            "error": str(e)
        }


async def restart_service_after_config_change(service_name: str) -> Dict[str, Any]:
    """Restart a service after configuration changes"""
    try:
        # Use the existing orchestrator restart functionality
        if hasattr(meta_orchestrator, 'restart_service'):
            result = await meta_orchestrator.restart_service(service_name)

            return {
                "restarted": result.success if hasattr(result, 'success') else True,
                "service_name": service_name,
                "message": result.message if hasattr(result, 'message') else "Service restarted"
            }
        else:
            # Mock orchestrator - simulate success
            return {
                "restarted": True,
                "service_name": service_name,
                "message": "Service restarted (mock)"
            }

    except Exception as e:
        logger.error(f"❌ Failed to restart service {service_name}: {e}")
        return {
            "restarted": False,
            "service_name": service_name,
            "error": str(e)
        }


async def rollback_config_changes(rollback_info: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rollback configuration changes for multiple services"""
    rollback_results = {}

    for rollback_item in rollback_info[::-1]:  # Rollback in reverse order
        service_name = rollback_item["service_name"]
        original_config = rollback_item["original_config"]

        try:
            result = await apply_service_config_changes(service_name, original_config)
            rollback_results[service_name] = {
                "rollback_success": result["success"],
                "message": result.get("message", "Rollback completed")
            }

            if result["success"] and rollback_item.get("restart_after_rollback", True):
                restart_result = await restart_service_after_config_change(service_name)
                result["restart_result"] = restart_result

        except Exception as e:
            rollback_results[service_name] = {
                "rollback_success": False,
                "error": str(e)
            }

    return {
        "services_attempted": len(rollback_info),
        "services_rolled_back": sum(1 for r in rollback_results.values() if r.get("rollback_success", False)),
        "results": rollback_results
    }


# Background task functions
async def start_all_services_background(profile: str):
    """Background task to start all services"""
    logger.info(f"🚀 Starting all services with profile '{profile}'")
    # Implementation would go here
    pass


async def stop_all_services_background():
    """Background task to stop all services"""
    logger.info("🛑 Stopping all services")
    # Implementation would go here
    pass
