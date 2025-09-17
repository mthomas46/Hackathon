"""Health Check Domain Service"""

import asyncio
import time
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime

from ..value_objects.health_status import HealthStatus
from ..value_objects.health_check_result import HealthCheckResult
from ..value_objects.service_health import ServiceHealth


class HealthCheckService:
    """Domain service for performing health checks on services."""

    def __init__(self, service_client=None):
        """Initialize the health check service."""
        self._service_client = service_client
        self._custom_checks: Dict[str, Callable] = {}

    def register_custom_check(self, service_name: str, check_function: Callable):
        """Register a custom health check function for a service."""
        self._custom_checks[service_name] = check_function

    async def check_service_health(
        self,
        service_name: str,
        timeout_seconds: float = 5.0
    ) -> ServiceHealth:
        """Check the health of a specific service."""
        start_time = time.time()

        try:
            # Try custom check first
            if service_name in self._custom_checks:
                result = await self._perform_custom_check(service_name, timeout_seconds)
            else:
                result = await self._perform_standard_check(service_name, timeout_seconds)

            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Update result with response time
            if result.response_time_ms is None:
                result = HealthCheckResult(
                    status=result.status,
                    message=result.message,
                    timestamp=result.timestamp,
                    details=result.details,
                    response_time_ms=response_time,
                    error_message=result.error_message
                )

            return ServiceHealth(
                service_name=service_name,
                status=result.status,
                check_result=result
            )

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            error_result = HealthCheckResult.failure(
                f"Health check timed out after {timeout_seconds}s",
                error_message="Timeout",
                response_time_ms=response_time
            )
            return ServiceHealth(
                service_name=service_name,
                status=HealthStatus.UNHEALTHY,
                check_result=error_result
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            error_result = HealthCheckResult.failure(
                f"Health check failed: {str(e)}",
                error_message=str(e),
                response_time_ms=response_time
            )
            return ServiceHealth(
                service_name=service_name,
                status=HealthStatus.UNHEALTHY,
                check_result=error_result
            )

    async def _perform_custom_check(
        self,
        service_name: str,
        timeout_seconds: float
    ) -> HealthCheckResult:
        """Perform a custom health check."""
        check_function = self._custom_checks[service_name]

        try:
            result = await asyncio.wait_for(
                check_function(),
                timeout=timeout_seconds
            )

            if isinstance(result, HealthCheckResult):
                return result
            elif isinstance(result, dict):
                return HealthCheckResult(
                    status=HealthStatus.from_string(result.get("status", "unknown")),
                    message=result.get("message", "Custom check completed"),
                    details=result.get("details", {}),
                    response_time_ms=result.get("response_time_ms")
                )
            elif isinstance(result, bool):
                return HealthCheckResult.success("Custom check passed") if result else HealthCheckResult.failure("Custom check failed")
            else:
                return HealthCheckResult.success("Custom check completed")

        except Exception as e:
            return HealthCheckResult.failure(
                f"Custom health check failed: {str(e)}",
                error_message=str(e)
            )

    async def _perform_standard_check(
        self,
        service_name: str,
        timeout_seconds: float
    ) -> HealthCheckResult:
        """Perform a standard health check."""
        # This would typically call the service's health endpoint
        # For now, we'll simulate a basic check
        try:
            # Simulate network call
            await asyncio.sleep(0.1)  # Simulate network latency

            # Mock successful response
            return HealthCheckResult.success(
                f"Service {service_name} is healthy",
                details={"endpoint": f"/health/{service_name}"}
            )

        except Exception as e:
            return HealthCheckResult.failure(
                f"Standard health check failed for {service_name}",
                error_message=str(e)
            )

    async def check_multiple_services(
        self,
        service_names: List[str],
        timeout_seconds: float = 5.0
    ) -> List[ServiceHealth]:
        """Check health of multiple services concurrently."""
        tasks = [
            self.check_service_health(service_name, timeout_seconds)
            for service_name in service_names
        ]

        return await asyncio.gather(*tasks)

    def get_registered_checks(self) -> List[str]:
        """Get list of services with registered custom checks."""
        return list(self._custom_checks.keys())
