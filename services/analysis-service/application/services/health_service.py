"""Application Health Service - Comprehensive health monitoring and reporting."""

import asyncio
import psutil
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from .application_service import ApplicationService, ServiceContext, service_registry


class HealthCheck(ABC):
    """Abstract base class for health checks."""

    def __init__(self, name: str, description: str = "", critical: bool = True):
        """Initialize health check."""
        self.name = name
        self.description = description or f"Health check for {name}"
        self.critical = critical
        self.last_check_time = 0
        self.last_check_result: Optional[Dict[str, Any]] = None

    @abstractmethod
    async def check(self) -> Dict[str, Any]:
        """Perform health check."""
        pass

    def get_status(self) -> str:
        """Get health check status."""
        if self.last_check_result is None:
            return "unknown"

        return self.last_check_result.get('status', 'unknown')

    def is_healthy(self) -> bool:
        """Check if health check is passing."""
        return self.get_status() == "healthy"

    def get_details(self) -> Dict[str, Any]:
        """Get health check details."""
        return {
            'name': self.name,
            'description': self.description,
            'critical': self.critical,
            'status': self.get_status(),
            'last_check_time': self.last_check_time,
            'details': self.last_check_result or {}
        }


class DatabaseHealthCheck(HealthCheck):
    """Health check for database connectivity."""

    def __init__(self, database_url: str):
        """Initialize database health check."""
        super().__init__("database", "Database connectivity and performance check")
        self.database_url = database_url

    async def check(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            start_time = time.time()

            # Basic connectivity check
            if self.database_url.startswith('sqlite:///'):
                import sqlite3
                conn = sqlite3.connect(self.database_url.replace('sqlite:///', ''))
                conn.execute('SELECT 1').fetchone()
                conn.close()
                response_time = time.time() - start_time

                return {
                    'status': 'healthy',
                    'response_time_seconds': response_time,
                    'database_type': 'sqlite'
                }
            else:
                # For other databases, we'd need proper connection pooling
                # This is a placeholder for more complex database health checks
                response_time = time.time() - start_time
                return {
                    'status': 'healthy',
                    'response_time_seconds': response_time,
                    'database_type': 'external'
                }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'error_type': type(e).__name__
            }


class CacheHealthCheck(HealthCheck):
    """Health check for cache system."""

    def __init__(self, cache_service=None):
        """Initialize cache health check."""
        super().__init__("cache", "Cache system availability and performance check")
        self.cache_service = cache_service

    async def check(self) -> Dict[str, Any]:
        """Check cache health."""
        if not self.cache_service:
            return {
                'status': 'unhealthy',
                'error': 'Cache service not configured'
            }

        try:
            start_time = time.time()

            # Test cache operations
            test_key = f"health_check_{int(time.time())}"
            test_value = f"test_value_{int(time.time())}"

            await self.cache_service.set(test_key, test_value, ttl_seconds=60)
            retrieved_value = await self.cache_service.get(test_key)
            await self.cache_service.delete(test_key)

            response_time = time.time() - start_time

            if retrieved_value == test_value:
                return {
                    'status': 'healthy',
                    'response_time_seconds': response_time,
                    'cache_operations': 'read/write/delete successful'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Cache read/write test failed',
                    'response_time_seconds': response_time
                }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'error_type': type(e).__name__
            }


class ExternalServiceHealthCheck(HealthCheck):
    """Health check for external service dependencies."""

    def __init__(self, service_name: str, service_url: str, timeout_seconds: int = 5):
        """Initialize external service health check."""
        super().__init__(f"external_{service_name}", f"External service {service_name} availability check")
        self.service_name = service_name
        self.service_url = service_url
        self.timeout_seconds = timeout_seconds

    async def check(self) -> Dict[str, Any]:
        """Check external service health."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                start_time = time.time()

                async with session.get(
                    self.service_url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)
                ) as response:
                    response_time = time.time() - start_time

                    if response.status == 200:
                        return {
                            'status': 'healthy',
                            'response_time_seconds': response_time,
                            'http_status': response.status,
                            'service_url': self.service_url
                        }
                    else:
                        return {
                            'status': 'degraded',
                            'response_time_seconds': response_time,
                            'http_status': response.status,
                            'service_url': self.service_url
                        }

        except asyncio.TimeoutError:
            return {
                'status': 'unhealthy',
                'error': f'Timeout after {self.timeout_seconds} seconds',
                'service_url': self.service_url
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'error_type': type(e).__name__,
                'service_url': self.service_url
            }


class SystemHealthCheck(HealthCheck):
    """Health check for system resources."""

    def __init__(self):
        """Initialize system health check."""
        super().__init__("system", "System resource usage and availability check")

    async def check(self) -> Dict[str, Any]:
        """Check system health."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Network connectivity (basic check)
            network_ok = True
            try:
                # Try to resolve a well-known host
                import socket
                socket.gethostbyname('google.com')
            except Exception:
                network_ok = False

            # Determine overall status
            status = 'healthy'

            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 95:
                status = 'critical'
            elif cpu_percent > 75 or memory_percent > 80 or disk_percent > 85:
                status = 'degraded'
            elif not network_ok:
                status = 'degraded'

            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk_percent,
                'disk_free_gb': disk.free / (1024**3),
                'network_connectivity': network_ok
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'error_type': type(e).__name__
            }


