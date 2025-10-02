"""Service Registry - Central service registration and configuration."""

import os
from typing import Any, Optional, Type

from .container import DependencyContainer, ServiceLifetime, get_global_container


# Minimal service implementations for dependency injection
class MinimalCacheService:
    async def get(self, key: str):
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        pass

    async def delete(self, key: str):
        pass

    async def exists(self, key: str):
        return False


class MinimalAnalysisService:
    async def analyze_documents(self, targets, analysis_type, **kwargs):
        return {"status": "success", "message": "Minimal analysis service"}
from .services import (
    IAnalysisRepository,
    IAnalysisService,
    ICacheService,
    IConfigurationService,
    IDocumentRepository,
    IDocumentService,
    IEventPublisher,
    IFindingRepository,
    ILoggerService,
    IMetricsService,
    IQualityAnalyzer,
    IRepositoryService,
    ISemanticAnalyzer,
    ISentimentAnalyzer,
    IServiceClient,
)


class ServiceRegistry:
    """Central service registry for dependency injection configuration."""

    def __init__(self, container: Optional[DependencyContainer] = None) -> None:
        self._container = container or get_global_container()
        self._services_registered = False

    def register_all_services(self) -> DependencyContainer:
        """Register all services with the container."""
        if self._services_registered:
            return self._container

        # Register core infrastructure services
        self._register_infrastructure_services()

        # Register domain services
        self._register_domain_services()

        # Register repository services
        self._register_repository_services()

        # Register external services
        self._register_external_services()

        # Register cross-cutting concerns
        self._register_cross_cutting_services()

        self._services_registered = True
        return self._container

    def _register_infrastructure_services(self) -> None:
        """Register infrastructure services."""

        # Configuration Service
        from services.shared.infrastructure.config.pydantic_config import ServiceConfig
        from services.shared.infrastructure.config import load_service_config

        class ConfigService:
            def __init__(self):
                self._config = None

            def _get_config(self):
                if self._config is None:
                    # Try to get service name from environment or use default
                    service_name = os.environ.get('SERVICE_NAME', 'unknown')
                    try:
                        self._config = load_service_config(service_name)
                    except:
                        # Fallback to a basic config
                        self._config = ServiceConfig()
                return self._config

            def get(self, key: str, default=None):
                try:
                    return getattr(self._get_config(), key, default)
                except:
                    return default

            def get_section(self, section: str):
                try:
                    config = self._get_config()
                    if hasattr(config, section):
                        section_obj = getattr(config, section)
                        if hasattr(section_obj, '__dict__'):
                            return section_obj.__dict__
                        return section_obj
                    return {}
                except:
                    return {}

            def set(self, key: str, value):
                # For now, just ignore - config is read-only
                pass

        self._container.register_singleton(IConfigurationService, ConfigService)

        # Logger Service
        from services.shared.infrastructure.logging.standardized_logger import StandardizedLogger

        # Create a simple wrapper to match the interface
        class LoggerService:
            def __init__(self):
                self._logger = StandardizedLogger("infrastructure")

            def info(self, message: str, **kwargs):
                self._logger.info(message, **kwargs)

            def error(self, message: str, **kwargs):
                self._logger.error(message, **kwargs)

            def warning(self, message: str, **kwargs):
                self._logger.warning(message, **kwargs)

            def debug(self, message: str, **kwargs):
                self._logger.debug(message, **kwargs)

        self._container.register_singleton(ILoggerService, LoggerService)

        # Metrics Service
        from services.shared.infrastructure.monitoring.metrics import ServiceMetrics

        # Create a wrapper to match the interface
        class MetricsService:
            def __init__(self):
                self._metrics = ServiceMetrics("infrastructure")

            def increment_counter(self, name: str, value: float = 1.0, **labels):
                # Simple wrapper - implement as needed
                pass

            def set_gauge(self, name: str, value: float, **labels):
                # Simple wrapper - implement as needed
                pass

            def observe_histogram(self, name: str, value: float, **labels):
                # Simple wrapper - implement as needed
                pass

        self._container.register_singleton(IMetricsService, MetricsService)

        # Cache Service - Minimal implementation
        self._container.register_singleton(ICacheService, MinimalCacheService)

        # Event Publisher - Temporarily disabled
        # from ..streaming.event_publisher import EventPublisher
        # self._container.register_singleton(IEventPublisher, EventPublisher)

        # Service Client - Temporarily disabled
        # from ..utilities.service_client import ServiceClient
        # self._container.register_singleton(IServiceClient, ServiceClient)

    def _register_domain_services(self) -> None:
        """Register domain services."""

        # Analysis Service - Minimal implementation
        self._container.register_singleton(IAnalysisService, MinimalAnalysisService)

        # Document Service - Temporarily disabled
        # from ...domain.services.document_service import DocumentService
        # self._container.register_singleton(IDocumentService, DocumentService)

        # Repository Service - Temporarily disabled
        # from ...domain.services.repository_service import RepositoryService
        # self._container.register_singleton(IRepositoryService, RepositoryService)

    def _register_repository_services(self) -> None:
        """Register repository services."""

        # Analysis Repository - Temporarily disabled
        # from ...infrastructure.repositories.analysis_repository import (
        #     AnalysisRepository,
        # )
        # self._container.register_scoped(IAnalysisRepository, AnalysisRepository)

        # Document Repository - Temporarily disabled
        # from ...infrastructure.repositories.document_repository import (
        #     DocumentRepository,
        # )
        # self._container.register_scoped(IDocumentRepository, DocumentRepository)

        # Finding Repository - Temporarily disabled
        # from ...infrastructure.repositories.finding_repository import FindingRepository
        # self._container.register_scoped(IFindingRepository, FindingRepository)

    def _register_external_services(self) -> None:
        """Register external service adapters."""

        # Semantic Analyzer - Temporarily disabled
        # from ...infrastructure.external.semantic_analyzer_adapter import (
        #     SemanticAnalyzerAdapter,
        # )
        # self._container.register_singleton(ISemanticAnalyzer, SemanticAnalyzerAdapter)

        # Sentiment Analyzer - Temporarily disabled
        # from ...infrastructure.external.sentiment_analyzer_adapter import (
        #     SentimentAnalyzerAdapter,
        # )
        # self._container.register_singleton(ISentimentAnalyzer, SentimentAnalyzerAdapter)

        # Quality Analyzer - Temporarily disabled
        # from ...infrastructure.external.quality_analyzer_adapter import (
        #     QualityAnalyzerAdapter,
        # )
        # self._container.register_singleton(IQualityAnalyzer, QualityAnalyzerAdapter)

    def _register_cross_cutting_services(self) -> None:
        """Register cross-cutting concern services."""

        # Register factories - Temporarily disabled
        # from ...application.factories.handler_factory import HandlerFactory
        # self._container.register_singleton(Type[HandlerFactory], HandlerFactory)

        # Register validators - Temporarily disabled
        # from ...application.validators.business_rule_validator import (
        #     BusinessRuleValidator,
        # )
        # self._container.register_singleton(
        #     Type[BusinessRuleValidator], BusinessRuleValidator
        # )

    def register_custom_service(
        self,
        interface: Type,
        implementation: Type,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    ) -> None:
        """Register a custom service."""
        if lifetime == ServiceLifetime.SINGLETON:
            self._container.register_singleton(interface, implementation)
        elif lifetime == ServiceLifetime.SCOPED:
            self._container.register_scoped(interface, implementation)
        else:
            self._container.register_transient(interface, implementation)

    def register_service_instance(self, interface: Type, instance: Any) -> None:
        """Register a service instance."""
        self._container.register_instance(interface, instance)

    def register_factory(
        self,
        interface: Type,
        factory_func,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ) -> None:
        """Register a service factory."""
        self._container.register_factory(interface, factory_func, lifetime)

    def get_service(self, interface: Type) -> Any:
        """Get service instance."""
        return self._container.resolve(interface)

    def create_scope(self):
        """Create a new service scope."""
        return self._container.create_scope()


