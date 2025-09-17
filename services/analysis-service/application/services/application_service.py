"""Base Application Service - Foundation for cross-cutting concerns."""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass

from ..events import EventBus


logger = logging.getLogger(__name__)


T = TypeVar('T')


@dataclass
class ServiceContext:
    """Context for service operations."""
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    start_time: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.start_time == 0.0:
            self.start_time = time.time()


class ApplicationService(ABC):
    """Base class for application services with cross-cutting concerns."""

    def __init__(
        self,
        service_name: str,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize application service."""
        self.service_name = service_name
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger(f"{__name__}.{service_name}")

        # Service state
        self._running = False
        self._health_check_interval = 60  # seconds
        self._last_health_check = 0
        self._operation_count = 0
        self._error_count = 0

    async def start(self) -> None:
        """Start the service."""
        self._running = True
        self.logger.info(f"Starting {self.service_name} service")

        # Publish service started event
        if self.event_bus:
            await self._publish_service_event("service_started")

    async def stop(self) -> None:
        """Stop the service."""
        self._running = False
        self.logger.info(f"Stopping {self.service_name} service")

        # Publish service stopped event
        if self.event_bus:
            await self._publish_service_event("service_stopped")

    def is_running(self) -> bool:
        """Check if service is running."""
        return self._running

    @asynccontextmanager
    async def operation_context(
        self,
        operation_name: str,
        context: Optional[ServiceContext] = None
    ):
        """Context manager for service operations with monitoring."""
        if context is None:
            context = ServiceContext()

        operation_start = time.time()
        self._operation_count += 1

        try:
            self.logger.debug(
                f"Starting operation: {operation_name}",
                extra={
                    'operation': operation_name,
                    'correlation_id': context.correlation_id,
                    'service': self.service_name
                }
            )

            yield context

            operation_duration = time.time() - operation_start
            self.logger.info(
                f"Completed operation: {operation_name} in {operation_duration:.3f}s",
                extra={
                    'operation': operation_name,
                    'duration': operation_duration,
                    'correlation_id': context.correlation_id,
                    'service': self.service_name
                }
            )

        except Exception as e:
            operation_duration = time.time() - operation_start
            self._error_count += 1

            self.logger.error(
                f"Failed operation: {operation_name} in {operation_duration:.3f}s",
                exc_info=True,
                extra={
                    'operation': operation_name,
                    'duration': operation_duration,
                    'error': str(e),
                    'correlation_id': context.correlation_id,
                    'service': self.service_name
                }
            )

            # Publish operation failed event
            if self.event_bus:
                await self._publish_operation_event(
                    "operation_failed",
                    operation_name,
                    context,
                    error=str(e),
                    duration=operation_duration
                )

            raise

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        current_time = time.time()

        health_status = {
            'service': self.service_name,
            'status': 'healthy' if self._running else 'stopped',
            'timestamp': current_time,
            'uptime': current_time - self._last_health_check if self._last_health_check > 0 else 0,
            'operations': {
                'total': self._operation_count,
                'errors': self._error_count,
                'success_rate': (self._operation_count - self._error_count) / max(1, self._operation_count)
            }
        }

        self._last_health_check = current_time
        return health_status

    async def _publish_service_event(self, event_type: str, **kwargs) -> None:
        """Publish service-related event."""
        if not self.event_bus:
            return

        from ..events.application_events import SystemHealthCheckEvent

        event = SystemHealthCheckEvent(
            event_id=f"{self.service_name}_{event_type}_{int(time.time())}",
            service_name=self.service_name,
            service_version=getattr(self, 'version', '1.0.0'),
            health_status=event_type,
            response_time_ms=0.0,
            system_metrics={
                'operation_count': self._operation_count,
                'error_count': self._error_count,
                **kwargs
            }
        )

        await self.event_bus.publish(event)

    async def _publish_operation_event(
        self,
        event_type: str,
        operation_name: str,
        context: ServiceContext,
        **kwargs
    ) -> None:
        """Publish operation-related event."""
        if not self.event_bus:
            return

        # Create a custom operation event
        from ..events.application_events import ApplicationEvent, EventType

        event = ApplicationEvent(
            event_id=f"{self.service_name}_{operation_name}_{event_type}_{int(time.time())}",
            event_type=EventType.SYSTEM_HEALTH_CHECK,  # Using existing event type for now
            correlation_id=context.correlation_id,
            metadata={
                'service': self.service_name,
                'operation': operation_name,
                'event_type': event_type,
                'user_id': context.user_id,
                'session_id': context.session_id,
                **kwargs
            }
        )

        await self.event_bus.publish(event)


class ServiceRegistry:
    """Registry for managing application services."""

    def __init__(self):
        """Initialize service registry."""
        self.services: Dict[str, ApplicationService] = {}
        self._startup_order: list = []
        self._shutdown_order: list = []

    def register(
        self,
        service: ApplicationService,
        startup_priority: int = 50,
        shutdown_priority: int = 50
    ) -> None:
        """Register a service."""
        service_name = service.service_name

        if service_name in self.services:
            raise ValueError(f"Service {service_name} already registered")

        self.services[service_name] = service

        # Insert in startup order (lower priority first)
        startup_idx = 0
        for i, (name, pri) in enumerate(self._startup_order):
            if startup_priority < pri:
                startup_idx = i
                break
            startup_idx = i + 1

        self._startup_order.insert(startup_idx, (service_name, startup_priority))

        # Insert in shutdown order (higher priority first for shutdown)
        shutdown_idx = 0
        for i, (name, pri) in enumerate(self._shutdown_order):
            if shutdown_priority > pri:
                shutdown_idx = i
                break
            shutdown_idx = i + 1

        self._shutdown_order.insert(shutdown_idx, (service_name, shutdown_priority))

        logger.info(f"Registered service: {service_name}")

    def unregister(self, service_name: str) -> None:
        """Unregister a service."""
        if service_name in self.services:
            del self.services[service_name]
            self._startup_order = [(name, pri) for name, pri in self._startup_order if name != service_name]
            self._shutdown_order = [(name, pri) for name, pri in self._shutdown_order if name != service_name]
            logger.info(f"Unregistered service: {service_name}")

    async def start_all(self) -> None:
        """Start all registered services in order."""
        logger.info("Starting all services...")

        for service_name, _ in self._startup_order:
            service = self.services[service_name]
            try:
                await service.start()
                logger.info(f"Started service: {service_name}")
            except Exception as e:
                logger.error(f"Failed to start service {service_name}: {e}", exc_info=True)
                raise

        logger.info("All services started")

    async def stop_all(self) -> None:
        """Stop all registered services in reverse order."""
        logger.info("Stopping all services...")

        for service_name, _ in self._shutdown_order:
            service = self.services[service_name]
            try:
                await service.stop()
                logger.info(f"Stopped service: {service_name}")
            except Exception as e:
                logger.error(f"Error stopping service {service_name}: {e}", exc_info=True)

        logger.info("All services stopped")

    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all services."""
        results = {}

        for service_name, service in self.services.items():
            try:
                health = await service.health_check()
                results[service_name] = health
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                results[service_name] = {
                    'service': service_name,
                    'status': 'error',
                    'error': str(e)
                }

        return results

    def get_service(self, service_name: str) -> Optional[ApplicationService]:
        """Get a registered service by name."""
        return self.services.get(service_name)


# Global service registry instance
service_registry = ServiceRegistry()