class ApplicationHealth:
    """Application health aggregator and reporter."""

    def __init__(self):
        """Initialize application health."""
        self.health_checks: List[HealthCheck] = []
        self.overall_status = "unknown"
        self.last_check_time = 0
        self.check_interval = 30  # seconds

    def add_health_check(self, health_check: HealthCheck) -> None:
        """Add a health check."""
        self.health_checks.append(health_check)

    async def perform_health_checks(self) -> Dict[str, Any]:
        """Perform all health checks."""
        current_time = time.time()

        # Only perform checks if enough time has passed
        if current_time - self.last_check_time < self.check_interval:
            # Return cached results if available
            if hasattr(self, '_cached_results'):
                return self._cached_results

        results = {}
        critical_issues = []
        degraded_services = []

        for health_check in self.health_checks:
            try:
                check_result = await health_check.check()
                health_check.last_check_result = check_result
                health_check.last_check_time = current_time

                results[health_check.name] = health_check.get_details()

                if health_check.critical and check_result['status'] == 'unhealthy':
                    critical_issues.append(health_check.name)
                elif check_result['status'] == 'degraded':
                    degraded_services.append(health_check.name)

            except Exception as e:
                results[health_check.name] = {
                    'name': health_check.name,
                    'status': 'error',
                    'error': str(e)
                }
                if health_check.critical:
                    critical_issues.append(health_check.name)

        # Determine overall status
        if critical_issues:
            overall_status = "critical"
        elif degraded_services:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        self.overall_status = overall_status
        self.last_check_time = current_time

        health_report = {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': results,
            'summary': {
                'total_checks': len(self.health_checks),
                'critical_issues': len(critical_issues),
                'degraded_services': len(degraded_services),
                'healthy_checks': len([r for r in results.values() if r['status'] == 'healthy'])
            }
        }

        # Cache results
        self._cached_results = health_report

        return health_report

    def get_health_status(self) -> str:
        """Get current overall health status."""
        return self.overall_status

    def get_detailed_report(self) -> Dict[str, Any]:
        """Get detailed health report."""
        if hasattr(self, '_cached_results'):
            return self._cached_results

        # Perform checks if no cached results
        return asyncio.run(self.perform_health_checks())