# Global registry instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry."""
    global _service_registry
    if _service_registry is None:
        container = get_global_container()
        _service_registry = ServiceRegistry(container)
        _service_registry.register_all_services()
    return _service_registry


def initialize_services() -> None:
    """Initialize all services - call this at application startup."""
    registry = get_service_registry()

    # Initialize any services that need startup
    try:
        registry.get_service(IConfigurationService)
        logger_service = registry.get_service(ILoggerService)
        registry.get_service(IMetricsService)

        # Log initialization
        logger_service.info(
            "Services initialized successfully",
            {
                "service_count": len(registry._container._services),
                "environment": os.getenv("ENVIRONMENT", "development"),
            },
        )

    except Exception as e:
        print(f"Failed to initialize services: {e}")
        raise


def get_service(interface: Type) -> Any:
    """Get service instance from global registry."""
    return get_service_registry().get_service(interface)


def create_service_scope():
    """Create a new service scope from global registry."""
    return get_service_registry().create_scope()


# Convenience functions for common services
def get_analysis_service() -> IAnalysisService:
    """Get analysis service."""
    return get_service(IAnalysisService)


def get_document_service() -> IDocumentService:
    """Get document service."""
    return get_service(IDocumentService)


def get_cache_service() -> ICacheService:
    """Get cache service."""
    return get_service(ICacheService)


def get_logger_service() -> ILoggerService:
    """Get logger service."""
    return get_service(ILoggerService)


def get_metrics_service() -> IMetricsService:
    """Get metrics service."""
    return get_service(IMetricsService)


def get_config_service() -> IConfigurationService:
    """Get configuration service."""
    return get_service(IConfigurationService)
