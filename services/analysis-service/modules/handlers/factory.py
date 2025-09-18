"""Handler Factory - Creates handlers with dependency injection."""

from typing import Dict, Any, Type, Optional, List
from .base_handler import BaseAnalysisHandler
from .semantic_handler import SemanticAnalysisHandler
from .sentiment_handler import SentimentAnalysisHandler
from .impact_handler import ChangeImpactAnalysisHandler
from .risk_handler import RiskAnalysisHandler
from .maintenance_handler import MaintenanceAnalysisHandler
from .remediation_handler import RemediationHandler
from .workflow_handler import WorkflowAnalysisHandler
from .distributed_handler import DistributedAnalysisHandler
from .cross_repository_handler import CrossRepositoryAnalysisHandler
from .quality_handler import QualityAnalysisHandler
from .trend_handler import TrendAnalysisHandler

from services.shared.core.di.services import (
    ILoggerService, ICacheService, IEventPublisher, IServiceClient, IMetricsService
)
from services.shared.core.di.registry import get_service


class HandlerFactory:
    """Factory for creating analysis handlers with dependency injection."""

    def __init__(self,
                 logger: Optional[ILoggerService] = None,
                 cache: Optional[ICacheService] = None,
                 event_publisher: Optional[IEventPublisher] = None,
                 service_client: Optional[IServiceClient] = None,
                 metrics: Optional[IMetricsService] = None) -> None:
        # Use injected services or get from registry
        self._logger = logger or get_service(ILoggerService)
        self._cache = cache or get_service(ICacheService)
        self._event_publisher = event_publisher or get_service(IEventPublisher)
        self._service_client = service_client or get_service(IServiceClient)
        self._metrics = metrics or get_service(IMetricsService)

        # Handler registry
        self._handler_classes: Dict[str, Type[BaseAnalysisHandler]] = {
            "semantic_similarity": SemanticAnalysisHandler,
            "sentiment_analysis": SentimentAnalysisHandler,
            "tone_analysis": SentimentAnalysisHandler,  # Reuse sentiment handler
            "content_quality": QualityAnalysisHandler,
            "trend_analysis": TrendAnalysisHandler,
            "portfolio_trend_analysis": TrendAnalysisHandler,  # Reuse trend handler
            "risk_assessment": RiskAnalysisHandler,
            "portfolio_risk_assessment": RiskAnalysisHandler,  # Reuse risk handler
            "maintenance_forecast": MaintenanceAnalysisHandler,
            "portfolio_maintenance_forecast": MaintenanceAnalysisHandler,  # Reuse maintenance handler
            "quality_degradation": QualityAnalysisHandler,  # Reuse quality handler
            "portfolio_quality_degradation": QualityAnalysisHandler,  # Reuse quality handler
            "change_impact": ChangeImpactAnalysisHandler,
            "portfolio_change_impact": ChangeImpactAnalysisHandler,  # Reuse impact handler
            "automated_remediation": RemediationHandler,
            "remediation_preview": RemediationHandler,  # Reuse remediation handler
            "workflow_event": WorkflowAnalysisHandler,
            "workflow_status": WorkflowAnalysisHandler,  # Reuse workflow handler
            "cross_repository_analysis": CrossRepositoryAnalysisHandler,
            "repository_connectivity": CrossRepositoryAnalysisHandler,  # Reuse cross-repo handler
            "repository_connector_config": CrossRepositoryAnalysisHandler,  # Reuse cross-repo handler
            "submit_distributed_task": DistributedAnalysisHandler,
            "submit_batch_tasks": DistributedAnalysisHandler,  # Reuse distributed handler
            "get_task_status": DistributedAnalysisHandler,  # Reuse distributed handler
            "cancel_task": DistributedAnalysisHandler,  # Reuse distributed handler
            "get_workers_status": DistributedAnalysisHandler,  # Reuse distributed handler
            "get_processing_stats": DistributedAnalysisHandler,  # Reuse distributed handler
            "scale_workers": DistributedAnalysisHandler,  # Reuse distributed handler
            "start_processing": DistributedAnalysisHandler,  # Reuse distributed handler
            "set_load_balancing_strategy": DistributedAnalysisHandler,  # Reuse distributed handler
            "get_queue_status": DistributedAnalysisHandler,  # Reuse distributed handler
            "configure_load_balancing": DistributedAnalysisHandler,  # Reuse distributed handler
            "get_load_balancing_config": DistributedAnalysisHandler,  # Reuse distributed handler
        }

    def create_handler(self, handler_type: str, **kwargs) -> BaseAnalysisHandler:
        """Create a handler instance with dependency injection."""
        if handler_type not in self._handler_classes:
            raise ValueError(f"Unknown handler type: {handler_type}")

        handler_class = self._handler_classes[handler_type]

        # Create handler with injected services
        try:
            handler = handler_class(
                handler_name=handler_type,
                logger=self._logger,
                cache=self._cache,
                event_publisher=self._event_publisher,
                service_client=self._service_client,
                metrics=self._metrics,
                **kwargs
            )
            return handler
        except Exception as e:
            # Fallback to creating with default services if injection fails
            try:
                handler = handler_class(handler_name=handler_type, **kwargs)
                return handler
            except Exception as fallback_error:
                raise RuntimeError(f"Failed to create handler {handler_type}: {e}, fallback also failed: {fallback_error}")

    def get_available_handlers(self) -> List[str]:
        """Get list of available handler types."""
        return list(self._handler_classes.keys())

    def register_handler(self, handler_type: str, handler_class: Type[BaseAnalysisHandler]) -> None:
        """Register a custom handler type."""
        self._handler_classes[handler_type] = handler_class

    def unregister_handler(self, handler_type: str) -> None:
        """Unregister a handler type."""
        if handler_type in self._handler_classes:
            del self._handler_classes[handler_type]

    async def create_all_handlers(self) -> Dict[str, BaseAnalysisHandler]:
        """Create instances of all available handlers."""
        handlers = {}
        for handler_type in self._handler_classes.keys():
            try:
                handler = self.create_handler(handler_type)
                handlers[handler_type] = handler
            except Exception as e:
                await self._logger.warning(f"Failed to create handler {handler_type}: {e}",
                                         handler_type=handler_type)
        return handlers


# Global factory instance
_handler_factory: Optional[HandlerFactory] = None


def get_handler_factory() -> HandlerFactory:
    """Get the global handler factory."""
    global _handler_factory
    if _handler_factory is None:
        _handler_factory = HandlerFactory()
    return _handler_factory


def create_handler(handler_type: str, **kwargs) -> BaseAnalysisHandler:
    """Create a handler instance using the global factory."""
    return get_handler_factory().create_handler(handler_type, **kwargs)


async def initialize_handlers() -> Dict[str, BaseAnalysisHandler]:
    """Initialize all handlers - call this at application startup."""
    factory = get_handler_factory()
    handlers = await factory.create_all_handlers()

    # Log initialization
    try:
        logger = factory._logger
        await logger.info("Handlers initialized successfully", {
            "handler_count": len(handlers),
            "handler_types": list(handlers.keys())
        })
    except Exception:
        pass  # Ignore logging errors during initialization

    return handlers
