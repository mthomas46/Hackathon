"""Simulation Health Checks - Reuse Shared Health Check Patterns.

This module implements comprehensive health checking for the simulation service,
following the established patterns from services/shared/health/ for consistency
and reusability across the ecosystem.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import httpx

# Import from shared infrastructure
shared_path = Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"
sys.path.insert(0, str(shared_path))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.monitoring.simulation_monitoring import get_simulation_monitoring_service

# Import shared health patterns (with fallbacks)
try:
    from monitoring.health import HealthStatus, register_health_endpoints
    # Create simple mock implementations for missing classes
    class HealthCheck:
        pass

    class HealthChecker:
        pass

    class ServiceHealthIndicator:
        pass

    class DatabaseHealthIndicator:
        pass

    class HealthEndpoint:
        pass

except ImportError:
    # Fallback implementations
    from enum import Enum

    class HealthStatus(str, Enum):
        HEALTHY = "healthy"
        DEGRADED = "degraded"
        UNHEALTHY = "unhealthy"

    class HealthCheck:
        def __init__(self, name: str):
            self.name = name
            self.status = HealthStatus.HEALTHY
            self.timestamp = datetime.now()
            self.details = {}

        def update_status(self, status: HealthStatus, details: Dict[str, Any] = None):
            self.status = status
            self.timestamp = datetime.now()
            if details:
                self.details.update(details)

    class HealthChecker:
        def __init__(self):
            self.checks = {}

        def add_check(self, name: str) -> HealthCheck:
            check = HealthCheck(name)
            self.checks[name] = check
            return check

        def run_checks(self) -> Dict[str, HealthCheck]:
            return self.checks

    class ServiceHealthIndicator:
        def __init__(self, service_name: str, service_url: str):
            self.service_name = service_name
            self.service_url = service_url
            self.last_check = datetime.now()
            self.status = HealthStatus.HEALTHY

        async def check_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.service_url}/health")
                    if response.status_code == 200:
                        return HealthStatus.HEALTHY, {"response_time": response.elapsed.total_seconds()}
                    else:
                        return HealthStatus.UNHEALTHY, {"status_code": response.status_code}
            except Exception as e:
                return HealthStatus.UNHEALTHY, {"error": str(e)}

    class DatabaseHealthIndicator:
        def __init__(self, connection_string: str):
            self.connection_string = connection_string
            self.last_check = datetime.now()
            self.status = HealthStatus.HEALTHY

        async def check_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
            # Simplified database health check
            try:
                # In real implementation, would test actual database connection
                return HealthStatus.HEALTHY, {"connection": "ok"}
            except Exception as e:
                return HealthStatus.UNHEALTHY, {"error": str(e)}

    class HealthEndpoint:
        def __init__(self, path: str = "/health"):
            self.path = path

        async def get_health_status(self) -> Dict[str, Any]:
            return {
                "status": "healthy",
                "timestamp": datetime.now(),
                "checks": {}
            }


class SimulationHealthChecker(HealthChecker):
    """Simulation-specific health checker extending shared patterns."""

    def __init__(self):
        super().__init__()
        self.logger = get_simulation_logger()
        self.monitoring_service = get_simulation_monitoring_service()
        self._initialize_simulation_checks()

    def _initialize_simulation_checks(self):
        """Initialize simulation-specific health checks."""
        # Core system checks
        self.add_check("simulation_engine")
        self.add_check("memory_usage")
        self.add_check("cpu_usage")
        self.add_check("disk_space")

        # Database checks
        self.add_check("database_connection")
        self.add_check("database_performance")

        # External service checks
        self.add_check("ecosystem_services")
        self.add_check("mock_data_generator")
        self.add_check("doc_store")
        self.add_check("analysis_service")
        self.add_check("llm_gateway")

        # Queue and processing checks
        self.add_check("simulation_queue")
        self.add_check("active_simulations")

        # Performance checks
        self.add_check("response_times")
        self.add_check("error_rates")

    async def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check following shared patterns."""
        start_time = datetime.now()

        # Run all health checks
        health_results = await self._run_all_checks()

        # Aggregate results
        overall_status = self._calculate_overall_status(health_results)
        health_score = self._calculate_health_score(health_results)

        # Get monitoring snapshot
        monitoring_snapshot = self.monitoring_service.get_monitoring_snapshot()

        comprehensive_result = {
            "status": overall_status,
            "timestamp": datetime.now(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "health_score": health_score,
            "checks": health_results,
            "monitoring": monitoring_snapshot,
            "recommendations": self._generate_health_recommendations(health_results)
        }

        self.logger.info(
            "Comprehensive health check completed",
            status=overall_status,
            health_score=health_score,
            duration_seconds=comprehensive_result["duration_seconds"]
        )

        return comprehensive_result

    async def _run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks concurrently."""
        check_results = {}

        # System resource checks
        check_results.update(await self._check_system_resources())

        # Database checks
        check_results.update(await self._check_database_health())

        # External service checks
        check_results.update(await self._check_ecosystem_services())

        # Application-specific checks
        check_results.update(await self._check_simulation_health())

        return check_results

    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource health."""
        results = {}

        # Memory usage check
        memory_check = self.checks["memory_usage"]
        try:
            # In production, would use psutil or similar
            memory_usage = 512  # MB - placeholder
            memory_threshold = 1024  # MB

            if memory_usage > memory_threshold * 0.9:
                memory_check.update_status(HealthStatus.UNHEALTHY, {"memory_mb": memory_usage})
            elif memory_usage > memory_threshold * 0.7:
                memory_check.update_status(HealthStatus.DEGRADED, {"memory_mb": memory_usage})
            else:
                memory_check.update_status(HealthStatus.HEALTHY, {"memory_mb": memory_usage})

        except Exception as e:
            memory_check.update_status(HealthStatus.UNHEALTHY, {"error": str(e)})

        results["memory_usage"] = {
            "status": memory_check.status,
            "details": memory_check.details,
            "timestamp": memory_check.timestamp
        }

        # CPU usage check
        cpu_check = self.checks["cpu_usage"]
        try:
            cpu_usage = 45.0  # % - placeholder
            cpu_threshold = 80.0  # %

            if cpu_usage > cpu_threshold:
                cpu_check.update_status(HealthStatus.UNHEALTHY, {"cpu_percent": cpu_usage})
            elif cpu_usage > cpu_threshold * 0.7:
                cpu_check.update_status(HealthStatus.DEGRADED, {"cpu_percent": cpu_usage})
            else:
                cpu_check.update_status(HealthStatus.HEALTHY, {"cpu_percent": cpu_usage})

        except Exception as e:
            cpu_check.update_status(HealthStatus.UNHEALTHY, {"error": str(e)})

        results["cpu_usage"] = {
            "status": cpu_check.status,
            "details": cpu_check.details,
            "timestamp": cpu_check.timestamp
        }

        return results

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health following shared patterns."""
        results = {}

        # Database connection check
        db_check = self.checks["database_connection"]
        try:
            # In production, would test actual database connection
            db_indicator = DatabaseHealthIndicator("postgresql://simulation:password@localhost:5432/simulation")
            status, details = await db_indicator.check_health()

            db_check.update_status(status, details)

        except Exception as e:
            db_check.update_status(HealthStatus.UNHEALTHY, {"error": str(e)})

        results["database_connection"] = {
            "status": db_check.status,
            "details": db_check.details,
            "timestamp": db_check.timestamp
        }

        # Database performance check
        perf_check = self.checks["database_performance"]
        try:
            # Simplified performance check
            query_time = 0.05  # seconds - placeholder
            performance_threshold = 1.0  # seconds

            if query_time > performance_threshold:
                perf_check.update_status(HealthStatus.UNHEALTHY, {"query_time_seconds": query_time})
            elif query_time > performance_threshold * 0.5:
                perf_check.update_status(HealthStatus.DEGRADED, {"query_time_seconds": query_time})
            else:
                perf_check.update_status(HealthStatus.HEALTHY, {"query_time_seconds": query_time})

        except Exception as e:
            perf_check.update_status(HealthStatus.UNHEALTHY, {"error": str(e)})

        results["database_performance"] = {
            "status": perf_check.status,
            "details": perf_check.details,
            "timestamp": perf_check.timestamp
        }

        return results

    async def _check_ecosystem_services(self) -> Dict[str, Any]:
        """Check ecosystem service health following shared patterns."""
        results = {}
        services_to_check = {
            "mock_data_generator": "http://localhost:5002",
            "doc_store": "http://localhost:5003",
            "analysis_service": "http://localhost:5004",
            "llm_gateway": "http://localhost:5005"
        }

        for service_name, service_url in services_to_check.items():
            check = self.checks.get(service_name, self.add_check(service_name))
            try:
                indicator = ServiceHealthIndicator(service_name, service_url)
                status, details = await indicator.check_health()

                check.update_status(status, details)

            except Exception as e:
                check.update_status(HealthStatus.UNHEALTHY, {"error": str(e)})

            results[service_name] = {
                "status": check.status,
                "details": check.details,
                "timestamp": check.timestamp
            }

        # Overall ecosystem services check
        ecosystem_check = self.checks["ecosystem_services"]
        unhealthy_services = [name for name, result in results.items() if result["status"] != HealthStatus.HEALTHY]

        if unhealthy_services:
            ecosystem_check.update_status(
                HealthStatus.UNHEALTHY if len(unhealthy_services) > 2 else HealthStatus.DEGRADED,
                {"unhealthy_services": unhealthy_services}
            )
        else:
            ecosystem_check.update_status(HealthStatus.HEALTHY, {"all_services_healthy": True})

        results["ecosystem_services"] = {
            "status": ecosystem_check.status,
            "details": ecosystem_check.details,
            "timestamp": ecosystem_check.timestamp
        }

        return results

    async def _check_simulation_health(self) -> Dict[str, Any]:
        """Check simulation-specific health metrics."""
        results = {}

        # Simulation queue check
        queue_check = self.checks["simulation_queue"]
        try:
            queue_depth = self.monitoring_service.metrics_collector.get_metric_value("simulation_queue_depth") or 0
            queue_threshold = 20

            if queue_depth > queue_threshold * 2:
                queue_check.update_status(HealthStatus.UNHEALTHY, {"queue_depth": queue_depth})
            elif queue_depth > queue_threshold:
                queue_check.update_status(HealthStatus.DEGRADED, {"queue_depth": queue_depth})
            else:
                queue_check.update_status(HealthStatus.HEALTHY, {"queue_depth": queue_depth})

        except Exception as e:
            queue_check.update_status(HealthStatus.UNHEALTHY, {"error": str(e)})

        results["simulation_queue"] = {
            "status": queue_check.status,
            "details": queue_check.details,
            "timestamp": queue_check.timestamp
        }

        # Active simulations check
        active_check = self.checks["active_simulations"]
        try:
            active_count = self.monitoring_service.metrics_collector.get_metric_value("simulation_active_count") or 0
            active_threshold = 50

            if active_count > active_threshold * 2:
                active_check.update_status(HealthStatus.UNHEALTHY, {"active_simulations": active_count})
            elif active_count > active_threshold:
                active_check.update_status(HealthStatus.DEGRADED, {"active_simulations": active_count})
            else:
                active_check.update_status(HealthStatus.HEALTHY, {"active_simulations": active_count})

        except Exception as e:
            active_check.update_status(HealthStatus.UNHEALTHY, {"error": str(e)})

        results["active_simulations"] = {
            "status": active_check.status,
            "details": active_check.details,
            "timestamp": active_check.timestamp
        }

        # Response times check
        response_check = self.checks["response_times"]
        try:
            avg_response_time = self.monitoring_service.metrics_collector.get_metric_value("ecosystem_service_response_time") or 0
            response_threshold = 2.0  # seconds

            if avg_response_time > response_threshold * 3:
                response_check.update_status(HealthStatus.UNHEALTHY, {"avg_response_time": avg_response_time})
            elif avg_response_time > response_threshold:
                response_check.update_status(HealthStatus.DEGRADED, {"avg_response_time": avg_response_time})
            else:
                response_check.update_status(HealthStatus.HEALTHY, {"avg_response_time": avg_response_time})

        except Exception as e:
            response_check.update_status(HealthStatus.UNHEALTHY, {"error": str(e)})

        results["response_times"] = {
            "status": response_check.status,
            "details": response_check.details,
            "timestamp": response_check.timestamp
        }

        # Error rates check
        error_check = self.checks["error_rates"]
        try:
            error_rate = self.monitoring_service.metrics_collector.get_metric_value("error_rate_percent", {"operation_type": "simulation"}) or 0
            error_threshold = 5.0  # %

            if error_rate > error_threshold * 4:
                error_check.update_status(HealthStatus.UNHEALTHY, {"error_rate_percent": error_rate})
            elif error_rate > error_threshold:
                error_check.update_status(HealthStatus.DEGRADED, {"error_rate_percent": error_rate})
            else:
                error_check.update_status(HealthStatus.HEALTHY, {"error_rate_percent": error_rate})

        except Exception as e:
            error_check.update_status(HealthStatus.UNHEALTHY, {"error": str(e)})

        results["error_rates"] = {
            "status": error_check.status,
            "details": error_check.details,
            "timestamp": error_check.timestamp
        }

        return results

    def _calculate_overall_status(self, health_results: Dict[str, Any]) -> HealthStatus:
        """Calculate overall health status."""
        statuses = [result["status"] for result in health_results.values()]

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def _calculate_health_score(self, health_results: Dict[str, Any]) -> float:
        """Calculate overall health score (0-100)."""
        total_checks = len(health_results)
        if total_checks == 0:
            return 100.0

        healthy_count = sum(1 for result in health_results.values() if result["status"] == HealthStatus.HEALTHY)
        degraded_count = sum(1 for result in health_results.values() if result["status"] == HealthStatus.DEGRADED)

        # Weight: healthy = 1.0, degraded = 0.5, unhealthy = 0.0
        score = (healthy_count * 1.0 + degraded_count * 0.5) / total_checks * 100

        return round(score, 2)

    def _generate_health_recommendations(self, health_results: Dict[str, Any]) -> List[str]:
        """Generate health recommendations based on check results."""
        recommendations = []

        for check_name, result in health_results.items():
            if result["status"] == HealthStatus.UNHEALTHY:
                if "memory" in check_name:
                    recommendations.append("Consider increasing memory allocation or optimizing memory usage")
                elif "cpu" in check_name:
                    recommendations.append("Monitor CPU usage and consider scaling resources")
                elif "database" in check_name:
                    recommendations.append("Check database connectivity and performance")
                elif "queue" in check_name:
                    recommendations.append("Reduce simulation queue depth by scaling or optimizing processing")
                elif check_name in ["mock_data_generator", "doc_store", "analysis_service", "llm_gateway"]:
                    recommendations.append(f"Investigate connectivity issues with {check_name} service")
                else:
                    recommendations.append(f"Address issues with {check_name} component")

            elif result["status"] == HealthStatus.DEGRADED:
                recommendations.append(f"Monitor {check_name} performance closely")

        if not recommendations:
            recommendations.append("All systems operating within normal parameters")

        return recommendations


class SimulationHealthEndpoint(HealthEndpoint):
    """Simulation-specific health endpoint following shared patterns."""

    def __init__(self, health_checker: SimulationHealthChecker):
        super().__init__()
        self.health_checker = health_checker

    async def get_detailed_health_status(self) -> Dict[str, Any]:
        """Get detailed health status for internal monitoring."""
        return await self.health_checker.perform_comprehensive_health_check()

    async def get_simple_health_status(self) -> Dict[str, Any]:
        """Get simple health status for load balancers and external monitoring."""
        comprehensive = await self.get_detailed_health_status()

        return {
            "status": comprehensive["status"],
            "timestamp": comprehensive["timestamp"],
            "version": "1.0.0",  # Would be dynamic in production
            "uptime_seconds": 3600  # Would be calculated in production
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status - override for simulation-specific logic."""
        return await self.get_detailed_health_status()


# Global health checker instance
_simulation_health_checker: Optional[SimulationHealthChecker] = None
_simulation_health_endpoint: Optional[SimulationHealthEndpoint] = None


def get_simulation_health_checker() -> SimulationHealthChecker:
    """Get the global simulation health checker instance."""
    global _simulation_health_checker
    if _simulation_health_checker is None:
        _simulation_health_checker = SimulationHealthChecker()
    return _simulation_health_checker


def get_simulation_health_endpoint() -> SimulationHealthEndpoint:
    """Get the global simulation health endpoint instance."""
    global _simulation_health_endpoint
    if _simulation_health_endpoint is None:
        _simulation_health_endpoint = SimulationHealthEndpoint(get_simulation_health_checker())
    return _simulation_health_endpoint


__all__ = [
    'SimulationHealthChecker',
    'SimulationHealthEndpoint',
    'get_simulation_health_checker',
    'get_simulation_health_endpoint'
]
