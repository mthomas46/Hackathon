"""
Health Check System for MCP Services.

Provides health check endpoints and utilities for monitoring service health.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Enumerations
# ============================================================================

class HealthStatus(Enum):
    """Health status of a service or component."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class HealthCheck:
    """Health check result."""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    details: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}


@dataclass
class ServiceHealth:
    """Overall service health."""
    service_name: str
    status: HealthStatus
    version: str
    uptime_seconds: float
    checks: List[HealthCheck]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "service": self.service_name,
            "status": self.status.value,
            "version": self.version,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp.isoformat(),
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details
                }
                for check in self.checks
            ]
        }


# ============================================================================
# Health Check Manager
# ============================================================================

class HealthCheckManager:
    """
    Manages health checks for a service.
    
    Usage:
        manager = HealthCheckManager("my-service", "1.0.0")
        manager.add_check("database", check_database_health)
        manager.add_check("redis", check_redis_health)
        
        health = manager.get_health()
    """
    
    def __init__(self, service_name: str, version: str):
        """
        Initialize health check manager.
        
        Args:
            service_name: Name of the service
            version: Service version
        """
        self.service_name = service_name
        self.version = version
        self._checks: Dict[str, callable] = {}
        self._start_time = datetime.now()
        
        logger.info(f"HealthCheckManager initialized for {service_name} v{version}")
    
    def add_check(self, name: str, check_func: callable):
        """
        Add a health check.
        
        Args:
            name: Check name
            check_func: Function that returns HealthCheck
        """
        self._checks[name] = check_func
        logger.debug(f"Added health check: {name}")
    
    def get_health(self) -> ServiceHealth:
        """
        Get overall service health.
        
        Returns:
            ServiceHealth instance
        """
        # Run all checks
        check_results = []
        for name, check_func in self._checks.items():
            try:
                result = check_func()
                if not isinstance(result, HealthCheck):
                    result = HealthCheck(
                        name=name,
                        status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                        message="Check completed"
                    )
                check_results.append(result)
            except Exception as e:
                logger.error(f"Health check '{name}' failed: {str(e)}")
                check_results.append(HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {str(e)}"
                ))
        
        # Determine overall status
        overall_status = self._determine_overall_status(check_results)
        
        # Calculate uptime
        uptime = (datetime.now() - self._start_time).total_seconds()
        
        return ServiceHealth(
            service_name=self.service_name,
            status=overall_status,
            version=self.version,
            uptime_seconds=uptime,
            checks=check_results
        )
    
    def _determine_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Determine overall status from check results."""
        if not checks:
            return HealthStatus.HEALTHY
        
        # If any check is unhealthy, service is unhealthy
        if any(check.status == HealthStatus.UNHEALTHY for check in checks):
            return HealthStatus.UNHEALTHY
        
        # If any check is degraded, service is degraded
        if any(check.status == HealthStatus.DEGRADED for check in checks):
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def is_ready(self) -> bool:
        """Check if service is ready to accept requests."""
        health = self.get_health()
        return health.status != HealthStatus.UNHEALTHY


# ============================================================================
# Common Health Checks
# ============================================================================

def check_database_connection(db_client) -> HealthCheck:
    """
    Check database connection health.
    
    Args:
        db_client: Database client to check
    
    Returns:
        HealthCheck result
    """
    try:
        # Try a simple query
        db_client.execute("SELECT 1")
        return HealthCheck(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database connection healthy"
        )
    except Exception as e:
        return HealthCheck(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database connection failed: {str(e)}"
        )


def check_redis_connection(redis_client) -> HealthCheck:
    """
    Check Redis connection health.
    
    Args:
        redis_client: Redis client to check
    
    Returns:
        HealthCheck result
    """
    try:
        redis_client.ping()
        return HealthCheck(
            name="redis",
            status=HealthStatus.HEALTHY,
            message="Redis connection healthy"
        )
    except Exception as e:
        return HealthCheck(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            message=f"Redis connection failed: {str(e)}"
        )


def check_disk_space(threshold_percent: float = 90.0) -> HealthCheck:
    """
    Check disk space usage.
    
    Args:
        threshold_percent: Warning threshold percentage
    
    Returns:
        HealthCheck result
    """
    try:
        import shutil
        
        total, used, free = shutil.disk_usage("/")
        percent_used = (used / total) * 100
        
        if percent_used >= threshold_percent:
            status = HealthStatus.UNHEALTHY
            message = f"Disk space critical: {percent_used:.1f}% used"
        elif percent_used >= (threshold_percent - 10):
            status = HealthStatus.DEGRADED
            message = f"Disk space warning: {percent_used:.1f}% used"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk space healthy: {percent_used:.1f}% used"
        
        return HealthCheck(
            name="disk_space",
            status=status,
            message=message,
            details={
                "total_gb": total / (1024**3),
                "used_gb": used / (1024**3),
                "free_gb": free / (1024**3),
                "percent_used": percent_used
            }
        )
    except Exception as e:
        return HealthCheck(
            name="disk_space",
            status=HealthStatus.UNHEALTHY,
            message=f"Failed to check disk space: {str(e)}"
        )


def check_memory_usage(threshold_percent: float = 90.0) -> HealthCheck:
    """
    Check memory usage.
    
    Args:
        threshold_percent: Warning threshold percentage
    
    Returns:
        HealthCheck result
    """
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        percent_used = memory.percent
        
        if percent_used >= threshold_percent:
            status = HealthStatus.UNHEALTHY
            message = f"Memory critical: {percent_used:.1f}% used"
        elif percent_used >= (threshold_percent - 10):
            status = HealthStatus.DEGRADED
            message = f"Memory warning: {percent_used:.1f}% used"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory healthy: {percent_used:.1f}% used"
        
        return HealthCheck(
            name="memory",
            status=status,
            message=message,
            details={
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "percent_used": percent_used
            }
        )
    except ImportError:
        return HealthCheck(
            name="memory",
            status=HealthStatus.DEGRADED,
            message="psutil not available for memory monitoring"
        )
    except Exception as e:
        return HealthCheck(
            name="memory",
            status=HealthStatus.UNHEALTHY,
            message=f"Failed to check memory: {str(e)}"
        )


# ============================================================================
# FastAPI Integration
# ============================================================================

def create_health_endpoint(manager: HealthCheckManager):
    """
    Create FastAPI health endpoint.
    
    Returns function for use with FastAPI:
        @app.get("/health")
        async def health():
            return create_health_endpoint(manager)()
    """
    def health_check():
        health = manager.get_health()
        status_code = 200 if health.status != HealthStatus.UNHEALTHY else 503
        return health.to_dict(), status_code
    
    return health_check


def create_ready_endpoint(manager: HealthCheckManager):
    """
    Create FastAPI readiness endpoint.
    
    Returns function for use with FastAPI:
        @app.get("/ready")
        async def ready():
            return create_ready_endpoint(manager)()
    """
    def readiness_check():
        is_ready = manager.is_ready()
        status_code = 200 if is_ready else 503
        return {"ready": is_ready}, status_code
    
    return readiness_check