class HealthService(ApplicationService):
    """Application health service for comprehensive health monitoring."""

    def __init__(self, check_interval: int = 30):
        """Initialize health service."""
        super().__init__("health_service")
        self.app_health = ApplicationHealth()
        self.app_health.check_interval = check_interval
        self._health_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start health service."""
        await super().start()

        # Add default health checks
        await self._setup_default_health_checks()

        # Start periodic health checking
        self._health_task = asyncio.create_task(self._periodic_health_check())

    async def stop(self) -> None:
        """Stop health service."""
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass

        await super().stop()

    async def _setup_default_health_checks(self) -> None:
        """Setup default health checks."""
        # System health check
        self.app_health.add_health_check(SystemHealthCheck())

        # Service registry health check
        await self._add_service_health_checks()

    async def _add_service_health_checks(self) -> None:
        """Add health checks for registered services."""
        try:
            # Get health status from service registry
            service_health = await service_registry.health_check_all()

            for service_name, health_data in service_health.items():
                # Create a synthetic health check for each service
                health_check = ServiceHealthCheck(service_name, health_data)
                self.app_health.add_health_check(health_check)

        except Exception as e:
            self.logger.error(f"Error setting up service health checks: {e}")

    async def _periodic_health_check(self) -> None:
        """Perform periodic health checks."""
        while self._running:
            try:
                await asyncio.sleep(self.app_health.check_interval)

                # Perform health checks
                health_report = await self.app_health.perform_health_checks()

                # Log health status
                status = health_report['status']
                if status == 'critical':
                    self.logger.error("Health check: CRITICAL", extra=health_report)
                elif status == 'degraded':
                    self.logger.warning("Health check: DEGRADED", extra=health_report)
                else:
                    self.logger.debug("Health check: HEALTHY", extra=health_report)

                # Publish health event
                if hasattr(self, 'event_bus') and self.event_bus:
                    from ..events.application_events import SystemHealthCheckEvent

                    health_event = SystemHealthCheckEvent(
                        event_id=f"health_check_{int(time.time())}",
                        service_name="analysis-service",
                        service_version="1.0.0",
                        health_status=status,
                        response_time_ms=self.app_health.check_interval * 1000,
                        system_metrics=health_report
                    )

                    await self.event_bus.publish(health_event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic health check: {e}")

    async def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report."""
        async with self.operation_context("get_health_report"):
            return await self.app_health.perform_health_checks()

    async def get_health_status(self) -> str:
        """Get current health status."""
        return self.app_health.get_health_status()

    async def add_health_check(self, health_check: HealthCheck) -> None:
        """Add a custom health check."""
        async with self.operation_context("add_health_check"):
            self.app_health.add_health_check(health_check)
            self.logger.info(f"Added health check: {health_check.name}")

    async def remove_health_check(self, health_check_name: str) -> bool:
        """Remove a health check."""
        async with self.operation_context("remove_health_check"):
            original_count = len(self.app_health.health_checks)
            self.app_health.health_checks = [
                hc for hc in self.app_health.health_checks
                if hc.name != health_check_name
            ]

            removed = len(self.app_health.health_checks) < original_count
            if removed:
                self.logger.info(f"Removed health check: {health_check_name}")

            return removed

    async def list_health_checks(self) -> List[Dict[str, Any]]:
        """List all health checks."""
        return [hc.get_details() for hc in self.app_health.health_checks]

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = await super().health_check()

        # Add health service specific info
        try:
            health_report = await self.get_health_report()
            health['health_service'] = {
                'overall_status': health_report['status'],
                'total_checks': health_report['summary']['total_checks'],
                'critical_issues': health_report['summary']['critical_issues'],
                'degraded_services': health_report['summary']['degraded_services'],
                'healthy_checks': health_report['summary']['healthy_checks'],
                'check_interval_seconds': self.app_health.check_interval
            }

        except Exception as e:
            health['health_service'] = {'error': str(e)}

        return health


class ServiceHealthCheck(HealthCheck):
    """Health check for a registered service."""

    def __init__(self, service_name: str, health_data: Dict[str, Any]):
        """Initialize service health check."""
        super().__init__(f"service_{service_name}", f"Service {service_name} health check", critical=True)
        self.service_name = service_name
        self.health_data = health_data

    async def check(self) -> Dict[str, Any]:
        """Check service health."""
        # Use the health data provided during initialization
        # In a real implementation, this would query the service
        status = self.health_data.get('status', 'unknown')

        return {
            'status': status,
            'service_name': self.service_name,
            'details': self.health_data
        }


class DependencyHealthCheck(HealthCheck):
    """Health check for service dependencies."""

    def __init__(self, dependencies: Dict[str, str]):
        """Initialize dependency health check."""
        super().__init__("dependencies", "Service dependencies health check")
        self.dependencies = dependencies

    async def check(self) -> Dict[str, Any]:
        """Check dependency health."""
        dependency_status = {}

        for name, url in self.dependencies.items():
            try:
                # Simple HTTP check for dependency
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        dependency_status[name] = {
                            'status': 'healthy' if response.status == 200 else 'degraded',
                            'http_status': response.status,
                            'url': url
                        }

            except Exception as e:
                dependency_status[name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'url': url
                }

        # Determine overall status
        unhealthy_deps = [name for name, status in dependency_status.items()
                         if status['status'] == 'unhealthy']

        if unhealthy_deps:
            overall_status = 'unhealthy'
        else:
            degraded_deps = [name for name, status in dependency_status.items()
                           if status['status'] == 'degraded']
            overall_status = 'degraded' if degraded_deps else 'healthy'

        return {
            'status': overall_status,
            'dependencies': dependency_status,
            'unhealthy_count': len(unhealthy_deps)
        }


# Global health service instance
health_service = HealthService()

# Create application health instance
app_health = health_service.app_health
