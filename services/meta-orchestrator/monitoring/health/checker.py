"""Health checker for monitoring service health"""

import asyncio
import logging
import aiohttp
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from monitoring.database.models import ServiceHealth
from monitoring.database.manager import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckConfig:
    """Configuration for health checking a service"""
    service_name: str
    health_endpoint: str
    timeout: float = 10.0
    expected_status_codes: List[int] = None
    expected_response_keys: List[str] = None

    def __post_init__(self):
        if self.expected_status_codes is None:
            self.expected_status_codes = [200]
        if self.expected_response_keys is None:
            self.expected_response_keys = ['status']


class HealthChecker:
    """Service health checker"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.session: Optional[aiohttp.ClientSession] = None
        self.health_configs: Dict[str, HealthCheckConfig] = {}

    async def initialize(self):
        """Initialize the health checker"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        logger.info("🏥 Health checker initialized")

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        logger.info("🧹 Health checker cleanup completed")

    def add_service_config(self, config: HealthCheckConfig):
        """Add health check configuration for a service"""
        self.health_configs[config.service_name] = config
        logger.info(f"✅ Added health check config for {config.service_name}")

    def remove_service_config(self, service_name: str):
        """Remove health check configuration for a service"""
        if service_name in self.health_configs:
            del self.health_configs[service_name]
            logger.info(f"❌ Removed health check config for {service_name}")

    async def check_service_health(self, service_name: str) -> ServiceHealth:
        """Check health of a specific service"""
        if service_name not in self.health_configs:
            return ServiceHealth(
                service_name=service_name,
                health_status="unknown",
                error_message="No health check configuration found"
            )

        config = self.health_configs[service_name]
        start_time = time.time()

        try:
            async with self.session.get(
                config.health_endpoint,
                timeout=aiohttp.ClientTimeout(total=config.timeout)
            ) as response:
                response_time = time.time() - start_time
                status_code = response.status

                # Check status code
                if status_code not in config.expected_status_codes:
                    return ServiceHealth(
                        service_name=service_name,
                        health_status="unhealthy",
                        response_time=response_time,
                        error_message=f"Unexpected status code: {status_code}",
                        endpoint=config.health_endpoint,
                        status_code=status_code
                    )

                # Try to parse JSON response
                try:
                    response_data = await response.json()
                except Exception:
                    response_data = {}

                # Check for expected response keys
                missing_keys = []
                for key in config.expected_response_keys:
                    if key not in response_data:
                        missing_keys.append(key)

                if missing_keys:
                    return ServiceHealth(
                        service_name=service_name,
                        health_status="degraded",
                        response_time=response_time,
                        error_message=f"Missing expected response keys: {missing_keys}",
                        endpoint=config.health_endpoint,
                        status_code=status_code
                    )

                # Check response status if present
                if 'status' in response_data:
                    status_value = response_data['status'].lower()
                    if status_value not in ['healthy', 'ok', 'success']:
                        return ServiceHealth(
                            service_name=service_name,
                            health_status="degraded",
                            response_time=response_time,
                            error_message=f"Service reports status: {status_value}",
                            endpoint=config.health_endpoint,
                            status_code=status_code
                        )

                # All checks passed
                return ServiceHealth(
                    service_name=service_name,
                    health_status="healthy",
                    response_time=response_time,
                    endpoint=config.health_endpoint,
                    status_code=status_code
                )

        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return ServiceHealth(
                service_name=service_name,
                health_status="unhealthy",
                response_time=response_time,
                error_message="Health check timeout",
                endpoint=config.health_endpoint
            )

        except aiohttp.ClientError as e:
            response_time = time.time() - start_time
            return ServiceHealth(
                service_name=service_name,
                health_status="unhealthy",
                response_time=response_time,
                error_message=f"Connection error: {str(e)}",
                endpoint=config.health_endpoint
            )

        except Exception as e:
            response_time = time.time() - start_time
            return ServiceHealth(
                service_name=service_name,
                health_status="unhealthy",
                response_time=response_time,
                error_message=f"Unexpected error: {str(e)}",
                endpoint=config.health_endpoint
            )

    async def check_all_services_health(self) -> Dict[str, ServiceHealth]:
        """Check health of all configured services"""
        logger.info(f"🏥 Checking health of {len(self.health_configs)} services")

        tasks = []
        service_names = []

        for service_name in self.health_configs:
            task = self.check_service_health(service_name)
            tasks.append(task)
            service_names.append(service_name)

        # Execute all health checks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        health_results = {}
        for service_name, result in zip(service_names, results):
            if isinstance(result, Exception):
                # Handle exceptions in health checks
                health_results[service_name] = ServiceHealth(
                    service_name=service_name,
                    health_status="error",
                    error_message=f"Health check failed: {str(result)}"
                )
                logger.error(f"❌ Health check failed for {service_name}: {result}")
            else:
                health_results[service_name] = result
                logger.info(f"✅ Health check completed for {service_name}: {result.health_status}")

                # Save to database
                try:
                    self.db_manager.save_service_health(result)
                except Exception as e:
                    logger.error(f"❌ Failed to save health data for {service_name}: {e}")

        return health_results

    async def get_service_health_history(self, service_name: str, hours: int = 24) -> List[ServiceHealth]:
        """Get health history for a service"""
        return self.db_manager.get_service_health_history(service_name, hours)

    def get_health_summary(self, health_results: Dict[str, ServiceHealth]) -> Dict[str, Any]:
        """Generate a health summary"""
        total_services = len(health_results)
        healthy_count = sum(1 for h in health_results.values() if h.health_status == "healthy")
        unhealthy_count = sum(1 for h in health_results.values() if h.health_status == "unhealthy")
        degraded_count = sum(1 for h in health_results.values() if h.health_status == "degraded")
        error_count = sum(1 for h in health_results.values() if h.health_status == "error")

        # Calculate average response time
        response_times = [h.response_time for h in health_results.values() if h.response_time is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None

        return {
            "total_services": total_services,
            "healthy_services": healthy_count,
            "unhealthy_services": unhealthy_count,
            "degraded_services": degraded_count,
            "error_services": error_count,
            "overall_health_percentage": (healthy_count / total_services * 100) if total_services > 0 else 0,
            "average_response_time": avg_response_time,
            "timestamp": time.time()
        }

    async def continuous_health_monitoring(self, interval_seconds: int = 60):
        """Run continuous health monitoring"""
        logger.info(f"🔄 Starting continuous health monitoring (interval: {interval_seconds}s)")

        while True:
            try:
                health_results = await self.check_all_services_health()
                summary = self.get_health_summary(health_results)

                # Log summary
                healthy_pct = summary['overall_health_percentage']
                logger.info(f"🏥 Health check summary: {summary['healthy_services']}/{summary['total_services']} services healthy ({healthy_pct:.1f}%)")

                # Alert on critical issues
                if healthy_pct < 80:
                    logger.warning(f"⚠️  Low overall health: {healthy_pct:.1f}% of services are healthy")

                if summary['unhealthy_services'] > 0:
                    unhealthy_services = [name for name, health in health_results.items()
                                        if health.health_status == "unhealthy"]
                    logger.error(f"❌ Unhealthy services: {unhealthy_services}")

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"❌ Error in continuous health monitoring: {e}")
                await asyncio.sleep(interval_seconds)
